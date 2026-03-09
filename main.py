import os
import sys
import sqlite3
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import keyboard
import pyperclip
from PIL import Image, ImageGrab, ImageDraw
import pystray

import config
import ollama_client
import sound
import settings_window
from i18n import t


# ── Filename helpers ──────────────────────────────────────────────────────────

def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _text_filename(text: str) -> str:
    """Build filename for a text clip. Uses AI title when Ollama is available."""
    prefix = config.get("filename_prefix") or "txtdrop"
    ts     = _timestamp()

    if ollama_client.is_running():
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
    return _text_folder()   # fallback


# ── Clipboard save ────────────────────────────────────────────────────────────

def drop_clipboard():
    # ── Image ────────────────────────────────────────────────────────────────
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            folder = _image_folder()
            if not folder:
                return
            filename = _image_filename()
            filepath = os.path.join(folder, filename)
            img.save(filepath, "PNG")
            config.history_add("image", filename, filepath)
            if config.get_bool("sound_enabled"):
                sound.play_drop()
            return
    except Exception:
        pass

    # ── Text ─────────────────────────────────────────────────────────────────
    try:
        text = pyperclip.paste()
        if text and text.strip():
            folder = _text_folder()
            if not folder:
                return
            filename = _text_filename(text)
            filepath = os.path.join(folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            config.history_add("text", filename, filepath)
            if config.get_bool("sound_enabled"):
                sound.play_drop()
    except Exception:
        pass


# ── DB helpers ────────────────────────────────────────────────────────────────

def _backup_db():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(
        title="TXTDrop — Select Backup Destination", parent=root
    )
    root.destroy()
    if not folder:
        return

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(folder, f"txtdrop_backup_{ts}.db")
    try:
        src = sqlite3.connect(config.DB_FILE)
        dst = sqlite3.connect(dest)
        with dst:
            src.backup(dst)
        dst.close()
        src.close()
        _notify(t("backup_success", path=dest))
    except Exception as e:
        _notify(t("backup_fail", err=e), error=True)


def _restore_db():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    src_path = filedialog.askopenfilename(
        title="TXTDrop — Select Backup File",
        filetypes=[("TXTDrop Database", "*.db"), ("All files", "*.*")],
        parent=root,
    )
    root.destroy()
    if not src_path:
        return

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    ok = messagebox.askyesno("TXTDrop", t("restore_confirm"), parent=root)
    root.destroy()
    if not ok:
        return

    try:
        src = sqlite3.connect(src_path)
        dst = sqlite3.connect(config.DB_FILE)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        _notify(t("restore_success"))
    except Exception as e:
        _notify(t("restore_fail", err=e), error=True)


def _notify(message: str, error: bool = False):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if error:
        messagebox.showerror("TXTDrop", message, parent=root)
    else:
        messagebox.showinfo("TXTDrop", message, parent=root)
    root.destroy()


# ── Ollama autostart check ────────────────────────────────────────────────────

def _ollama_check():
    if not config.get_bool("ollama_autostart"):
        return
    if ollama_client.is_running():
        return

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    ok = messagebox.askyesno("TXTDrop — Ollama", t("ollama_prompt"), parent=root)
    root.destroy()

    if ok:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )


# ── First run ─────────────────────────────────────────────────────────────────

def _first_run() -> bool:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(t("first_run_title"), t("first_run_msg"), parent=root)
    root.destroy()

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title=t("select_folder"), parent=root)
    root.destroy()

    if not folder:
        return False

    config.set("text_save_folder",  folder)
    config.set("image_save_folder", folder)
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

    # First-run folder setup
    if not config.get("text_save_folder"):
        if not _first_run():
            return

    # Ollama check in background
    threading.Thread(target=_ollama_check, daemon=True).start()

    # Register hotkey
    hotkey_state = {"current": config.get("hotkey") or "ctrl+shift+z"}
    keyboard.add_hotkey(
        hotkey_state["current"],
        lambda: threading.Thread(target=drop_clipboard, daemon=True).start(),
    )

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
                hotkey_state["current"] = new_hk
        settings_window.open_settings(on_save=on_save)

    def on_backup(icon, item):
        threading.Thread(target=_backup_db, daemon=True).start()

    def on_restore(icon, item):
        threading.Thread(target=_restore_db, daemon=True).start()

    def on_exit(icon, item):
        keyboard.unhook_all()
        icon.stop()

    tray = pystray.Icon(
        name="TXTDrop",
        icon=_make_icon(),
        title="TXTDrop",
        menu=pystray.Menu(
            pystray.MenuItem(lambda item: t("settings"), on_settings),
            pystray.MenuItem(lambda item: t("backup_db"), on_backup),
            pystray.MenuItem(lambda item: t("restore_db"), on_restore),
            pystray.MenuItem(lambda item: t("exit"), on_exit),
        ),
    )
    tray.run()


if __name__ == "__main__":
    main()
