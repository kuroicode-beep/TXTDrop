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
    "tts_hotkey":        "ctrl+shift+x",
    "language":          "ko",
    "ollama_model":      "llama3.2",
    "dedup_auto":        "true",
    "dedup_threshold":   "90",
    "memory_enabled":    "false",
    "memory_hotkey":     "ctrl+shift+m",
    "memory_char_limit": "8000",
    # TTS 낭독 설정 (SVIL TTS 설정 표준) — 빈 값/auto는 서버 기본을 따른다
    "tts_engine":        "auto",
    "tts_voice":         "",
    "tts_speed":         "1.0",
    "tts_use_rvc":       "1",     # 서버 pipeline 기본이 RVC ON이므로 기존 동작 보존
    "tts_rvc_model":     "",      # '' = 자동 (서버가 보이스에 맞춰 선택)
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
            CREATE TABLE IF NOT EXISTS trash (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                saved_at   TEXT NOT NULL,
                type       TEXT NOT NULL,
                filename   TEXT NOT NULL,
                filepath   TEXT NOT NULL,
                trashed_at TEXT NOT NULL,
                reason     TEXT NOT NULL
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


def history_add(type_: str, filename: str, filepath: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO history (saved_at, type, filename, filepath) "
            "VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), type_, filename, filepath),
        )
        return cur.lastrowid


def history_rows(type_: str | None = None, limit: int = 5000) -> list[dict]:
    """id 포함 저장 기록 조회 (중복 검사용, 오래된 순)."""
    q, args = "SELECT id, saved_at, type, filename, filepath FROM history", []
    if type_:
        q += " WHERE type = ?"
        args.append(type_)
    q += " ORDER BY id ASC LIMIT ?"
    args.append(limit)
    with _connect() as conn:
        rows = conn.execute(q, args).fetchall()
    return [
        {"id": r[0], "saved_at": r[1], "type": r[2],
         "filename": r[3], "filepath": r[4]}
        for r in rows
    ]


# ── Trash (중복 문서 격리 — row 이동, 파일은 건드리지 않음) ────────────────────

def history_move_to_trash(hist_id: int, reason: str) -> bool:
    """history row를 trash 테이블로 이동. 성공 시 True."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT saved_at, type, filename, filepath FROM history WHERE id = ?",
            (hist_id,),
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "INSERT INTO trash (saved_at, type, filename, filepath, trashed_at, reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (*row, datetime.datetime.now().isoformat(), reason),
        )
        conn.execute("DELETE FROM history WHERE id = ?", (hist_id,))
        return True


def trash_get(limit: int = 500) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, saved_at, type, filename, filepath, trashed_at, reason "
            "FROM trash ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"id": r[0], "saved_at": r[1], "type": r[2], "filename": r[3],
         "filepath": r[4], "trashed_at": r[5], "reason": r[6]}
        for r in rows
    ]


def trash_restore(trash_id: int) -> bool:
    """trash row를 history로 되돌린다. 성공 시 True."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT saved_at, type, filename, filepath FROM trash WHERE id = ?",
            (trash_id,),
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "INSERT INTO history (saved_at, type, filename, filepath) "
            "VALUES (?, ?, ?, ?)",
            row,
        )
        conn.execute("DELETE FROM trash WHERE id = ?", (trash_id,))
        return True


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
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
        src.close()
    return dest


def restore_db(src_path: str):
    """Overwrite live DB with a backup file."""
    src = sqlite3.connect(src_path)
    dst = _connect()
    try:
        with dst:
            src.backup(dst)
    finally:
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
