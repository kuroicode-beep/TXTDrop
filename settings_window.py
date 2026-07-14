"""
settings_window.py — TXTDrop settings UI.

Uses the shared hidden tk.Tk root (tk_root module): window is a
tk.Toplevel, no mainloop() call needed.
"""
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
import ollama_client
from i18n import t
from version import VERSION_LABEL, VERSION_HISTORY

# ── Palette ───────────────────────────────────────────────────────────────────
_BG     = "#111111"
_BG2    = "#1c1c1c"
_BG3    = "#242424"
_FG     = "#f0f0f0"
_DIM    = "#888888"
_ACCENT = "#ffd600"
_BORDER = "#383838"

_MODELS_DEFAULT = ["llama3", "llama3.2", "phi3", "mistral", "gemma3", "qwen2.5"]
_LANGUAGES      = [("한국어", "ko"), ("English", "en")]

# Singleton: prevent multiple settings windows
_win_ref  = [None]
_win_lock = threading.Lock()


def open_settings(on_save=None):
    """Schedule settings window creation on the Tk thread. Safe from any thread."""
    import tk_root as tkr
    with _win_lock:
        if _win_ref[0] is not None:
            tkr.call_on_main(_raise_win)
            return
    tkr.call_on_main(lambda: _run(tkr.get(), on_save))


def _raise_win():
    """Raise existing window, or re-create if it was already destroyed."""
    import tk_root as tkr
    w = _win_ref[0]
    if w:
        try:
            w.lift()
            w.focus_force()
        except tk.TclError:
            with _win_lock:
                _win_ref[0] = None
            tkr.call_on_main(lambda: _run(tkr.get(), None))  # re-open


# ── Private (Tk-thread only) ──────────────────────────────────────────────────

def _run(root, on_save):
    win = tk.Toplevel(root)
    win.title(t("settings_title"))
    win.configure(bg=_BG)
    win.resizable(False, False)
    win.attributes("-topmost", True)

    with _win_lock:
        _win_ref[0] = win

    def on_close():
        with _win_lock:
            _win_ref[0] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    _apply_ttk_theme()

    # ── Variables ─────────────────────────────────────────────────────────────
    v_text_folder  = tk.StringVar(value=config.get("text_save_folder"))
    v_image_folder = tk.StringVar(value=config.get("image_save_folder"))
    v_prefix       = tk.StringVar(value=config.get("filename_prefix") or "txtdrop")
    v_hotkey       = tk.StringVar(value=config.get("hotkey") or "ctrl+shift+z")
    v_tts_hotkey   = tk.StringVar(value=config.get("tts_hotkey") or "ctrl+shift+x")
    v_model        = tk.StringVar(value=config.get("ollama_model") or "llama3")
    v_autostart    = tk.BooleanVar(value=config.get_bool("ollama_autostart"))
    v_sound        = tk.BooleanVar(value=config.get_bool("sound_enabled"))
    v_dedup_auto   = tk.BooleanVar(value=config.get_bool("dedup_auto"))
    v_memory_enabled = tk.BooleanVar(value=config.get_bool("memory_enabled"))
    v_memory_hotkey  = tk.StringVar(value=config.get("memory_hotkey") or "ctrl+shift+m")
    v_memory_token   = tk.StringVar(value=config.get("memory_pairing_token") or "")
    v_lang         = tk.StringVar(value=config.get("language") or "ko")

    # ── Layout ────────────────────────────────────────────────────────────────
    outer = tk.Frame(win, bg=_BG)
    outer.pack(fill="both", expand=True)

    hdr = tk.Frame(outer, bg=_BG2, pady=14)
    hdr.pack(fill="x")
    tk.Label(hdr, text="TXTDrop", bg=_BG2, fg=_ACCENT,
             font=("Malgun Gothic", 15, "bold")).pack(side="left", padx=(20, 4))
    tk.Label(hdr, text=VERSION_LABEL, bg=_BG2, fg=_DIM,
             font=("Malgun Gothic", 10, "bold")).pack(side="left")
    tk.Label(hdr, text=t("settings_title"), bg=_BG2, fg=_DIM,
             font=("Malgun Gothic", 10)).pack(side="left", padx=(10, 0))

    def show_history():
        _show_version_history(win)

    hist_link = tk.Label(hdr, text=t("btn_version_history"), bg=_BG2, fg="#69b4ff",
                         font=("Malgun Gothic", 9, "underline"), cursor="hand2")
    hist_link.pack(side="right", padx=20)
    hist_link.bind("<Button-1>", lambda e: show_history())

    body = tk.Frame(outer, bg=_BG, padx=24, pady=8)
    body.pack(fill="both", expand=True)

    # ── Section: 저장 폴더 ────────────────────────────────────────────────────
    _section(body, t("sec_folders"))
    _folder_row(body, t("lbl_text_folder"),  v_text_folder,  win)
    _folder_row(body, t("lbl_img_folder"),   v_image_folder, win)

    # ── Section: 파일명 ───────────────────────────────────────────────────────
    _section(body, t("sec_filename"))
    _input_row(body, t("lbl_prefix"), v_prefix, width=20)

    # ── Section: 단축키 ───────────────────────────────────────────────────────
    _section(body, t("sec_hotkey"))
    _hotkey_row(body, t("lbl_hotkey"),     v_hotkey,     win)
    _hotkey_row(body, t("lbl_tts_hotkey"), v_tts_hotkey, win)

    # ── Section: AI 기억 (TXTAIMemory 연계) ─────────────────────────────────────
    _section(body, t("sec_memory"))
    _check(body, t("chk_memory_enabled"), v_memory_enabled)
    _hotkey_row(body, t("lbl_memory_hotkey"), v_memory_hotkey, win)
    _input_row(body, t("lbl_memory_token"), v_memory_token, width=36, show="*")
    _hint_label(body, t("hint_memory_token"))

    # ── Section: AI ───────────────────────────────────────────────────────────
    ai_hdr = tk.Frame(body, bg=_BG)
    ai_hdr.pack(fill="x", pady=(12, 2))
    tk.Label(ai_hdr, text=t("sec_ai"), bg=_BG, fg=_ACCENT,
             font=("Malgun Gothic", 10, "bold")).pack(side="left")
    srv_lbl = tk.Label(ai_hdr, text="  ● 확인 중…", bg=_BG, fg=_DIM,
                       font=("Malgun Gothic", 9))
    srv_lbl.pack(side="left", padx=(8, 0))
    tk.Frame(body, bg=_BORDER, height=1).pack(fill="x", pady=(2, 4))

    ai_row = tk.Frame(body, bg=_BG)
    ai_row.pack(fill="x", pady=3)
    tk.Label(ai_row, text=t("lbl_model"), bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), width=16, anchor="w").pack(side="left")
    cb = ttk.Combobox(ai_row, textvariable=v_model,
                      values=[], state="readonly", width=22)
    cb.pack(side="left")
    model_lbl = tk.Label(ai_row, text="", bg=_BG, font=("Malgun Gothic", 9))
    model_lbl.pack(side="left", padx=(8, 0))

    _cached_models: list[str] = []

    def _update_model_status(*_):
        selected = v_model.get()
        resolved = ollama_client.resolve_model(selected)
        if resolved in _cached_models:
            model_lbl.config(text="✓ 정상작동", fg="#81c995")
        elif _cached_models:
            model_lbl.config(text=f"→ {resolved} 사용", fg=_ACCENT)
        else:
            model_lbl.config(text="모델 없음", fg="#f28b82")

    def _check_ollama_status():
        # Always do a fresh check inside settings — cached value may be stale
        running   = ollama_client.is_running()
        available = ollama_client.list_models() if running else []
        _cached_models.clear()
        if available:
            _cached_models.extend(available)

        # Also update the shared cache so rest of app sees the fresh value
        import time as _time
        with ollama_client._cache_lock:
            ollama_client._cached_running = running
            ollama_client._cache_time     = _time.monotonic()

        def _apply():
            try:
                if running:
                    srv_lbl.config(text="  ● 실행 중", fg="#81c995")
                    cb.config(values=available)
                    cur      = v_model.get()
                    resolved = ollama_client.resolve_model(cur)
                    if cur not in available and resolved in available:
                        v_model.set(resolved)
                else:
                    srv_lbl.config(text="  ● 오프라인", fg="#f28b82")
                _update_model_status()
            except tk.TclError:
                pass  # window closed while checking

        win.after(0, _apply)

    threading.Thread(target=_check_ollama_status, daemon=True).start()
    v_model.trace_add("write", _update_model_status)

    _check(body, t("chk_autostart"), v_autostart)

    # ── Section: 중복제거 ─────────────────────────────────────────────────────
    _section(body, t("sec_dedup"))
    _check(body, t("chk_dedup_auto"), v_dedup_auto)

    # ── Section: 사운드 ───────────────────────────────────────────────────────
    _section(body, t("sec_sound"))
    _check(body, t("chk_sound"), v_sound)

    # ── Section: 언어 ─────────────────────────────────────────────────────────
    _section(body, t("sec_language"))
    lang_row = tk.Frame(body, bg=_BG)
    lang_row.pack(fill="x", pady=4)
    for label, val in _LANGUAGES:
        tk.Radiobutton(
            lang_row, text=label, variable=v_lang, value=val,
            bg=_BG, fg=_FG, selectcolor=_BG3,
            activebackground=_BG, activeforeground=_FG,
            font=("Malgun Gothic", 10),
        ).pack(side="left", padx=(0, 18))

    # ── Section: 데이터베이스 ─────────────────────────────────────────────────
    _section(body, t("sec_database"))
    db_row = tk.Frame(body, bg=_BG)
    db_row.pack(fill="x", pady=6)

    def do_backup():
        folder = filedialog.askdirectory(title=t("select_folder"), parent=win)
        if not folder:
            return
        try:
            path = config.backup_db(folder)
            messagebox.showinfo("TXTDrop", t("backup_success", path=path), parent=win)
        except Exception as e:
            messagebox.showerror("TXTDrop", t("backup_fail", err=e), parent=win)

    def do_restore():
        src = filedialog.askopenfilename(
            title="TXTDrop — " + t("btn_restore"),
            filetypes=[("TXTDrop Database", "*.db"), ("All files", "*.*")],
            parent=win,
        )
        if not src:
            return
        if not messagebox.askyesno("TXTDrop", t("restore_confirm"), parent=win):
            return
        try:
            config.restore_db(src)
            messagebox.showinfo("TXTDrop", t("restore_success"), parent=win)
        except Exception as e:
            messagebox.showerror("TXTDrop", t("restore_fail", err=e), parent=win)

    tk.Button(db_row, text=t("btn_backup"), command=do_backup,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 10),
              relief="flat", bd=0, padx=16, pady=6,
              cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(db_row, text=t("btn_restore"), command=do_restore,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 10),
              relief="flat", bd=0, padx=16, pady=6,
              cursor="hand2").pack(side="left")

    # ── Save / Cancel ─────────────────────────────────────────────────────────
    tk.Frame(outer, bg=_BORDER, height=1).pack(fill="x")
    btn_row = tk.Frame(outer, bg=_BG2, pady=12, padx=20)
    btn_row.pack(fill="x")

    def save():
        lang_changed = v_lang.get() != config.get("language")

        config.set("text_save_folder",  v_text_folder.get().strip())
        config.set("image_save_folder", v_image_folder.get().strip())
        config.set("filename_prefix",   v_prefix.get().strip() or "txtdrop")
        config.set("hotkey",            v_hotkey.get().strip() or "ctrl+shift+z")
        config.set("tts_hotkey",        v_tts_hotkey.get().strip() or "ctrl+shift+x")
        config.set("ollama_model",      v_model.get())
        config.set_bool("ollama_autostart", v_autostart.get())
        config.set_bool("sound_enabled",    v_sound.get())
        config.set_bool("dedup_auto",       v_dedup_auto.get())
        config.set_bool("memory_enabled",   v_memory_enabled.get())
        config.set("memory_hotkey",         v_memory_hotkey.get().strip() or "ctrl+shift+m")
        config.set("memory_pairing_token",  v_memory_token.get().strip())
        config.set("language",          v_lang.get())

        msg = t("saved")
        if lang_changed:
            msg += "\n\n" + t("lang_restart_notice")
        messagebox.showinfo("TXTDrop", msg, parent=win)

        with _win_lock:
            _win_ref[0] = None
        win.destroy()
        if on_save:
            on_save()

    tk.Button(
        btn_row, text=t("save"), command=save,
        bg=_ACCENT, fg="#000", font=("Malgun Gothic", 10, "bold"),
        relief="flat", bd=0, padx=22, pady=7, cursor="hand2",
    ).pack(side="right", padx=(8, 0))

    tk.Button(
        btn_row, text=t("cancel"), command=on_close,
        bg=_BG3, fg=_FG, font=("Malgun Gothic", 10),
        relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
    ).pack(side="right")

    win.update_idletasks()
    win.geometry(f"520x{win.winfo_reqheight() + 10}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _apply_ttk_theme():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("TFrame",       background=_BG)
    s.configure("TLabel",       background=_BG, foreground=_FG,
                font=("Malgun Gothic", 10))
    s.configure("TCheckbutton", background=_BG, foreground=_FG,
                font=("Malgun Gothic", 10))
    s.map("TCheckbutton",
          background=[("active", _BG)],
          foreground=[("active", _FG)])
    s.configure("TCombobox",
                fieldbackground=_BG3, foreground=_FG,
                selectbackground=_BG3, selectforeground=_FG)
    s.map("TCombobox",
          fieldbackground=[("readonly", _BG3)],
          foreground=[("readonly", _FG)])


def _section(parent, text: str):
    f = tk.Frame(parent, bg=_BG)
    f.pack(fill="x", pady=(12, 2))
    tk.Label(f, text=text, bg=_BG, fg=_ACCENT,
             font=("Malgun Gothic", 10, "bold")).pack(anchor="w")
    tk.Frame(f, bg=_BORDER, height=1).pack(fill="x", pady=(2, 0))


def _folder_row(parent, label: str, var: tk.StringVar, win):
    row = tk.Frame(parent, bg=_BG)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label, bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), width=16, anchor="w").pack(side="left")
    e = tk.Entry(row, textvariable=var, bg=_BG3, fg=_FG,
                 insertbackground=_FG, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=_BORDER,
                 highlightcolor=_ACCENT, width=28)
    e.pack(side="left", padx=(0, 6))

    def browse():
        folder = filedialog.askdirectory(title=t("select_folder"), parent=win)
        if folder:
            var.set(folder)

    tk.Button(row, text=t("browse"), command=browse,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=10, pady=4,
              cursor="hand2").pack(side="left")


def _input_row(parent, label: str, var: tk.StringVar, width: int = 28, show: str | None = None):
    row = tk.Frame(parent, bg=_BG)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label, bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), width=16, anchor="w").pack(side="left")
    entry = tk.Entry(row, textvariable=var, bg=_BG3, fg=_FG,
             insertbackground=_FG, relief="flat", bd=0,
             highlightthickness=1, highlightbackground=_BORDER,
             highlightcolor=_ACCENT, width=width)
    if show:
        entry.config(show=show)
    entry.pack(side="left")


def _hint_label(parent, text: str):
    """작은 회색 보조 설명 텍스트(입력 필드 아래 용도)."""
    tk.Label(parent, text=text, bg=_BG, fg=_DIM,
             font=("Malgun Gothic", 9), wraplength=440, justify="left",
             anchor="w").pack(fill="x", pady=(0, 4))


def _hotkey_row(parent, label: str, var: tk.StringVar, win):
    """Hotkey entry with keyboard-capture and modifier-key validation."""
    row = tk.Frame(parent, bg=_BG)
    row.pack(fill="x", pady=3)

    tk.Label(row, text=label, bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), width=16, anchor="w").pack(side="left")

    display = tk.Entry(
        row, textvariable=var,
        bg=_BG3, fg=_FG, insertbackground=_FG,
        relief="flat", bd=0,
        highlightthickness=1, highlightbackground=_BORDER,
        highlightcolor=_ACCENT, width=22,
        state="readonly", readonlybackground=_BG3,
    )
    display.pack(side="left", padx=(0, 8))

    capturing  = {"active": False}
    saved_val  = [var.get()]

    def _set_display(text, bg=_BG3, border=_BORDER):
        display.config(state="normal")
        var.set(text)
        display.config(state="readonly", readonlybackground=bg,
                       highlightbackground=border)

    def start_capture():
        capturing["active"] = True
        saved_val[0] = var.get()
        _set_display(t("hotkey_press"), bg="#2a2a1a", border=_ACCENT)
        btn.config(text=t("cancel"), command=cancel_capture,
                   bg="#3a3a2a", fg=_ACCENT)
        win.bind("<KeyPress>", on_key)
        win.focus_set()

    def cancel_capture():
        capturing["active"] = False
        win.unbind("<KeyPress>")
        _set_display(saved_val[0])
        btn.config(text=t("hotkey_capture"), command=start_capture,
                   bg=_BG3, fg=_FG)

    def _show_modifier_warning():
        _set_display(t("hotkey_modifier_required"), bg="#3a1a1a", border="#f28b82")
        win.after(2000, lambda: _set_display(t("hotkey_press"),
                                             bg="#2a2a1a", border=_ACCENT))

    def on_key(event):
        if not capturing["active"]:
            return
        key = event.keysym.lower()
        if key in ("control_l", "control_r", "shift_l", "shift_r",
                   "alt_l", "alt_r", "super_l", "super_r", "caps_lock"):
            return  # ignore bare modifier press

        modifiers = []
        state = event.state
        if state & 0x4:      modifiers.append("ctrl")
        if state & 0x1:      modifiers.append("shift")
        if state & 0x20000:  modifiers.append("alt")

        if not modifiers:
            # Require at least one modifier
            _show_modifier_warning()
            return

        hotkey = "+".join(modifiers + [key])
        capturing["active"] = False
        win.unbind("<KeyPress>")
        _set_display(hotkey)
        btn.config(text=t("hotkey_capture"), command=start_capture,
                   bg=_BG3, fg=_FG)

    btn = tk.Button(
        row, text=t("hotkey_capture"), command=start_capture,
        bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
        relief="flat", bd=0, padx=12, pady=4, cursor="hand2",
    )
    btn.pack(side="left")


def _check(parent, text: str, var: tk.BooleanVar):
    ttk.Checkbutton(parent, text=text, variable=var).pack(anchor="w", pady=3)


def _show_version_history(parent):
    """버전별 변경 요약을 최신순으로 보여주는 대화상자 (SVIL 앱 버전 규칙)."""
    win = tk.Toplevel(parent)
    win.title(t("version_history_title"))
    win.configure(bg=_BG)
    win.resizable(False, False)
    win.attributes("-topmost", True)

    tk.Label(win, text=t("version_history_title"), bg=_BG, fg=_ACCENT,
             font=("Malgun Gothic", 12, "bold")).pack(anchor="w", padx=20, pady=(16, 8))

    body = tk.Frame(win, bg=_BG, padx=20)
    body.pack(fill="both", expand=True)

    for ver, date, summary in VERSION_HISTORY:
        row = tk.Frame(body, bg=_BG)
        row.pack(fill="x", pady=4, anchor="w")
        tk.Label(row, text=f"v{ver}", bg=_BG, fg=_ACCENT,
                 font=("Malgun Gothic", 10, "bold"), width=8, anchor="w").pack(side="left")
        tk.Label(row, text=date, bg=_BG, fg=_DIM,
                 font=("Malgun Gothic", 9), width=11, anchor="w").pack(side="left")
        tk.Label(row, text=summary, bg=_BG, fg=_FG, font=("Malgun Gothic", 9),
                 anchor="w", justify="left", wraplength=360).pack(side="left", fill="x")

    tk.Button(win, text=t("close"), command=win.destroy,
              bg=_BG3, fg=_FG, font=("Malgun Gothic", 9),
              relief="flat", bd=0, padx=16, pady=6,
              cursor="hand2").pack(pady=16)
