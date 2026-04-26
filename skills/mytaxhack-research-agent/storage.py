"""
SQLite-backed deduplication store.
Tracks every post we've already seen so we never re-process it.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "seen_posts.db")


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_posts (
                id          TEXT NOT NULL,
                platform    TEXT NOT NULL,
                first_seen  TEXT NOT NULL,
                PRIMARY KEY (id, platform)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyzed_posts (
                id              TEXT NOT NULL,
                platform        TEXT NOT NULL,
                analyzed_at     TEXT NOT NULL,
                relevance_score INTEGER,
                intent_type     TEXT,
                should_contact  INTEGER,
                author          TEXT DEFAULT '',
                PRIMARY KEY (id, platform)
            )
        """)
        # Migrate: add author column to existing DBs
        try:
            conn.execute("ALTER TABLE analyzed_posts ADD COLUMN author TEXT DEFAULT ''")
        except Exception:
            pass  # Column already exists
        conn.commit()


def is_seen(post_id: str, platform: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_posts WHERE id = ? AND platform = ?",
            (post_id, platform),
        ).fetchone()
    return row is not None


def mark_seen(post_id: str, platform: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_posts (id, platform, first_seen) VALUES (?, ?, ?)",
            (post_id, platform, datetime.utcnow().isoformat()),
        )
        conn.commit()


def save_analysis(post_id: str, platform: str, author: str, relevance_score: int,
                  intent_type: str, should_contact: bool) -> None:
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO analyzed_posts
                (id, platform, analyzed_at, relevance_score, intent_type, should_contact, author)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (post_id, platform, datetime.utcnow().isoformat(),
              relevance_score, intent_type, int(should_contact), author or ""))
        conn.commit()


def get_author_platforms(author: str, exclude_platform: str) -> list[str]:
    """Return list of OTHER platforms where this author has previously been analyzed."""
    if not author or author in ("unknown", ""):
        return []
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT platform FROM analyzed_posts WHERE author = ? AND platform != ?",
            (author, exclude_platform),
        ).fetchall()
    return [row[0] for row in rows]


def get_stats() -> dict:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM seen_posts").fetchone()[0]
        analyzed = conn.execute("SELECT COUNT(*) FROM analyzed_posts").fetchone()[0]
        contacts = conn.execute(
            "SELECT COUNT(*) FROM analyzed_posts WHERE should_contact = 1"
        ).fetchone()[0]
    return {"total_seen": total, "total_analyzed": analyzed, "should_contact": contacts}
