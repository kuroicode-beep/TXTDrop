"""
log_window.py — TXTDrop log history viewer.

open_log() launches the window in a daemon thread.
Shows newest entries first, colour-coded by level.
"""
import threading
import tkinter as tk
from tkinter import ttk

import config
from i18n import t

_BG     = "#111111"
_BG2    = "#1c1c1c"
_BG3    = "#242424"
_FG     = "#f0f0f0"
_DIM    = "#888888"
_ACCENT = "#ffd600"
_BORDER = "#383838"

# log level colours
_COL_INFO  = "#81c995"   # green
_COL_WARN  = "#ffd600"   # yellow
_COL_ERROR = "#f28b82"   # red

# category colours
_CAT_COLOUR = {
    "startup": "#69b4ff",
    "ollama":  "#c792ea",
    "save":    "#82aaff",
}
_CAT_DEFAULT = "#888888"

_singleton_lock = threading.Lock()
_singleton_win  = [None]


def open_log():
    """Open (or raise) the log history window."""
    with _singleton_lock:
        if _singleton_win[0] is not None:
            try:
                _singleton_win[0].lift()
                _singleton_win[0].focus_force()
                return
            except Exception:
                _singleton_win[0] = None

    threading.Thread(target=_run, daemon=True).start()


def _run():
    win = tk.Tk()
    win.title(t("log_title"))
    win.configure(bg=_BG)
    win.geometry("760x520")
    win.attributes("-topmost", True)
    win.resizable(True, True)

    with _singleton_lock:
        _singleton_win[0] = win

    def on_close():
        with _singleton_lock:
            _singleton_win[0] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    # ── header ────────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg=_BG2, pady=12)
    hdr.pack(fill="x")
    tk.Label(hdr, text="TXTDrop", bg=_BG2, fg=_ACCENT,
             font=("Malgun Gothic", 14, "bold")).pack(side="left", padx=18)
    tk.Label(hdr, text=t("log_title").split("—")[-1].strip(), bg=_BG2, fg=_DIM,
             font=("Malgun Gothic", 10)).pack(side="left", padx=2)

    # ── text area ─────────────────────────────────────────────────────────────
    txt_frame = tk.Frame(win, bg=_BG)
    txt_frame.pack(fill="both", expand=True, padx=0, pady=0)

    sb = tk.Scrollbar(txt_frame, bg=_BG3, troughcolor=_BG, bd=0,
                      relief="flat", highlightthickness=0)
    sb.pack(side="right", fill="y")

    txt = tk.Text(
        txt_frame,
        bg="#0c0c0c", fg=_FG,
        font=("Consolas", 9),
        yscrollcommand=sb.set,
        wrap="none",
        relief="flat", bd=0,
        padx=12, pady=8,
        state="disabled",
        selectbackground=_BG3,
    )
    txt.pack(side="left", fill="both", expand=True)
    sb.config(command=txt.yview)

    # horizontal scrollbar
    hsb = tk.Scrollbar(win, orient="horizontal", bg=_BG3,
                       troughcolor=_BG, bd=0, relief="flat",
                       highlightthickness=0)
    hsb.pack(fill="x")
    txt.config(xscrollcommand=hsb.set)
    hsb.config(command=txt.xview)

    # tags
    txt.tag_config("time",      foreground=_DIM)
    txt.tag_config("INFO",      foreground=_COL_INFO)
    txt.tag_config("WARN",      foreground=_COL_WARN)
    txt.tag_config("ERROR",     foreground=_COL_ERROR)
    txt.tag_config("msg",       foreground=_FG)
    for cat, col in _CAT_COLOUR.items():
        txt.tag_config(f"cat_{cat}", foreground=col)
    txt.tag_config("cat_default", foreground=_CAT_DEFAULT)

    def _load():
        entries = config.log_get(1000)
        txt.config(state="normal")
        txt.delete("1.0", "end")
        if not entries:
            txt.insert("end", f"\n  {t('log_empty')}\n", "time")
        else:
            for e in entries:           # already newest-first from log_get()
                time_str = e["time"][:19].replace("T", " ")
                level    = e["level"].upper()
                category = e["category"].lower()
                msg      = e["message"]

                cat_tag = f"cat_{category}" if category in _CAT_COLOUR else "cat_default"
                lvl_tag = level if level in ("INFO", "WARN", "ERROR") else "INFO"

                txt.insert("end", f"{time_str}  ", "time")
                txt.insert("end", f"[{level:<5}]", lvl_tag)
                txt.insert("end", f" [{category:<8}] ", cat_tag)
                txt.insert("end", f"{msg}\n", "msg")
        txt.config(state="disabled")

    _load()

    # ── footer buttons ────────────────────────────────────────────────────────
    sep = tk.Frame(win, bg=_BORDER, height=1)
    sep.pack(fill="x")

    btn_row = tk.Frame(win, bg=_BG2, pady=10, padx=16)
    btn_row.pack(fill="x")

    def do_clear():
        config.log_clear()
        _load()

    tk.Button(btn_row, text=t("log_clear"), command=do_clear,
              bg="#3a3a3a", fg=_COL_ERROR, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=14, pady=5,
              cursor="hand2").pack(side="left")

    tk.Button(btn_row, text=t("log_refresh"), command=_load,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=14, pady=5,
              cursor="hand2").pack(side="left", padx=(8, 0))

    tk.Button(btn_row, text=t("cancel"), command=on_close,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=16, pady=5,
              cursor="hand2").pack(side="right")

    win.mainloop()
