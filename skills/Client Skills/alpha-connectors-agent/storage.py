"""
SQLite-backed deduplication store. Tracks seen post IDs so we never analyze the same signal twice.
"""

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "seen_signals.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_signals (
            id TEXT PRIMARY KEY,
            url TEXT,
            platform TEXT,
            seen_at TEXT
        )
    """)
    conn.commit()
    return conn


def make_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def is_seen(signal_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_signals WHERE id = ?", (signal_id,)
        ).fetchone()
        return row is not None


def mark_seen(signal_id: str, url: str, platform: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_signals (id, url, platform, seen_at) VALUES (?, ?, ?, ?)",
            (signal_id, url, platform, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def count_seen() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM seen_signals").fetchone()[0]
