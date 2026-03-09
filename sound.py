import threading
import winsound


def play_drop():
    """Play a short two-tone drop sound in a daemon thread."""
    threading.Thread(target=_beep, daemon=True).start()


def _beep():
    try:
        winsound.Beep(1200, 55)
        winsound.Beep(880,  85)
    except Exception:
        pass
