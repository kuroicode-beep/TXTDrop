import threading
import winsound


def play_drop():
    """Play a short two-tone drop sound in a daemon thread."""
    threading.Thread(target=_beep, daemon=True).start()


def _beep():
    import config
    try:
        winsound.Beep(1200, 120)
        winsound.Beep(880,  180)
    except Exception as e:
        try:
            # Fallback: Windows system sound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
        config.log_add("WARN", "sound", f"Beep 실패: {e}")
