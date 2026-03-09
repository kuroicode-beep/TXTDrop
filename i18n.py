import config

_STRINGS: dict[str, dict[str, str]] = {
    "ko": {
        # tray
        "settings":           "환경설정",
        "log_history":        "로그 기록",
        "exit":               "종료",
        # settings window
        "settings_title":     "TXTDrop 환경설정",
        "save":               "저장",
        "cancel":             "취소",
        "saved":              "설정이 저장되었습니다.",
        "browse":             "찾기",
        "select_folder":      "폴더 선택",
        # first run
        "first_run_title":    "TXTDrop 첫 실행",
        "first_run_msg":      "텍스트 파일을 저장할 폴더를 선택해주세요.",
        # db
        "backup_success":     "백업 완료:\n{path}",
        "backup_fail":        "백업 실패:\n{err}",
        "restore_confirm":    "선택한 백업으로 복원하시겠습니까?\n현재 데이터가 덮어씌워집니다.",
        "restore_success":    "복원 완료. 앱을 재시작하면 반영됩니다.",
        "restore_fail":       "복원 실패:\n{err}",
        # ollama
        "ollama_prompt":      "Ollama 서버가 실행되지 않았습니다.\n실행할까요?",
        # settings sections
        "sec_folders":        "저장 폴더",
        "sec_filename":       "파일명",
        "sec_hotkey":         "단축키",
        "sec_ai":             "AI (Ollama)",
        "sec_sound":          "사운드",
        "sec_language":       "언어",
        "sec_database":       "데이터베이스",
        # settings labels
        "lbl_text_folder":    "텍스트 저장 폴더",
        "lbl_img_folder":     "이미지 저장 폴더",
        "lbl_prefix":         "파일명 접두사",
        "lbl_hotkey":         "단축키",
        "lbl_model":          "Ollama 모델",
        "lbl_language":       "언어",
        # settings checks / buttons
        "chk_autostart":      "TXTDrop 실행 시 Ollama 자동 시작",
        "chk_sound":          "저장 성공 시 효과음 재생",
        "btn_backup":         "DB 백업",
        "btn_restore":        "DB 복원",
        "hotkey_capture":     "변경",
        "hotkey_press":       "키를 누르세요…",
        # toast
        "toast_ok":           "저장 완료",
        "toast_fail":         "저장 실패",
        "toast_hint":         "클릭하면 로그 기록을 봅니다",
        # save errors
        "save_fail_folder":   "저장 폴더가 설정되지 않았습니다.",
        "save_fail_empty":    "클립보드가 비어 있습니다.",
        # log window
        "log_title":          "TXTDrop — 로그 기록",
        "log_clear":          "로그 지우기",
        "log_refresh":        "새로고침",
        "log_empty":          "로그 기록이 없습니다.",
    },
    "en": {
        # tray
        "settings":           "Settings",
        "log_history":        "Log History",
        "exit":               "Exit",
        # settings window
        "settings_title":     "TXTDrop Settings",
        "save":               "Save",
        "cancel":             "Cancel",
        "saved":              "Settings saved.",
        "browse":             "Browse",
        "select_folder":      "Select Folder",
        # first run
        "first_run_title":    "TXTDrop Setup",
        "first_run_msg":      "Please select a folder to save text files.",
        # db
        "backup_success":     "Backup saved:\n{path}",
        "backup_fail":        "Backup failed:\n{err}",
        "restore_confirm":    "Restore from selected backup?\nCurrent data will be overwritten.",
        "restore_success":    "Restore complete. Restart the app to apply.",
        "restore_fail":       "Restore failed:\n{err}",
        # ollama
        "ollama_prompt":      "Ollama server is not running.\nStart it now?",
        # settings sections
        "sec_folders":        "Save Folders",
        "sec_filename":       "Filename",
        "sec_hotkey":         "Hotkey",
        "sec_ai":             "AI (Ollama)",
        "sec_sound":          "Sound",
        "sec_language":       "Language",
        "sec_database":       "Database",
        # settings labels
        "lbl_text_folder":    "Text Save Folder",
        "lbl_img_folder":     "Image Save Folder",
        "lbl_prefix":         "Filename Prefix",
        "lbl_hotkey":         "Hotkey",
        "lbl_model":          "Ollama Model",
        "lbl_language":       "Language",
        # settings checks / buttons
        "chk_autostart":      "Auto-start Ollama on launch",
        "chk_sound":          "Play sound effect on save",
        "btn_backup":         "Backup DB",
        "btn_restore":        "Restore DB",
        "hotkey_capture":     "Change",
        "hotkey_press":       "Press a key…",
        # toast
        "toast_ok":           "Saved",
        "toast_fail":         "Save Failed",
        "toast_hint":         "Click to view log history",
        # save errors
        "save_fail_folder":   "Save folder is not configured.",
        "save_fail_empty":    "Clipboard is empty.",
        # log window
        "log_title":          "TXTDrop — Log History",
        "log_clear":          "Clear Logs",
        "log_refresh":        "Refresh",
        "log_empty":          "No log entries.",
    },
}


def t(key: str, **kwargs) -> str:
    lang = config.get("language") or "ko"
    s = _STRINGS.get(lang, _STRINGS["ko"]).get(key, key)
    if kwargs:
        try:
            s = s.format(**kwargs)
        except Exception:
            pass
    return s
