"""
dedup_window.py — TXTDrop 중복제거 창.

[중복제거 실행] 버튼으로 기존 저장 기록 전체를 검사하고,
휴지통(trash 테이블) 목록에서 선택 복구할 수 있다.
row만 이동하며 실제 파일은 건드리지 않는다.
"""
import threading
import tkinter as tk
from tkinter import ttk

import config
import dedup
from i18n import t

_BG     = "#111111"
_BG2    = "#1c1c1c"
_BG3    = "#242424"
_FG     = "#f0f0f0"
_DIM    = "#888888"
_ACCENT = "#ffd600"
_BORDER = "#383838"

_singleton_lock = threading.Lock()
_singleton_win  = [None]


def open_dedup():
    """Open (or raise) the dedup window.  Safe to call from any thread."""
    import tk_root as tkr
    with _singleton_lock:
        if _singleton_win[0] is not None:
            tkr.call_on_main(_raise_win)
            return
    tkr.call_on_main(_create)


def _raise_win():
    import tk_root as tkr
    w = _singleton_win[0]
    if w:
        try:
            w.lift()
            w.focus_force()
        except tk.TclError:
            with _singleton_lock:
                _singleton_win[0] = None
            tkr.call_on_main(_create)


# ── Private (Tk-thread only) ──────────────────────────────────────────────────

def _create():
    import tk_root as tkr
    root = tkr.get()

    win = tk.Toplevel(root)
    win.title(t("dedup_title"))
    win.configure(bg=_BG)
    win.geometry("820x560")
    win.attributes("-topmost", True)
    win.resizable(True, True)

    with _singleton_lock:
        _singleton_win[0] = win

    def on_close():
        with _singleton_lock:
            _singleton_win[0] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    s = ttk.Style()
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
    tk.Label(hdr, text=t("tray_dedup"), bg=_BG2, fg=_DIM,
             font=("Malgun Gothic", 10)).pack(side="left", padx=2)

    # ── Control row ───────────────────────────────────────────────────────────
    ctl = tk.Frame(win, bg=_BG, padx=16, pady=10)
    ctl.pack(fill="x")

    run_btn = tk.Button(ctl, text=t("dedup_run"),
                        bg=_ACCENT, fg="#000",
                        font=("Malgun Gothic", 10, "bold"),
                        relief="flat", bd=0, padx=18, pady=7, cursor="hand2")
    run_btn.pack(side="left")

    tk.Label(ctl, text=t("dedup_threshold"), bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10)).pack(side="left", padx=(18, 6))
    v_threshold = tk.StringVar(value=config.get("dedup_threshold") or "90")
    tk.Spinbox(ctl, from_=70, to=100, textvariable=v_threshold, width=5,
               bg=_BG3, fg=_FG, insertbackground=_FG,
               buttonbackground=_BG3, relief="flat",
               highlightthickness=1, highlightbackground=_BORDER,
               font=("Malgun Gothic", 10)).pack(side="left")

    status_lbl = tk.Label(ctl, text="", bg=_BG, fg=_DIM,
                          font=("Malgun Gothic", 10))
    status_lbl.pack(side="left", padx=(18, 0))

    # ── Trash list (휴지통) ───────────────────────────────────────────────────
    body = tk.Frame(win, bg=_BG)
    body.pack(fill="both", expand=True, padx=16, pady=(0, 4))

    columns = ("trashed", "filename", "reason")
    tree = ttk.Treeview(body, columns=columns, show="headings",
                        style="Hist.Treeview", selectmode="extended")
    tree.heading("trashed",  text=t("dedup_col_trashed"))
    tree.heading("filename", text=t("dedup_col_file"))
    tree.heading("reason",   text=t("dedup_col_reason"))
    tree.column("trashed",  width=150, minwidth=120, anchor="w", stretch=False)
    tree.column("filename", width=280, minwidth=160, anchor="w", stretch=True)
    tree.column("reason",   width=320, minwidth=160, anchor="w", stretch=True)

    vsb = ttk.Scrollbar(body, orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(body, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    body.rowconfigure(0, weight=1)
    body.columnconfigure(0, weight=1)

    _trash_ids: dict[str, int] = {}

    def _load_trash():
        for iid in tree.get_children():
            tree.delete(iid)
        _trash_ids.clear()
        for e in config.trash_get(500):
            time_str = e["trashed_at"][:19].replace("T", " ")
            iid = tree.insert("", "end",
                              values=(time_str, e["filename"], e["reason"]))
            _trash_ids[iid] = e["id"]

    _load_trash()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _set_status(text: str):
        try:
            status_lbl.config(text=text)
        except tk.TclError:
            pass

    def do_run():
        try:
            threshold = max(70, min(100, int(v_threshold.get())))
        except ValueError:
            threshold = 90
        v_threshold.set(str(threshold))
        config.set("dedup_threshold", str(threshold))

        run_btn.config(state="disabled")
        _set_status(t("dedup_running", done=0, total=0))

        def _progress(done, total):
            win.after(0, lambda: _set_status(
                t("dedup_running", done=done, total=total)))

        def _work():
            moved, missing = dedup.scan_existing(threshold, _progress)

            def _finish():
                try:
                    run_btn.config(state="normal")
                    _load_trash()
                    if moved:
                        _set_status(t("dedup_result",
                                      n=len(moved), missing=missing))
                    else:
                        _set_status(t("dedup_none"))
                except tk.TclError:
                    pass
            win.after(0, _finish)

        threading.Thread(target=_work, daemon=True).start()

    def do_restore():
        selected = tree.selection()
        if not selected:
            return
        n = 0
        for iid in selected:
            tid = _trash_ids.get(iid)
            if tid is not None and config.trash_restore(tid):
                n += 1
        config.log_add("INFO", "dedup", f"휴지통 복구: {n}건")
        _load_trash()
        _set_status(t("dedup_restored", n=n))

    run_btn.config(command=do_run)

    # ── Footer ────────────────────────────────────────────────────────────────
    tk.Frame(win, bg=_BORDER, height=1).pack(fill="x")
    btn_row = tk.Frame(win, bg=_BG2, pady=10, padx=16)
    btn_row.pack(fill="x")

    tk.Button(btn_row, text=t("dedup_restore"), command=do_restore,
              bg=_BG3, fg="#81c995", font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=14, pady=5,
              cursor="hand2").pack(side="left")

    tk.Button(btn_row, text=t("log_refresh"), command=_load_trash,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=14, pady=5,
              cursor="hand2").pack(side="left", padx=(8, 0))

    tk.Button(btn_row, text=t("close"), command=on_close,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=16, pady=5,
              cursor="hand2").pack(side="right")
