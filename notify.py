"""
notify.py — corner toast notifications for TXTDrop.

Uses the shared hidden tk.Tk root (tk_root module) so every toast is a
tk.Toplevel — no separate Tk() per thread, no message-queue collisions.

Toasts stack upward from the bottom-right corner and reposition when one
is dismissed.

All functions that touch Tk widgets run on the Tk event-loop thread via
tk_root.call_on_main().
"""
import threading
import tkinter as tk

_BG    = "#1a1a1a"
_FG    = "#f0f0f0"
_DIM   = "#888888"
_GREEN = "#81c995"
_RED   = "#f28b82"

# Accessed exclusively from the Tk thread — no locking required.
_active: list[dict] = []   # {"win", "h", "x", "sh"}


def show_toast(title: str, body: str, on_click=None, level: str = "info"):
    """Fire-and-forget.  Safe to call from any thread."""
    import tk_root as tkr
    tkr.call_on_main(_create, title, body, on_click, level)


# ── Private (Tk-thread only) ──────────────────────────────────────────────────

def _create(title: str, body: str, on_click, level: str):
    from i18n import t
    import tk_root as tkr

    root   = tkr.get()
    accent = _RED if level == "error" else _GREEN

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=accent)

    inner = tk.Frame(win, bg=_BG, padx=14, pady=10)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    hdr = tk.Frame(inner, bg=_BG)
    hdr.pack(fill="x")
    tk.Label(hdr, text="TXTDrop", bg=_BG, fg=accent,
             font=("Malgun Gothic", 9, "bold")).pack(side="left")
    tk.Label(hdr, text=f"  {title}", bg=_BG, fg=_DIM,
             font=("Malgun Gothic", 9)).pack(side="left")

    tk.Label(inner, text=body, bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), anchor="w", justify="left",
             wraplength=270).pack(fill="x", pady=(6, 0))

    if on_click:
        tk.Label(inner, text=t("toast_hint"), bg=_BG, fg=_DIM,
                 font=("Malgun Gothic", 8)).pack(anchor="w", pady=(4, 0))

    win.update_idletasks()
    w  = max(win.winfo_reqwidth(), 300)
    h  = win.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()

    y_offset = sum(s["h"] + 8 for s in _active)
    x = sw - w - 20
    y = sh - h - 52 - y_offset
    win.geometry(f"{w}x{h}+{x}+{y}")

    slot = {"win": win, "h": h, "x": x, "sh": sh}
    _active.append(slot)

    clicked = [False]

    def dismiss(evt=None):
        if slot in _active:
            _active.remove(slot)
            _restack()
        try:
            win.destroy()
        except tk.TclError:
            pass
        if clicked[0] and on_click:
            threading.Thread(target=on_click, daemon=True).start()

    def on_click_evt(evt):
        clicked[0] = True
        dismiss()

    _bind_recursive(win, on_click_evt)
    win.after(4000, dismiss)


def _restack():
    """Re-anchor remaining toasts after one is dismissed."""
    y_offset = 0
    for slot in reversed(_active):
        try:
            h  = slot["h"]
            x  = slot["x"]
            sh = slot["sh"]
            y  = sh - h - 52 - y_offset
            slot["win"].geometry(f"+{x}+{y}")
            y_offset += h + 8
        except tk.TclError:
            pass


def _bind_recursive(widget, handler):
    widget.bind("<Button-1>", handler)
    for child in widget.winfo_children():
        _bind_recursive(child, handler)
