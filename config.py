import os
import sys
import random
import sqlite3
import datetime

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "txtdrop.db")

DEFAULTS = {
    "text_save_folder":  "",
    "image_save_folder": "",
    "filename_prefix":   "txtdrop",
    "sound_enabled":     "true",
    "hotkey":            "ctrl+shift+z",
    "language":          "ko",
    "ollama_model":      "llama3.2",
    "ollama_autostart":  "true",
}

# In-memory cache — avoids repeated DB opens for read-heavy hot path
_cache: dict[str, str] = {}


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_FILE)


def init_db():
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                saved_at  TEXT NOT NULL,
                type      TEXT NOT NULL,
                filename  TEXT NOT NULL,
                filepath  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                logged_at  TEXT NOT NULL,
                level      TEXT NOT NULL,
                category   TEXT NOT NULL,
                message    TEXT NOT NULL
            );
        """)
        # Purge logs older than 30 days on startup
        conn.execute(
            "DELETE FROM log WHERE logged_at < datetime('now', '-30 days')"
        )
        # Pre-load entire config table into memory cache
        rows = conn.execute("SELECT key, value FROM config").fetchall()
        for k, v in rows:
            _cache[k] = v


def get(key: str) -> str:
    if key in _cache:
        return _cache[key]
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
    value = row[0] if row else DEFAULTS.get(key, "")
    _cache[key] = value
    return value


def set(key: str, value: str):
    _cache[key] = value
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_bool(key: str) -> bool:
    return get(key).lower() in ("true", "1", "yes")


def set_bool(key: str, value: bool):
    set(key, "true" if value else "false")


def history_add(type_: str, filename: str, filepath: str):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO history (saved_at, type, filename, filepath) "
            "VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), type_, filename, filepath),
        )


# ── Log ───────────────────────────────────────────────────────────────────────

def log_add(level: str, category: str, message: str):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO log (logged_at, level, category, message) VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), level, category, message),
        )
        # 1 % chance: purge logs older than 30 days (keeps table lean)
        if random.random() < 0.01:
            conn.execute(
                "DELETE FROM log WHERE logged_at < datetime('now', '-30 days')"
            )


def log_count() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM log").fetchone()[0]


def log_last_id() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT MAX(id) FROM log").fetchone()
        return row[0] or 0


def log_get(limit: int = 500) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT logged_at, level, category, message FROM log "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"time": r[0], "level": r[1], "category": r[2], "message": r[3]} for r in rows]


def log_clear():
    with _connect() as conn:
        conn.execute("DELETE FROM log")


# ── DB Backup / Restore ───────────────────────────────────────────────────────

def backup_db(dest_folder: str) -> str:
    """Copy live DB to dest_folder. Returns the backup file path."""
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(dest_folder, f"txtdrop_backup_{ts}.db")
    src  = _connect()
    dst  = sqlite3.connect(dest)
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
    return dest


def restore_db(src_path: str):
    """Overwrite live DB with a backup file."""
    src = sqlite3.connect(src_path)
    dst = _connect()
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    _cache.clear()


def history_get(limit: int = 500) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT saved_at, type, filename, filepath FROM history "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"time": r[0], "type": r[1], "filename": r[2], "filepath": r[3]}
        for r in rows
    ]
