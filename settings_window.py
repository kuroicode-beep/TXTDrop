import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
import ollama_client
from i18n import t

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


def open_settings(on_save=None):
    """Open the settings window in a daemon thread."""
    threading.Thread(target=lambda: _run(on_save), daemon=True).start()


# ── Private ───────────────────────────────────────────────────────────────────

def _run(on_save):
    win = tk.Tk()
    win.title(t("settings_title"))
    win.configure(bg=_BG)
    win.resizable(False, False)
    win.attributes("-topmost", True)

    _apply_ttk_theme(win)

    # ── Variables ─────────────────────────────────────────────────────────────
    v_text_folder  = tk.StringVar(value=config.get("text_save_folder"))
    v_image_folder = tk.StringVar(value=config.get("image_save_folder"))
    v_prefix       = tk.StringVar(value=config.get("filename_prefix") or "txtdrop")
    v_hotkey       = tk.StringVar(value=config.get("hotkey") or "ctrl+shift+z")
    v_model        = tk.StringVar(value=config.get("ollama_model") or "llama3")
    v_autostart    = tk.BooleanVar(value=config.get_bool("ollama_autostart"))
    v_sound        = tk.BooleanVar(value=config.get_bool("sound_enabled"))
    v_lang         = tk.StringVar(value=config.get("language") or "ko")

    # ── Scrollable canvas ─────────────────────────────────────────────────────
    outer = tk.Frame(win, bg=_BG)
    outer.pack(fill="both", expand=True)

    # Header
    hdr = tk.Frame(outer, bg=_BG2, pady=14)
    hdr.pack(fill="x")
    tk.Label(hdr, text="TXTDrop", bg=_BG2, fg=_ACCENT,
             font=("Malgun Gothic", 15, "bold")).pack(side="left", padx=20)
    tk.Label(hdr, text=t("settings_title"), bg=_BG2, fg=_DIM,
             font=("Malgun Gothic", 10)).pack(side="left", padx=4)

    # Body
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
    _hotkey_row(body, t("lbl_hotkey"), v_hotkey, win)

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

    models = ollama_client.list_models()
    cb = ttk.Combobox(ai_row, textvariable=v_model,
                      values=models, state="readonly", width=22)
    cb.pack(side="left")

    model_lbl = tk.Label(ai_row, text="", bg=_BG, font=("Malgun Gothic", 9))
    model_lbl.pack(side="left", padx=(8, 0))

    _cached_models: list[str] = list(models)

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
        running   = ollama_client.is_running()
        available = ollama_client.list_models()
        _cached_models.clear()
        _cached_models.extend(available)

        def _apply():
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

        win.after(0, _apply)

    threading.Thread(target=_check_ollama_status, daemon=True).start()
    v_model.trace_add("write", _update_model_status)

    _check(body, t("chk_autostart"), v_autostart)

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
        ok = messagebox.askyesno("TXTDrop", t("restore_confirm"), parent=win)
        if not ok:
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

    # ── Buttons ───────────────────────────────────────────────────────────────
    sep = tk.Frame(outer, bg=_BORDER, height=1)
    sep.pack(fill="x")

    btn_row = tk.Frame(outer, bg=_BG2, pady=12, padx=20)
    btn_row.pack(fill="x")

    def save():
        config.set("text_save_folder",  v_text_folder.get().strip())
        config.set("image_save_folder", v_image_folder.get().strip())
        config.set("filename_prefix",   v_prefix.get().strip() or "txtdrop")
        config.set("hotkey",            v_hotkey.get().strip() or "ctrl+shift+z")
        config.set("ollama_model",      v_model.get())
        config.set_bool("ollama_autostart", v_autostart.get())
        config.set_bool("sound_enabled",    v_sound.get())
        config.set("language",          v_lang.get())
        messagebox.showinfo("TXTDrop", t("saved"), parent=win)
        win.destroy()
        if on_save:
            on_save()

    tk.Button(
        btn_row, text=t("save"), command=save,
        bg=_ACCENT, fg="#000", font=("Malgun Gothic", 10, "bold"),
        relief="flat", bd=0, padx=22, pady=7, cursor="hand2",
    ).pack(side="right", padx=(8, 0))

    tk.Button(
        btn_row, text=t("cancel"), command=win.destroy,
        bg=_BG3, fg=_FG, font=("Malgun Gothic", 10),
        relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
    ).pack(side="right")

    win.update_idletasks()
    w, h = 520, win.winfo_reqheight() + 10
    win.geometry(f"{w}x{h}")
    win.mainloop()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _apply_ttk_theme(win):
    s = ttk.Style(win)
    s.theme_use("clam")
    s.configure("TFrame",    background=_BG)
    s.configure("TLabel",    background=_BG, foreground=_FG,
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


def _input_row(parent, label: str, var: tk.StringVar, width: int = 28):
    row = tk.Frame(parent, bg=_BG)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label, bg=_BG, fg=_FG,
             font=("Malgun Gothic", 10), width=16, anchor="w").pack(side="left")
    tk.Entry(row, textvariable=var, bg=_BG3, fg=_FG,
             insertbackground=_FG, relief="flat", bd=0,
             highlightthickness=1, highlightbackground=_BORDER,
             highlightcolor=_ACCENT, width=width).pack(side="left")


def _hotkey_row(parent, label: str, var: tk.StringVar, win):
    """Hotkey row with keyboard-capture button."""
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

    capturing = {"active": False}
    _saved_value = [var.get()]

    def start_capture():
        capturing["active"]  = True
        _saved_value[0]      = var.get()
        display.config(state="normal")
        var.set(t("hotkey_press"))
        display.config(state="readonly", readonlybackground="#2a2a1a",
                       highlightbackground=_ACCENT)
        btn.config(text=t("cancel"), command=cancel_capture,
                   bg="#3a3a2a", fg=_ACCENT)
        win.bind("<KeyPress>", on_key)
        win.focus_set()

    def cancel_capture():
        capturing["active"] = False
        win.unbind("<KeyPress>")
        display.config(state="normal")
        var.set(_saved_value[0])
        display.config(state="readonly", readonlybackground=_BG3,
                       highlightbackground=_BORDER)
        btn.config(text=t("hotkey_capture"), command=start_capture,
                   bg=_BG3, fg=_FG)

    def on_key(event):
        if not capturing["active"]:
            return
        key = event.keysym.lower()
        # ignore bare modifier presses
        if key in ("control_l", "control_r", "shift_l", "shift_r",
                   "alt_l", "alt_r", "super_l", "super_r", "caps_lock"):
            return
        modifiers = []
        state = event.state
        if state & 0x4:      modifiers.append("ctrl")
        if state & 0x1:      modifiers.append("shift")
        if state & 0x20000:  modifiers.append("alt")
        hotkey = "+".join(modifiers + [key])
        display.config(state="normal")
        var.set(hotkey)
        display.config(state="readonly", readonlybackground=_BG3,
                       highlightbackground=_BORDER)
        capturing["active"] = False
        win.unbind("<KeyPress>")
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
