"""
tk_root.py — Shared Tkinter root for TXTDrop.

A single hidden tk.Tk() instance is created once and shared by all UI
modules (notify, log_window, settings_window).  Every other window is a
tk.Toplevel so Windows' message queue is never split across threads.

Usage
-----
    import tk_root as tkr
    tkr.init()          # call once in main(), before any UI
    tkr.start()         # starts mainloop in a daemon thread
    tkr.call_on_main(fn, *args)   # schedule work on the Tk thread
    tkr.get()           # returns the root Tk instance
"""
import tkinter as tk
import threading

_root: tk.Tk | None = None


def init() -> tk.Tk:
    """Create the hidden root.  Must be called from the main thread."""
    global _root
    _root = tk.Tk()
    _root.withdraw()
    return _root


def get() -> tk.Tk:
    return _root


def start():
    """Run the Tk event loop in a daemon thread (non-blocking)."""
    threading.Thread(target=_root.mainloop, name="TkMainLoop", daemon=True).start()


def call_on_main(fn, *args):
    """Thread-safe: schedule fn(*args) on the Tk event loop."""
    _root.after(0, fn, *args)
