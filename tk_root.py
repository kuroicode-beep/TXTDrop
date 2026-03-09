"""
tk_root.py — Shared Tkinter root for TXTDrop.

A single hidden tk.Tk() instance is created once and shared by all UI
modules (notify, log_window, settings_window).  Every other window is a
tk.Toplevel so Windows' message queue is never split across threads.

IMPORTANT: Tkinter mainloop() MUST run on the OS main thread.
Call tkr.init() early, then run tray.run_detached() for pystray, and
finally call tkr.get().mainloop() on the main thread.

Usage
-----
    import tk_root as tkr
    tkr.init()                    # call once in main(), before any UI
    tkr.call_on_main(fn, *args)   # schedule work on the Tk thread
    tkr.get()                     # returns the root Tk instance
    tkr.get().mainloop()          # block main thread in Tk event loop
"""
import tkinter as tk

_root: tk.Tk | None = None


def init() -> tk.Tk:
    """Create the hidden root.  Must be called from the main thread."""
    global _root
    _root = tk.Tk()
    _root.withdraw()
    return _root


def get() -> tk.Tk:
    return _root


def call_on_main(fn, *args):
    """Thread-safe: schedule fn(*args) on the Tk event loop."""
    _root.after(0, fn, *args)
