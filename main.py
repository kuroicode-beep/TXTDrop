import os
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import keyboard
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
        import pyperclip
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
    if ollama_client.is_running():
        models = ollama_client.list_models()
        config.log_add("INFO", "ollama",
                       f"서버 실행 중 — 모델 {len(models)}개: {', '.join(models[:3])}")
        return

    config.log_add("WARN", "ollama", "서버 미실행 — 사용자에게 확인 요청")

    result = [False]
    event  = threading.Event()

    def _ask():
        tmp = tk.Toplevel(tkr.get())
        tmp.withdraw()
        tmp.attributes("-topmost", True)
        result[0] = messagebox.askyesno(
            "TXTDrop — Ollama", t("ollama_prompt"), parent=tmp
        )
        tmp.destroy()
        event.set()

    tkr.call_on_main(_ask)
    event.wait()

    if result[0]:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        config.log_add("INFO", "ollama", "ollama serve 백그라운드 시작됨")
    else:
        config.log_add("INFO", "ollama", "사용자가 Ollama 시작 취소")


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

    # Start the shared Tk root FIRST so UI calls work before tray.run()
    tkr.init()
    tkr.start()

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

    def on_settings(icon, item):
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

    def on_log(icon, item):
        log_window.open_log()

    def on_exit(icon, item):
        config.log_add("INFO", "startup", "TXTDrop 종료됨")
        keyboard.unhook_all()
        icon.stop()

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
    tray.run()


if __name__ == "__main__":
    main()
