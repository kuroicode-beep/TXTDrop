import os
import sys
import sqlite3
import datetime
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import keyboard
import pyperclip
from PIL import Image, ImageGrab, ImageDraw
import pystray

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "txtdrop.db")


# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------

def db_connect():
    return sqlite3.connect(DB_FILE)


def db_init():
    with db_connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                saved_at  TEXT NOT NULL,
                type      TEXT NOT NULL,
                filename  TEXT NOT NULL,
                filepath  TEXT NOT NULL
            );
        """)


def config_get(key):
    with db_connect() as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else None


def config_set(key, value):
    with db_connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )


def history_add(type_, filename, filepath):
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO history (saved_at, type, filename, filepath) VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), type_, filename, filepath),
        )


# ------------------------------------------------------------------
# UI helpers
# ------------------------------------------------------------------

def pick_folder(title="Select Save Folder"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title=title, parent=root)
    root.destroy()
    return folder or None


def backup_db():
    folder = pick_folder("TXTDrop — Select Backup Destination")
    if not folder:
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(folder, f"txtdrop_backup_{ts}.db")

    try:
        # Use SQLite online backup API to ensure a consistent snapshot
        src = db_connect()
        dst = sqlite3.connect(dest)
        with dst:
            src.backup(dst)
        dst.close()
        src.close()
        _notify(f"Backup saved:\n{dest}")
    except Exception as e:
        _notify(f"Backup failed:\n{e}", error=True)


def restore_db():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    src_path = filedialog.askopenfilename(
        title="TXTDrop — Select Backup File to Restore",
        filetypes=[("TXTDrop Database", "*.db"), ("All files", "*.*")],
        parent=root,
    )
    root.destroy()

    if not src_path:
        return

    # Confirm before overwriting
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    confirmed = messagebox.askyesno(
        "TXTDrop — Restore",
        f"Restore database from:\n{src_path}\n\nCurrent data will be overwritten. Continue?",
        parent=root,
    )
    root.destroy()

    if not confirmed:
        return

    try:
        src = sqlite3.connect(src_path)
        dst = db_connect()
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        _notify("Restore complete.\nRestart TXTDrop to apply changes.")
    except Exception as e:
        _notify(f"Restore failed:\n{e}", error=True)


def _notify(message, error=False):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if error:
        messagebox.showerror("TXTDrop", message, parent=root)
    else:
        messagebox.showinfo("TXTDrop", message, parent=root)
    root.destroy()


def make_tray_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        d.rounded_rectangle([4, 4, 60, 60], radius=10, fill=(41, 128, 185))
    except AttributeError:
        d.rectangle([4, 4, 60, 60], fill=(41, 128, 185))
    d.rectangle([16, 16, 48, 23], fill="white")  # top bar
    d.rectangle([28, 16, 36, 50], fill="white")  # stem
    return img


# ------------------------------------------------------------------
# Clipboard
# ------------------------------------------------------------------

def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def drop_clipboard(save_folder):
    # Image takes priority over text
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            filename = f"txtdrop_{timestamp()}.png"
            filepath = os.path.join(save_folder, filename)
            img.save(filepath, "PNG")
            history_add("image", filename, filepath)
            return
    except Exception:
        pass

    try:
        text = pyperclip.paste()
        if text and text.strip():
            filename = f"txtdrop_{timestamp()}.txt"
            filepath = os.path.join(save_folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            history_add("text", filename, filepath)
    except Exception:
        pass


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    db_init()

    save_folder = config_get("save_folder")
    if not save_folder or not os.path.isdir(save_folder):
        save_folder = pick_folder("TXTDrop — Select Save Folder")
        if not save_folder:
            return
        config_set("save_folder", save_folder)

    state = {"save_folder": save_folder}

    def on_hotkey():
        drop_clipboard(state["save_folder"])

    keyboard.add_hotkey("ctrl+shift+z", on_hotkey)

    def on_change_folder(icon, item):
        def do():
            folder = pick_folder("TXTDrop — Change Save Folder")
            if folder:
                state["save_folder"] = folder
                config_set("save_folder", folder)
        threading.Thread(target=do, daemon=True).start()

    def on_backup_db(icon, item):
        threading.Thread(target=backup_db, daemon=True).start()

    def on_restore_db(icon, item):
        threading.Thread(target=restore_db, daemon=True).start()

    def on_exit(icon, item):
        keyboard.unhook_all()
        icon.stop()

    tray = pystray.Icon(
        name="TXTDrop",
        icon=make_tray_icon(),
        title="TXTDrop",
        menu=pystray.Menu(
            pystray.MenuItem("Change Folder", on_change_folder),
            pystray.MenuItem("Backup Database", on_backup_db),
            pystray.MenuItem("Restore Database", on_restore_db),
            pystray.MenuItem("Exit", on_exit),
        ),
    )
    tray.run()


if __name__ == "__main__":
    main()
