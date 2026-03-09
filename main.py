import os
import time
import ctypes
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
import ollama_client
import sound
import notify
import log_window
import settings_window
from i18n import t


# ── Filename helpers ──────────────────────────────────────────────────────────

def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _text_filename(text: str, ollama_running: bool) -> str:
    """Build filename.  Uses AI title only when ollama_running is True."""
    prefix = config.get("filename_prefix") or "txtdrop"
    ts     = _timestamp()
    if ollama_running:
        model = config.get("ollama_model") or "llama3"
        title = ollama_client.generate_title(text, model)
        if title:
            return f"{prefix}_{title}_{ts}.txt"
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
        config.history_add("text", filename, filepath)
        config.log_add("INFO", "save", f"[text] {filename}")
        if config.get_bool("sound_enabled"):
            config.log_add("INFO", "sound", "play")
            sound.play_drop()
        notify.show_toast(t("toast_ok"), filename,
                          on_click=log_window.open_log)

    except Exception as e:
        msg = f"[text] {e}"
        config.log_add("ERROR", "save", msg)
        notify.show_toast(t("toast_fail"), str(e),
                          on_click=log_window.open_log, level="error")


# ── Ollama autostart check ────────────────────────────────────────────────────

def _ollama_check():
    config.log_add("INFO", "ollama", "서버 상태 확인 중…")
    if not config.get_bool("ollama_autostart"):
        config.log_add("INFO", "ollama", "자동 시작 비활성화 — 건너뜀")
        return

    # is_running_cached() first call: synchronous check + fills cache for drop_clipboard()
    if ollama_client.is_running_cached():
        models = ollama_client.list_models()
        config.log_add("INFO", "ollama",
                       f"서버 실행 중 — 모델 {len(models)}개: {', '.join(models[:3])}")
        return

    # Auto-start without prompting — user already opted in via the setting
    config.log_add("INFO", "ollama", "서버 미실행 — 자동 시작 시도")
    notify.show_toast("Ollama", t("ollama_starting"), level="info")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        config.log_add("INFO", "ollama", "ollama serve 백그라운드 시작됨")
    except FileNotFoundError:
        config.log_add("WARN", "ollama", "ollama 명령을 찾을 수 없음 — 설치 확인 필요")
        notify.show_toast("Ollama", t("ollama_not_found"), level="error")
        return

    def _wait_and_refresh():
        time.sleep(5)   # ollama takes a few seconds to be ready
        ollama_client._refresh_cache()
        if ollama_client._cached_running:
            models = ollama_client.list_models()
            config.log_add("INFO", "ollama",
                           f"자동 시작 완료 — 모델 {len(models)}개: {', '.join(models[:3])}")
            notify.show_toast("Ollama", t("ollama_started"), level="info")
        else:
            config.log_add("WARN", "ollama", "자동 시작 후 서버 응답 없음")
    threading.Thread(target=_wait_and_refresh, daemon=True).start()


# ── First run ─────────────────────────────────────────────────────────────────

def _first_run() -> bool:
    result = [None]
    event  = threading.Event()

    def _do():
        tmp = tk.Toplevel(tkr.get())
        tmp.withdraw()
        tmp.attributes("-topmost", True)
        messagebox.showinfo(t("first_run_title"), t("first_run_msg"), parent=tmp)
        folder = filedialog.askdirectory(title=t("select_folder"), parent=tmp)
        tmp.destroy()
        result[0] = folder
        event.set()

    tkr.call_on_main(_do)
    event.wait()

    folder = result[0]
    if not folder:
        return False
    config.set("text_save_folder",  folder)
    config.set("image_save_folder", folder)
    config.log_add("INFO", "startup", f"첫 실행 — 저장 폴더 설정: {folder}")
    return True


# ── Dark tray menu ───────────────────────────────────────────────────────────

def _dark_tray_menu(settings_cb, log_cb, exit_cb):
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
        menu.add_command(label=t("settings"),    command=settings_cb)
        menu.add_command(label=t("log_history"), command=log_cb)
        menu.add_separator()
        menu.add_command(label=t("exit"),        command=exit_cb)
        menu.tk_popup(cx, cy)

    tkr.call_on_main(_popup)


def _patch_tray_dark_menu(tray, settings_cb, log_cb, exit_cb):
    """
    Monkey-patch pystray's WM_RBUTTONUP handler to show a custom dark menu
    instead of the native Windows popup.  Falls back silently if pystray's
    internals have changed.
    """
    try:
        import types
        import pystray._win32 as _pw

        WM_LBUTTONUP = 0x0202
        WM_RBUTTONUP = 0x0205

        def _custom_on_notify(self, wparam, lparam):
            if lparam == WM_LBUTTONUP:
                self()   # default left-click action
            elif lparam == WM_RBUTTONUP:
                _dark_tray_menu(settings_cb, log_cb, exit_cb)

        tray._on_notify = types.MethodType(_custom_on_notify, tray)
    except Exception as e:
        config.log_add("WARN", "startup",
                       f"다크 트레이 메뉴 패치 실패 — 네이티브 메뉴 사용: {e}")


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

    config.log_add("INFO", "startup", "TXTDrop 시작됨")

    # First-run folder setup (uses tkr event loop)
    if not config.get("text_save_folder"):
        if not _first_run():
            config.log_add("WARN", "startup", "첫 실행 폴더 선택 취소 — 종료")
            return

    # Ollama check in background
    threading.Thread(target=_ollama_check, daemon=True).start()

    # Register hotkey
    hotkey_state = {"current": config.get("hotkey") or "ctrl+shift+z"}
    keyboard.add_hotkey(
        hotkey_state["current"],
        lambda: threading.Thread(target=drop_clipboard, daemon=True).start(),
    )
    config.log_add("INFO", "startup", f"단축키 등록: {hotkey_state['current']}")

    # ── Tray callbacks ────────────────────────────────────────────────────────

    tray_ref = [None]   # filled after tray creation

    def _do_settings():
        def on_save():
            new_hk = config.get("hotkey") or "ctrl+shift+z"
            if new_hk != hotkey_state["current"]:
                try:
                    keyboard.remove_hotkey(hotkey_state["current"])
                except Exception:
                    pass
                keyboard.add_hotkey(
                    new_hk,
                    lambda: threading.Thread(target=drop_clipboard, daemon=True).start(),
                )
                config.log_add("INFO", "startup",
                               f"단축키 변경: {hotkey_state['current']} → {new_hk}")
                hotkey_state["current"] = new_hk
        settings_window.open_settings(on_save=on_save)

    def _do_log():
        log_window.open_log()

    def _do_exit():
        config.log_add("INFO", "startup", "TXTDrop 종료됨")
        keyboard.unhook_all()
        time.sleep(0.15)  # allow SQLite commit before exit
        if tray_ref[0]:
            tray_ref[0].stop()
        os._exit(0)  # OS-level kill: bypasses Tkinter exception swallowing, kills all threads

    # pystray native-menu callbacks (keep for fallback / accessibility)
    def on_settings(icon, item): _do_settings()
    def on_log(icon, item):      _do_log()
    def on_exit(icon, item):     _do_exit()

    tray = pystray.Icon(
        name="TXTDrop",
        icon=_make_icon(),
        title="TXTDrop",
        menu=pystray.Menu(
            pystray.MenuItem(lambda item: t("settings"),    on_settings),
            pystray.MenuItem(lambda item: t("log_history"), on_log),
            pystray.MenuItem(lambda item: t("exit"),        on_exit),
        ),
    )
    tray_ref[0] = tray

    # Replace native right-click menu with custom dark Tk menu
    _patch_tray_dark_menu(tray, _do_settings, _do_log, _do_exit)

    # Run pystray in a background thread so the main thread can own mainloop()
    tray.run_detached()

    # Block the main thread with the Tk event loop — required on Windows
    tkr.get().mainloop()


if __name__ == "__main__":
    main()
