"""
notify.py — corner toast notifications for TXTDrop.

show_toast() runs in a daemon thread and creates a small dark overlay
in the bottom-right corner of the screen.  Auto-dismisses after 4 s.
Clicking anywhere on the toast calls on_click (if provided).
"""
import threading
import tkinter as tk

_BG     = "#1a1a1a"
_FG     = "#f0f0f0"
_DIM    = "#888888"
_GREEN  = "#81c995"
_RED    = "#f28b82"
_YELLOW = "#ffd600"


def show_toast(title: str, body: str, on_click=None, level: str = "info"):
    """Fire-and-forget toast.  level: 'info' | 'error'"""
    threading.Thread(
        target=_run, args=(title, body, on_click, level), daemon=True
    ).start()


def _run(title: str, body: str, on_click, level: str):
    from i18n import t  # lazy — avoids import-time circular dep

    accent = _RED if level == "error" else _GREEN

    win = tk.Tk()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=accent)

    # 1-px accent border via outer frame colour
    inner = tk.Frame(win, bg=_BG, padx=14, pady=10)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    # header row: "TXTDrop  <title>"
    hdr = tk.Frame(inner, bg=_BG)
    hdr.pack(fill="x")
    tk.Label(hdr, text="TXTDrop", bg=_BG, fg=accent,
             font=("Malgun Gothic", 9, "bold")).pack(side="left")
    tk.Label(hdr, text=f"  {title}", bg=_BG, fg=_DIM,
             font=("Malgun Gothic", 9)).pack(side="left")

    # body message
    tk.Label(inner, text=body, bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), anchor="w", justify="left",
             wraplength=270).pack(fill="x", pady=(6, 0))

    # hint line when clickable
    if on_click:
        tk.Label(inner, text=t("toast_hint"), bg=_BG, fg=_DIM,
                 font=("Malgun Gothic", 8)).pack(anchor="w", pady=(4, 0))

    # position: bottom-right corner
    win.update_idletasks()
    w  = max(win.winfo_reqwidth(), 300)
    h  = win.winfo_reqheight()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 52}")

    clicked = [False]

    def dismiss(evt=None):
        try:
            win.destroy()
        except Exception:
            pass
        if clicked[0] and on_click:
            threading.Thread(target=on_click, daemon=True).start()

    def on_click_evt(evt):
        clicked[0] = True
        dismiss()

    _bind_recursive(win, on_click_evt)
    win.after(4000, dismiss)
    win.mainloop()


def _bind_recursive(widget, handler):
    widget.bind("<Button-1>", handler)
    for child in widget.winfo_children():
        _bind_recursive(child, handler)
