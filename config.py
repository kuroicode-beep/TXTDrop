import os
import sys
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
        """)


def get(key: str) -> str:
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else DEFAULTS.get(key, "")


def set(key: str, value: str):
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
