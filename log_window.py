"""
log_window.py — TXTDrop log history viewer.

Two tabs:
  [로그]        — colour-coded log stream, auto-refreshes every 5 s
  [저장 기록]   — Treeview of saved files, double-click opens the file
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import config
from i18n import t

_BG     = "#111111"
_BG2    = "#1c1c1c"
_BG3    = "#242424"
_FG     = "#f0f0f0"
_DIM    = "#888888"
_ACCENT = "#ffd600"
_BORDER = "#383838"

_COL_INFO  = "#81c995"
_COL_WARN  = "#ffd600"
_COL_ERROR = "#f28b82"

_CAT_COLOUR  = {"startup": "#69b4ff", "ollama": "#c792ea", "save": "#82aaff"}
_CAT_DEFAULT = "#888888"

_singleton_lock = threading.Lock()
_singleton_win  = [None]


def open_log():
    """Open (or raise) the log window.  Safe to call from any thread."""
    import tk_root as tkr
    with _singleton_lock:
        if _singleton_win[0] is not None:
            tkr.call_on_main(_raise_win)
            return
    tkr.call_on_main(_create)


# ── Private (Tk-thread only) ──────────────────────────────────────────────────

def _raise_win():
    w = _singleton_win[0]
    if w:
        try:
            w.lift()
            w.focus_force()
        except tk.TclError:
            with _singleton_lock:
                _singleton_win[0] = None


def _create():
    import tk_root as tkr
    root = tkr.get()

    win = tk.Toplevel(root)
    win.title(t("log_title"))
    win.configure(bg=_BG)
    win.geometry("800x560")
    win.attributes("-topmost", True)
    win.resizable(True, True)

    with _singleton_lock:
        _singleton_win[0] = win

    def on_close():
        with _singleton_lock:
            _singleton_win[0] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    # ── TTK dark styles ───────────────────────────────────────────────────────
    s = ttk.Style()
    s.configure("TNotebook",     background=_BG,  borderwidth=0, tabmargins=0)
    s.configure("TNotebook.Tab", background=_BG3, foreground=_DIM,
                font=("Malgun Gothic", 9), padding=[14, 5])
    s.map("TNotebook.Tab",
          background=[("selected", _BG2),   ("active", _BG3)],
          foreground=[("selected", _ACCENT), ("active", _FG)])

    s.configure("Hist.Treeview",
                background="#0c0c0c", foreground=_FG,
                fieldbackground="#0c0c0c", rowheight=22,
                font=("Consolas", 9))
    s.configure("Hist.Treeview.Heading",
                background=_BG3, foreground=_DIM,
                font=("Malgun Gothic", 9, "bold"), relief="flat")
    s.map("Hist.Treeview",
          background=[("selected", "#2a4a7a")],
          foreground=[("selected", _FG)])

    # ── Header ────────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg=_BG2, pady=12)
    hdr.pack(fill="x")
    tk.Label(hdr, text="TXTDrop", bg=_BG2, fg=_ACCENT,
             font=("Malgun Gothic", 14, "bold")).pack(side="left", padx=18)
    tk.Label(hdr, text=t("log_title").split("—")[-1].strip(), bg=_BG2, fg=_DIM,
             font=("Malgun Gothic", 10)).pack(side="left", padx=2)

    # ── Notebook ──────────────────────────────────────────────────────────────
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True)

    # ════════════════════════════════════════════════════
    # Tab 1 — 로그
    # ════════════════════════════════════════════════════
    log_frame = tk.Frame(nb, bg=_BG)
    nb.add(log_frame, text=f"  {t('tab_log')}  ")

    txt_frame = tk.Frame(log_frame, bg=_BG)
    txt_frame.pack(fill="both", expand=True)

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

    hsb = tk.Scrollbar(log_frame, orient="horizontal", bg=_BG3,
                       troughcolor=_BG, bd=0, relief="flat",
                       highlightthickness=0)
    hsb.pack(fill="x")
    txt.config(xscrollcommand=hsb.set)
    hsb.config(command=txt.xview)

    txt.tag_config("time",        foreground=_DIM)
    txt.tag_config("INFO",        foreground=_COL_INFO)
    txt.tag_config("WARN",        foreground=_COL_WARN)
    txt.tag_config("ERROR",       foreground=_COL_ERROR)
    txt.tag_config("msg",         foreground=_FG)
    for cat, col in _CAT_COLOUR.items():
        txt.tag_config(f"cat_{cat}", foreground=col)
    txt.tag_config("cat_default", foreground=_CAT_DEFAULT)

    _last_log_id = [0]

    def _load_log():
        entries = config.log_get(1000)
        _last_log_id[0] = config.log_last_id()
        txt.config(state="normal")
        txt.delete("1.0", "end")
        if not entries:
            txt.insert("end", f"\n  {t('log_empty')}\n", "time")
        else:
            for e in entries:
                time_str = e["time"][:19].replace("T", " ")
                level    = e["level"].upper()
                category = e["category"].lower()
                msg      = e["message"]
                cat_tag  = f"cat_{category}" if category in _CAT_COLOUR else "cat_default"
                lvl_tag  = level if level in ("INFO", "WARN", "ERROR") else "INFO"
                txt.insert("end", f"{time_str}  ", "time")
                txt.insert("end", f"[{level:<5}]", lvl_tag)
                txt.insert("end", f" [{category:<8}] ", cat_tag)
                txt.insert("end", f"{msg}\n", "msg")
        txt.config(state="disabled")

    _load_log()

    def _auto_refresh():
        try:
            latest = config.log_last_id()
            if latest != _last_log_id[0]:
                _load_log()
            win.after(5000, _auto_refresh)
        except tk.TclError:
            pass   # window destroyed

    win.after(5000, _auto_refresh)

    # ════════════════════════════════════════════════════
    # Tab 2 — 저장 기록
    # ════════════════════════════════════════════════════
    hist_frame = tk.Frame(nb, bg=_BG)
    nb.add(hist_frame, text=f"  {t('tab_history')}  ")

    columns = ("time", "type", "filename")
    tree = ttk.Treeview(hist_frame, columns=columns, show="headings",
                        style="Hist.Treeview", selectmode="browse")
    tree.heading("time",     text=t("hist_col_time"))
    tree.heading("type",     text=t("hist_col_type"))
    tree.heading("filename", text=t("hist_col_file"))
    tree.column("time",     width=160, minwidth=120, anchor="w",      stretch=False)
    tree.column("type",     width=65,  minwidth=50,  anchor="center", stretch=False)
    tree.column("filename", width=520, minwidth=200, anchor="w",      stretch=True)

    tree.tag_configure("text",  foreground="#82aaff")
    tree.tag_configure("image", foreground="#c792ea")

    hsb_tree = ttk.Scrollbar(hist_frame, orient="horizontal", command=tree.xview)
    vsb_tree = ttk.Scrollbar(hist_frame, orient="vertical",   command=tree.yview)
    tree.configure(xscrollcommand=hsb_tree.set, yscrollcommand=vsb_tree.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb_tree.grid(row=0, column=1, sticky="ns")
    hsb_tree.grid(row=1, column=0, sticky="ew")
    hist_frame.rowconfigure(0, weight=1)
    hist_frame.columnconfigure(0, weight=1)

    _filepath_map: dict[str, str] = {}

    def _load_history():
        for iid in tree.get_children():
            tree.delete(iid)
        _filepath_map.clear()
        for entry in config.history_get(500):
            time_str = entry["time"][:19].replace("T", " ")
            iid = tree.insert(
                "", "end",
                values=(time_str, entry["type"], entry["filename"]),
                tags=(entry["type"],),
            )
            _filepath_map[iid] = entry["filepath"]

    _load_history()

    def on_dbl_click(event):
        iid = tree.focus()
        if not iid:
            return
        fp = _filepath_map.get(iid, "")
        if fp and os.path.exists(fp):
            os.startfile(fp)
        else:
            messagebox.showwarning(
                "TXTDrop", f"{t('file_not_found')}\n{fp}", parent=win
            )

    tree.bind("<Double-1>", on_dbl_click)

    # ── Footer buttons ────────────────────────────────────────────────────────
    sep = tk.Frame(win, bg=_BORDER, height=1)
    sep.pack(fill="x")

    btn_row = tk.Frame(win, bg=_BG2, pady=10, padx=16)
    btn_row.pack(fill="x")

    def do_clear():
        config.log_clear()
        _load_log()

    def do_refresh():
        _load_log()
        _load_history()

    tk.Button(btn_row, text=t("log_clear"), command=do_clear,
              bg="#3a3a3a", fg=_COL_ERROR, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=14, pady=5,
              cursor="hand2").pack(side="left")

    tk.Button(btn_row, text=t("log_refresh"), command=do_refresh,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=14, pady=5,
              cursor="hand2").pack(side="left", padx=(8, 0))

    tk.Button(btn_row, text=t("close"), command=on_close,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=16, pady=5,
              cursor="hand2").pack(side="right")
