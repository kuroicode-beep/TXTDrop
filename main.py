import os
import re
import time
import ctypes
import ctypes.wintypes
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import keyboard
import pyperclip
from PIL import Image, ImageGrab, ImageDraw
import pystray

import tk_root as tkr
import config
import hotkeys
import ollama_client
import tts_client
import memory_client
import dedup
import dedup_window
import sound
import notify
import log_window
import registry_client
import settings_window
from i18n import t
from version import VERSION_LABEL


# ── Filename helpers ──────────────────────────────────────────────────────────

def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _clip_title(text: str) -> str:
    """Extract a file-safe title from the first non-empty line of clipboard text."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            line = re.sub(r'[\\/:*?"<>|]', '', line)   # Windows-illegal chars
            line = re.sub(r'\s+', '-', line).strip('-')
            return line[:40]
    return ""


def _text_filename(text: str, ollama_running: bool) -> str:
    """Build filename.  AI title when Ollama is up, else first line of clipboard."""
    prefix = config.get("filename_prefix") or "txtdrop"
    ts     = _timestamp()
    if ollama_running:
        model = config.get("ollama_model") or "llama3"
        title = ollama_client.generate_title(text, model)
        if title:
            return f"{prefix}_{title}_{ts}.txt"
    # Fallback: first line of clipboard text
    clip = _clip_title(text)
    if clip:
        return f"{prefix}_{clip}_{ts}.txt"
    return f"{prefix}_{ts}.txt"


def _image_filename() -> str:
    prefix = config.get("filename_prefix") or "txtdrop"
    return f"{prefix}_{_timestamp()}.png"


# ── Folder helpers ────────────────────────────────────────────────────────────

def _text_folder() -> str | None:
    f = config.get("text_save_folder")
    return f if f and os.path.isdir(f) else None


def _image_folder() -> str | None:
    f = config.get("image_save_folder")
    if f and os.path.isdir(f):
        return f
    return _text_folder()


# ── Clipboard save ────────────────────────────────────────────────────────────

def drop_clipboard():
    # ── Image ────────────────────────────────────────────────────────────────
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            folder = _image_folder()
            if not folder:
                msg = t("save_fail_folder")
                config.log_add("WARN", "save", f"[image] {msg}")
                notify.show_toast(t("toast_fail"), msg,
                                  on_click=log_window.open_log, level="error")
                return
            filename = _image_filename()
            filepath = os.path.join(folder, filename)
            img.save(filepath, "PNG")
            config.history_add("image", filename, filepath)
            config.log_add("INFO", "save", f"[image] {filename}")
            if config.get_bool("sound_enabled"):
                config.log_add("INFO", "sound", "play")
                sound.play_drop()
            notify.show_toast(t("toast_ok"), filename,
                              on_click=log_window.open_log)
            return
    except Exception as e:
        msg = f"[image] {e}"
        config.log_add("ERROR", "save", msg)
        notify.show_toast(t("toast_fail"), str(e),
                          on_click=log_window.open_log, level="error")
        return

    # ── Text ─────────────────────────────────────────────────────────────────
    try:
        text = pyperclip.paste()
        if not text or not text.strip():
            config.log_add("WARN", "save", t("save_fail_empty"))
            return

        folder = _text_folder()
        if not folder:
            msg = t("save_fail_folder")
            config.log_add("WARN", "save", f"[text] {msg}")
            notify.show_toast(t("toast_fail"), msg,
                              on_click=log_window.open_log, level="error")
            return

        # Show AI-progress toast if Ollama is available (non-blocking)
        ollama_ok = ollama_client.is_running_cached()
        if ollama_ok:
            notify.show_toast(t("toast_ai_generating"), t("toast_ai_body"),
                              level="info")

        filename = _text_filename(text, ollama_ok)
        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        hist_id = config.history_add("text", filename, filepath)
        config.log_add("INFO", "save", f"[text] {filename}")
        if config.get_bool("sound_enabled"):
            config.log_add("INFO", "sound", "play")
            sound.play_drop()
        notify.show_toast(t("toast_ok"), filename,
                          on_click=log_window.open_log)

        # 저장 직후 백그라운드 중복 검사 — 중복이면 기록을 휴지통으로 이동
        dedup.check_new_async(
            hist_id, filename, text,
            on_dup=lambda reason: notify.show_toast(
                t("toast_dedup"), reason,
                on_click=dedup_window.open_dedup, level="info"),
        )

    except Exception as e:
        msg = f"[text] {e}"
        config.log_add("ERROR", "save", msg)
        notify.show_toast(t("toast_fail"), str(e),
                          on_click=log_window.open_log, level="error")


# ── Clipboard TTS (ctrl+shift+x) ──────────────────────────────────────────────

def _grab_selection(old: str, trigger_key: str) -> str:
    """
    현재 선택된 텍스트를 Ctrl+C로 복사해 가져온다.
    선택이 없으면 기존 클립보드(old)를 반환하고, 클립보드는 원래대로 되돌린다.
    trigger_key: 단축키의 마지막 키(예: 낭독="x", AI 기억="m") — 손을 뗄 때까지 대기하는 데 사용.
    """
    # 단축키 보조키에서 손을 뗄 때까지 대기 (최대 1초) — 안 떼면 Ctrl+Shift+<key>가 눌림
    # (GetAsyncKeyState 기반 — keyboard 훅이 죽어도 동작)
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline and (
        hotkeys.is_down("ctrl") or hotkeys.is_down("shift")
        or hotkeys.is_down(trigger_key)
    ):
        time.sleep(0.03)

    keyboard.send("ctrl+c")
    time.sleep(0.2)                      # 대상 앱의 클립보드 반영 대기
    text = pyperclip.paste()
    if text and text.strip():
        if text != old:
            pyperclip.copy(old)          # 캡처가 클립보드를 바꾸지 않도록 원복
        return text
    return old                           # 선택 없음 → 기존 클립보드 사용


def _active_window_title() -> str | None:
    # 캡처 시점의 활성 창 제목 (origin_app 힌트, best-effort)
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return None
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or None
    except Exception:
        return None


def speak_clipboard():
    # 선택한 텍스트(없으면 클립보드)를 SVIL TTS(:8765)로 즉시 낭독
    try:
        text = _grab_selection(pyperclip.paste(), "x")
        if not text or not text.strip():
            config.log_add("WARN", "tts", t("save_fail_empty"))
            notify.show_toast(t("toast_tts_fail"), t("tts_nothing"),
                              level="error")
            return

        notify.show_toast(t("toast_tts_generating"), t("toast_tts_body"),
                          level="info")
        ok, err = tts_client.speak(
            text,
            on_starting=lambda: notify.show_toast(
                t("toast_tts_starting"), t("toast_tts_starting_body"),
                level="info"),
        )
        if not ok:
            notify.show_toast(t("toast_tts_fail"), err,
                              on_click=log_window.open_log, level="error")
    except Exception as e:
        config.log_add("ERROR", "tts", f"예외: {type(e).__name__}: {e}")
        notify.show_toast(t("toast_tts_fail"), str(e),
                          on_click=log_window.open_log, level="error")


# ── AI 기억 캡처 (ctrl+shift+m, TXTAIMemory 연계, 기본 비활성) ─────────────────

def capture_memory():
    # 선택한 텍스트(없으면 클립보드)를 TXTAIMemory 원장(source=drop)에 캡처
    try:
        origin = _active_window_title()
        text = _grab_selection(pyperclip.paste(), "m")
        if not text or not text.strip():
            config.log_add("WARN", "memory", t("save_fail_empty"))
            notify.show_toast(t("toast_memory_fail"), t("tts_nothing"),
                              level="error")
            return

        ok, msg, fell_back = memory_client.capture(text, origin_app=origin)
        if fell_back:
            notify.show_toast(t("toast_memory_fallback"), msg, level="info")
        elif ok:
            notify.show_toast(t("toast_memory_ok"), t("toast_memory_ok_body"))
        else:
            notify.show_toast(t("toast_memory_fail"), msg,
                              on_click=log_window.open_log, level="error")
    except Exception as e:
        config.log_add("ERROR", "memory", f"예외: {type(e).__name__}: {e}")
        notify.show_toast(t("toast_memory_fail"), str(e),
                          on_click=log_window.open_log, level="error")


# ── Ollama startup check (always silent) ─────────────────────────────────────

def _ollama_check():
    """
    On startup: 상태 확인·로그만 남긴다.
    자동 시작(페일오버) 없음 — 서버가 죽어 있으면 그대로 두고, AI 제목 없이
    클립보드 첫 줄 파일명으로 동작한다. 기동은 트레이 'Ollama 새로고침'으로만.
    """
    config.log_add("INFO", "ollama", "서버 상태 확인 중...")
    if ollama_client.is_running_cached():
        models = ollama_client.list_models()
        config.log_add("INFO", "ollama",
                       f"서버 실행 중 - 모델 {len(models)}개: {', '.join(models[:3])}")
    else:
        config.log_add("INFO", "ollama",
                       "서버 미실행 - AI 제목 생략, 클립보드 첫 줄 파일명 사용")


# ── Ollama manual refresh (from tray menu) ────────────────────────────────────

def _do_ollama_refresh():
    """Check Ollama status from tray; start if needed; notify user."""
    def _check():
        running = ollama_client.is_running()
        with ollama_client._cache_lock:
            ollama_client._cached_running = running
            ollama_client._cache_time     = time.monotonic()

        if running:
            models = ollama_client.list_models()
            config.log_add("INFO", "ollama", f"수동 확인 - 실행 중, 모델 {len(models)}개")
            notify.show_toast("Ollama", t("ollama_running_models", n=len(models)), level="info")
            return

        # Not running — try to start
        config.log_add("INFO", "ollama", "수동 시작 시도")
        notify.show_toast("Ollama", t("ollama_starting"), level="info")
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except FileNotFoundError:
            config.log_add("WARN", "ollama", "ollama 미설치")
            notify.show_toast("Ollama", t("ollama_install_notice"), level="error")
            return

        time.sleep(5)
        ollama_client._refresh_cache()
        if ollama_client._cached_running:
            models = ollama_client.list_models()
            config.log_add("INFO", "ollama", f"수동 시작 완료 - 모델 {len(models)}개")
            notify.show_toast("Ollama", t("ollama_started"), level="info")
        else:
            config.log_add("WARN", "ollama", "수동 시작 후 서버 응답 없음")
            notify.show_toast("Ollama", t("ollama_no_response"), level="error")

    threading.Thread(target=_check, daemon=True).start()


# ── Hotkey registration (RegisterHotKey 우선, keyboard 라이브러리 폴백) ───────

_kb_fallback: set[str] = set()   # keyboard 라이브러리로 폴백 등록된 단축키


def _current_bindings() -> tuple[dict, dict]:
    """설정에서 현재 단축키 바인딩 {단축키: 콜백}과 {단축키: 라벨}을 만든다."""
    bindings, labels = {}, {}

    def add(hk, fn, label):
        hk = (hk or "").strip().lower()
        if not hk:
            return
        if hk in bindings:
            config.log_add("WARN", "startup",
                           f"{label} 단축키가 '{labels[hk]}'과(와) 중복 - 건너뜀: {hk}")
            return
        bindings[hk] = fn
        labels[hk]   = label

    add(config.get("hotkey")     or "ctrl+shift+z", drop_clipboard,  "저장")
    add(config.get("tts_hotkey") or "ctrl+shift+x", speak_clipboard, "낭독")
    # AI 기억 캡처(TXTAIMemory 연계)는 기본 비활성 — 켜져 있을 때만 등록
    if config.get_bool("memory_enabled"):
        add(config.get("memory_hotkey") or "ctrl+shift+m", capture_memory, "AI 기억")
    return bindings, labels


def _apply_hotkeys():
    """
    단축키 전체를 RegisterHotKey로 재등록한다.  keyboard 훅과 달리 절전
    복귀·시스템 부하에도 OS가 등록을 유지한다.  조합이 이미 선점된 경우에만
    keyboard 라이브러리로 폴백한다.
    """
    bindings, labels = _current_bindings()

    for hk in list(_kb_fallback):
        try:
            keyboard.remove_hotkey(hk)
        except Exception:
            pass
        _kb_fallback.discard(hk)

    results = hotkeys.apply(bindings)
    for hk, err in results.items():
        label = labels[hk]
        if err is None:
            config.log_add("INFO", "startup", f"{label} 단축키 등록: {hk}")
            continue
        config.log_add("WARN", "startup",
                       f"{label} 단축키 RegisterHotKey 실패({err}) - keyboard 폴백 시도")
        try:
            fn = bindings[hk]
            keyboard.add_hotkey(
                hk, lambda fn=fn: threading.Thread(target=fn, daemon=True).start()
            )
            _kb_fallback.add(hk)
            config.log_add("INFO", "startup", f"{label} 단축키 폴백 등록: {hk}")
        except Exception as e:
            config.log_add("ERROR", "startup", f"{label} 단축키 등록 실패: {e}")


# ── First run ─────────────────────────────────────────────────────────────────

def _first_run() -> bool:
    """
    Called from the main thread BEFORE mainloop() starts.
    messagebox / filedialog run their own internal event loops, so
    direct Tk calls are safe here — no call_on_main / event.wait() needed.
    """
    root = tkr.get()
    root.attributes("-topmost", True)
    messagebox.showinfo(t("first_run_title"), t("first_run_msg"), parent=root)
    folder = filedialog.askdirectory(title=t("select_folder"), parent=root)
    root.attributes("-topmost", False)
    if not folder:
        return False
    config.set("text_save_folder",  folder)
    config.set("image_save_folder", folder)
    config.log_add("INFO", "startup", f"첫 실행 - 저장 폴더 설정: {folder}")
    return True


# ── Dark tray menu ────────────────────────────────────────────────────────────

def _dark_tray_menu(settings_cb, log_cb, dedup_cb, ollama_cb, exit_cb):
    """Show a custom dark Tk popup menu at the current cursor position."""
    class _POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    cx, cy = pt.x, pt.y

    def _popup():
        root = tkr.get()
        menu = tk.Menu(
            root, tearoff=0,
            bg="#1c1c1c", fg="#f0f0f0",
            activebackground="#2d2d2d", activeforeground="#ffd600",
            font=("Malgun Gothic", 10),
            bd=0, relief="flat",
            activeborderwidth=0,
        )
        menu.add_command(label=t("settings"),           command=settings_cb)
        menu.add_command(label=t("log_history"),        command=log_cb)
        menu.add_command(label=t("tray_dedup"),         command=dedup_cb)
        menu.add_command(label=t("tray_ollama_refresh"), command=ollama_cb)
        menu.add_separator()
        menu.add_command(label=t("exit"),               command=exit_cb)
        try:
            menu.tk_popup(cx, cy)
        finally:
            menu.grab_release()

    tkr.call_on_main(_popup)


def _patch_tray_dark_menu(tray, settings_cb, log_cb, dedup_cb, ollama_cb, exit_cb):
    """
    Monkey-patch pystray's WM_RBUTTONUP handler to show a custom dark menu
    instead of the native Windows popup.
    """
    try:
        import types
        import pystray._win32 as _pw

        WM_LBUTTONUP = 0x0202
        WM_RBUTTONUP = 0x0205

        def _custom_on_notify(self, wparam, lparam):
            if lparam == WM_LBUTTONUP:
                self()
            elif lparam == WM_RBUTTONUP:
                _dark_tray_menu(settings_cb, log_cb, dedup_cb, ollama_cb, exit_cb)

        tray._on_notify = types.MethodType(_custom_on_notify, tray)
        # pystray는 __init__에서 _message_handlers 딕셔너리에 원본 바운드
        # 메서드를 저장해두고 디스패처가 그 딕셔너리만 참조하므로,
        # 딕셔너리 항목까지 교체해야 패치가 실제로 적용된다
        tray._message_handlers[_pw.win32.WM_NOTIFY] = tray._on_notify
        config.log_add("INFO", "startup", "다크 트레이 메뉴 패치 완료")
    except Exception as e:
        config.log_add("WARN", "startup",
                       f"다크 트레이 메뉴 패치 실패 - 네이티브 메뉴 사용: {e}")


# ── Tray icon ─────────────────────────────────────────────────────────────────

def _make_icon() -> Image.Image:
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d    = ImageDraw.Draw(img)
    try:
        d.rounded_rectangle([4, 4, 60, 60], radius=10, fill=(41, 128, 185))
    except AttributeError:
        d.rectangle([4, 4, 60, 60], fill=(41, 128, 185))
    d.rectangle([16, 16, 48, 23], fill="white")
    d.rectangle([28, 16, 36, 50], fill="white")
    return img


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    config.init_db()

    # Create the shared Tk root on the main thread (mainloop runs here later)
    tkr.init()

    config.log_add("INFO", "startup", f"TXTDrop {VERSION_LABEL} 시작됨")

    # SVIL 디스커버리 레지스트리에 자기 항목 기록 — 실패해도 기동을 막지 않는다(내부에서 stderr 로그만)
    registry_client.register_app()

    # First-run folder setup (uses tkr event loop)
    if not config.get("text_save_folder"):
        if not _first_run():
            config.log_add("WARN", "startup", "첫 실행 폴더 선택 취소 - 종료")
            return

    # Ollama check in background (always silent)
    threading.Thread(target=_ollama_check, daemon=True).start()

    # Register hotkeys (저장 + 낭독 + AI 기억) — RegisterHotKey 기반
    _apply_hotkeys()

    # ── Tray callbacks ────────────────────────────────────────────────────────

    tray_ref = [None]

    def _do_settings():
        # 설정 저장 후 단축키 전체 재등록 (변경·토글 모두 반영)
        settings_window.open_settings(on_save=_apply_hotkeys)

    def _do_log():
        log_window.open_log()

    def _do_dedup():
        dedup_window.open_dedup()

    def _do_exit():
        config.log_add("INFO", "startup", "TXTDrop 종료됨")
        hotkeys.stop()
        keyboard.unhook_all()
        time.sleep(0.15)
        if tray_ref[0]:
            tray_ref[0].stop()
        os._exit(0)

    # pystray native-menu callbacks (fallback)
    def on_settings(icon, item):    _do_settings()
    def on_log(icon, item):         _do_log()
    def on_dedup(icon, item):       _do_dedup()
    def on_ollama(icon, item):      _do_ollama_refresh()
    def on_exit(icon, item):        _do_exit()

    tray = pystray.Icon(
        name="TXTDrop",
        icon=_make_icon(),
        title=f"TXTDrop {VERSION_LABEL}",
        menu=pystray.Menu(
            pystray.MenuItem(lambda item: t("settings"),           on_settings),
            pystray.MenuItem(lambda item: t("log_history"),        on_log),
            pystray.MenuItem(lambda item: t("tray_dedup"),         on_dedup),
            pystray.MenuItem(lambda item: t("tray_ollama_refresh"), on_ollama),
            pystray.MenuItem(lambda item: t("exit"),               on_exit),
        ),
    )
    tray_ref[0] = tray

    _patch_tray_dark_menu(tray, _do_settings, _do_log, _do_dedup,
                          _do_ollama_refresh, _do_exit)

    tray.run_detached()
    tkr.get().mainloop()


if __name__ == "__main__":
    main()
