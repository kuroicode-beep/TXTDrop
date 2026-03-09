import config

_STRINGS: dict[str, dict[str, str]] = {
    "ko": {
        "settings":         "환경설정",
        "exit":             "종료",
        "backup_db":        "DB 백업",
        "restore_db":       "DB 복원",
        "settings_title":   "TXTDrop 환경설정",
        "save":             "저장",
        "cancel":           "취소",
        "saved":            "설정이 저장되었습니다.",
        "browse":           "찾기",
        "select_folder":    "폴더 선택",
        "first_run_title":  "TXTDrop 첫 실행",
        "first_run_msg":    "텍스트 파일을 저장할 폴더를 선택해주세요.",
        "backup_success":   "백업 완료:\n{path}",
        "backup_fail":      "백업 실패:\n{err}",
        "restore_confirm":  "선택한 백업으로 복원하시겠습니까?\n현재 데이터가 덮어씌워집니다.",
        "restore_success":  "복원 완료. 앱을 재시작하면 반영됩니다.",
        "restore_fail":     "복원 실패:\n{err}",
        "ollama_prompt":    "Ollama 서버가 실행되지 않았습니다.\n실행할까요?",
        "sec_folders":      "저장 폴더",
        "sec_filename":     "파일명",
        "sec_hotkey":       "단축키",
        "sec_ai":           "AI (Ollama)",
        "sec_sound":        "사운드",
        "sec_language":     "언어",
        "lbl_text_folder":  "텍스트 저장 폴더",
        "lbl_img_folder":   "이미지 저장 폴더",
        "lbl_prefix":       "파일명 접두사",
        "lbl_hotkey":       "단축키",
        "lbl_model":        "Ollama 모델",
        "chk_autostart":    "TXTDrop 실행 시 Ollama 자동 시작",
        "chk_sound":        "저장 성공 시 효과음 재생",
        "lbl_language":     "언어",
    },
    "en": {
        "settings":         "Settings",
        "exit":             "Exit",
        "backup_db":        "Backup DB",
        "restore_db":       "Restore DB",
        "settings_title":   "TXTDrop Settings",
        "save":             "Save",
        "cancel":           "Cancel",
        "saved":            "Settings saved.",
        "browse":           "Browse",
        "select_folder":    "Select Folder",
        "first_run_title":  "TXTDrop Setup",
        "first_run_msg":    "Please select a folder to save text files.",
        "backup_success":   "Backup saved:\n{path}",
        "backup_fail":      "Backup failed:\n{err}",
        "restore_confirm":  "Restore from selected backup?\nCurrent data will be overwritten.",
        "restore_success":  "Restore complete. Restart the app to apply.",
        "restore_fail":     "Restore failed:\n{err}",
        "ollama_prompt":    "Ollama server is not running.\nStart it now?",
        "sec_folders":      "Save Folders",
        "sec_filename":     "Filename",
        "sec_hotkey":       "Hotkey",
        "sec_ai":           "AI (Ollama)",
        "sec_sound":        "Sound",
        "sec_language":     "Language",
        "lbl_text_folder":  "Text Save Folder",
        "lbl_img_folder":   "Image Save Folder",
        "lbl_prefix":       "Filename Prefix",
        "lbl_hotkey":       "Hotkey",
        "lbl_model":        "Ollama Model",
        "chk_autostart":    "Auto-start Ollama on launch",
        "chk_sound":        "Play sound effect on save",
        "lbl_language":     "Language",
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
