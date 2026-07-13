"""
hotkeys.py — Win32 RegisterHotKey 기반 전역 단축키 관리자.

keyboard 라이브러리의 저수준 키보드 훅(WH_KEYBOARD_LL)은 절전 복귀나
시스템 부하 시 Windows가 조용히 제거해버려 단축키가 죽는 문제가 있다.
RegisterHotKey는 OS가 등록을 직접 관리하므로 절전/복귀에도 유지된다.

주의: 이 모듈은 커스텀 WNDPROC 콜백을 쓰지 않는다 — 창 없이 스레드
메시지 큐(GetMessageW)로만 WM_HOTKEY를 수신한다.  (WNDPROC 방식은
PyInstaller 고정 런타임에서 STATUS_STACK_BUFFER_OVERRUN 크래시 이력 있음)
"""
import ctypes
import ctypes.wintypes
import threading

_user32   = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WM_HOTKEY   = 0x0312
WM_QUIT     = 0x0012
PM_NOREMOVE = 0x0000

MOD_ALT      = 0x0001
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004
MOD_WIN      = 0x0008
MOD_NOREPEAT = 0x4000

_MOD_NAMES = {
    "ctrl": MOD_CONTROL, "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "alt": MOD_ALT,
    "win": MOD_WIN, "windows": MOD_WIN, "super": MOD_WIN,
}

# Tk keysym / keyboard 라이브러리 표기 → Windows 가상 키 코드
_VK_NAMES = {
    "space": 0x20, "tab": 0x09, "return": 0x0D, "enter": 0x0D,
    "escape": 0x1B, "esc": 0x1B, "backspace": 0x08,
    "delete": 0x2E, "del": 0x2E, "insert": 0x2D, "ins": 0x2D,
    "home": 0x24, "end": 0x23,
    "pageup": 0x21, "prior": 0x21, "pagedown": 0x22, "next": 0x22,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "pause": 0x13, "printscreen": 0x2C, "scrolllock": 0x91,
    "plus": 0xBB, "equal": 0xBB, "minus": 0xBD,
    "comma": 0xBC, "period": 0xBE, "slash": 0xBF,
    "grave": 0xC0, "semicolon": 0xBA, "apostrophe": 0xDE,
    "backslash": 0xDC, "bracketleft": 0xDB, "bracketright": 0xDD,
}
for _i in range(1, 25):
    _VK_NAMES[f"f{_i}"] = 0x70 + _i - 1


def parse(hotkey: str) -> tuple[int, int]:
    """'ctrl+shift+z' → (수정자 비트, 가상 키 코드).  실패 시 ValueError."""
    mods, vk = 0, None
    for part in hotkey.lower().replace(" ", "").split("+"):
        if not part:
            continue
        if part in _MOD_NAMES:
            mods |= _MOD_NAMES[part]
        elif vk is not None:
            raise ValueError(f"키가 두 개 이상입니다: {hotkey}")
        elif part in _VK_NAMES:
            vk = _VK_NAMES[part]
        elif len(part) == 1 and part.isascii() and part.isalnum():
            vk = ord(part.upper())
        else:
            raise ValueError(f"알 수 없는 키: {part}")
    if vk is None:
        raise ValueError(f"일반 키가 없습니다: {hotkey}")
    return mods, vk


def is_down(key: str) -> bool:
    """현재 키가 눌려 있는지 (GetAsyncKeyState — 훅 불필요)."""
    special = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B}
    vk = special.get(key) or _VK_NAMES.get(key)
    if vk is None and len(key) == 1:
        vk = ord(key.upper())
    if vk is None:
        return False
    return bool(_user32.GetAsyncKeyState(vk) & 0x8000)


# ── 리스너 스레드 관리 ─────────────────────────────────────────────────────────

_lock       = threading.Lock()
_thread     = None
_thread_id  = None


def apply(bindings: dict[str, "callable"]) -> dict[str, str | None]:
    """
    단축키 전체를 재등록한다.  {단축키: 콜백} → {단축키: 오류 메시지 | None(성공)}.
    기존 리스너 스레드는 중지 후 새로 시작한다 (RegisterHotKey는 등록 스레드에서만 해제 가능).
    """
    global _thread, _thread_id
    with _lock:
        _stop_locked()

        results: dict[str, str | None] = {}
        parsed = []
        for i, (hk, fn) in enumerate(bindings.items(), start=1):
            try:
                mods, vk = parse(hk)
                parsed.append((i, hk, mods, vk, fn))
            except ValueError as e:
                results[hk] = str(e)

        if not parsed:
            return results

        ready = threading.Event()
        state: dict = {}
        t = threading.Thread(
            target=_worker, args=(parsed, results, state, ready),
            daemon=True, name="hotkey-listener",
        )
        t.start()
        if not ready.wait(5):
            for _, hk, *_rest in parsed:
                results.setdefault(hk, "리스너 스레드 시작 시간 초과")
            return results

        _thread    = t
        _thread_id = state.get("tid")
        return results


def stop():
    """리스너 중지 및 모든 단축키 해제 (종료 시 호출)."""
    with _lock:
        _stop_locked()


def _stop_locked():
    global _thread, _thread_id
    if _thread and _thread.is_alive() and _thread_id:
        _user32.PostThreadMessageW(_thread_id, WM_QUIT, 0, 0)
        _thread.join(2)
    _thread    = None
    _thread_id = None


def _worker(parsed, results, state, ready):
    msg = ctypes.wintypes.MSG()
    # 메시지 큐를 먼저 생성해 PostThreadMessage(WM_QUIT)가 유실되지 않게 한다
    _user32.PeekMessageW(ctypes.byref(msg), None, 0x0400, 0x0400, PM_NOREMOVE)
    state["tid"] = _kernel32.GetCurrentThreadId()

    callbacks: dict[int, "callable"] = {}
    for hk_id, hk, mods, vk, fn in parsed:
        if _user32.RegisterHotKey(None, hk_id, mods | MOD_NOREPEAT, vk):
            callbacks[hk_id] = fn
            results[hk] = None
        else:
            code = ctypes.get_last_error()
            if code == 1409:            # ERROR_HOTKEY_ALREADY_REGISTERED
                results[hk] = "다른 프로그램이 이미 사용 중"
            else:
                results[hk] = f"RegisterHotKey 오류 코드 {code}"
    ready.set()

    try:
        while True:
            r = _user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r == 0 or r == -1:       # WM_QUIT 또는 오류
                break
            if msg.message == WM_HOTKEY:
                fn = callbacks.get(msg.wParam)
                if fn:
                    threading.Thread(target=fn, daemon=True).start()
    finally:
        for hk_id in callbacks:
            _user32.UnregisterHotKey(None, hk_id)
