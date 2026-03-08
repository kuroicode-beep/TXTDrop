import os
import sys
import json
import datetime
import threading
import tkinter as tk
from tkinter import filedialog

import keyboard
import pyperclip
from PIL import Image, ImageGrab, ImageDraw
import pystray

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


def pick_folder(title="Select Save Folder"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title=title, parent=root)
    root.destroy()
    return folder or None


def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def drop_clipboard(save_folder):
    # Image takes priority over text
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            path = os.path.join(save_folder, f"txtdrop_{timestamp()}.png")
            img.save(path, "PNG")
            return
    except Exception:
        pass

    try:
        text = pyperclip.paste()
        if text and text.strip():
            path = os.path.join(save_folder, f"txtdrop_{timestamp()}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    except Exception:
        pass


def make_tray_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        d.rounded_rectangle([4, 4, 60, 60], radius=10, fill=(41, 128, 185))
    except AttributeError:
        d.rectangle([4, 4, 60, 60], fill=(41, 128, 185))
    # White "T"
    d.rectangle([16, 16, 48, 23], fill="white")  # top bar
    d.rectangle([28, 16, 36, 50], fill="white")  # stem
    return img


def main():
    config = load_config()

    if not config.get("save_folder") or not os.path.isdir(config["save_folder"]):
        folder = pick_folder("TXTDrop — Select Save Folder")
        if not folder:
            return
        config["save_folder"] = folder
        save_config(config)

    state = {"save_folder": config["save_folder"]}

    def on_hotkey():
        drop_clipboard(state["save_folder"])

    keyboard.add_hotkey("ctrl+shift+z", on_hotkey)

    def on_change_folder(icon, item):
        def do():
            folder = pick_folder("TXTDrop — Change Save Folder")
            if folder:
                state["save_folder"] = folder
                config["save_folder"] = folder
                save_config(config)
        threading.Thread(target=do, daemon=True).start()

    def on_exit(icon, item):
        keyboard.unhook_all()
        icon.stop()

    tray = pystray.Icon(
        name="TXTDrop",
        icon=make_tray_icon(),
        title="TXTDrop",
        menu=pystray.Menu(
            pystray.MenuItem("Change Folder", on_change_folder),
            pystray.MenuItem("Exit", on_exit),
        ),
    )
    tray.run()


if __name__ == "__main__":
    main()
