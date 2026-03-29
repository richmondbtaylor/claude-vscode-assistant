"""
Engagement Tracker — SQLite storage for all engagement history.

Tables:
  - comments      : record of every comment left (with timestamp)
  - follows       : record of every follow (with follow-back status + timestamp)
  - likes         : record of every like (with timestamp)
  - rate_counters : rolling hourly and daily action counts per account
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from config import DB_PATH, RATE_LIMITS_HOURLY, RATE_LIMITS_DAILY, FOLLOW_BACK_WAIT_DAYS, UNFOLLOW_WHITELIST

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist, and run any needed migrations."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS comments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                account     TEXT NOT NULL,
                target_user TEXT NOT NULL,
                post_url    TEXT NOT NULL,
                comment     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS follows (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                account         TEXT NOT NULL,
                target_user     TEXT NOT NULL,
                followed_at     TEXT NOT NULL,
                followed_back   INTEGER DEFAULT 0,
                checked_at      TEXT,
                unfollowed_at   TEXT,
                last_engaged_at TEXT
            );

            CREATE TABLE IF NOT EXISTS likes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                account     TEXT NOT NULL,
                target_user TEXT NOT NULL,
                post_url    TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rate_counters (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                account     TEXT NOT NULL,
                action      TEXT NOT NULL,
                window      TEXT NOT NULL,
                window_start TEXT NOT NULL,
                count       INTEGER DEFAULT 0,
                UNIQUE(account, action, window, window_start)
            );

            CREATE TABLE IF NOT EXISTS account_meta (
                account         TEXT PRIMARY KEY,
                start_date      TEXT NOT NULL,
                limit_multiplier REAL DEFAULT 1.0
            );
        """)
        # Migration: add last_engaged_at to existing follows tables
        try:
            conn.execute("ALTER TABLE follows ADD COLUMN last_engaged_at TEXT")
        except Exception:
            pass  # column already exists


# ---------------------------------------------------------------------------
# Comment tracking
# ---------------------------------------------------------------------------

def record_comment(account: str, target_user: str, post_url: str, comment: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO comments (account, target_user, post_url, comment, created_at) VALUES (?,?,?,?,?)",
            (account, target_user, post_url, comment, datetime.utcnow().isoformat())
        )


def commented_recently(account: str, target_user: str, cooldown_days: int) -> bool:
    """Return True if we've already commented on this target's post within the cooldown window."""
    cutoff = (datetime.utcnow() - timedelta(days=cooldown_days)).isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM comments WHERE account=? AND target_user=? AND created_at >= ? LIMIT 1",
            (account, target_user, cutoff)
        ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Follow / unfollow tracking
# ---------------------------------------------------------------------------

def record_follow(account: str, target_user: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO follows (account, target_user, followed_at) VALUES (?,?,?)",
            (account, target_user, datetime.utcnow().isoformat())
        )


def record_unfollow(account: str, target_user: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE follows SET unfollowed_at=? WHERE account=? AND target_user=? AND unfollowed_at IS NULL",
            (datetime.utcnow().isoformat(), account, target_user)
        )


def mark_followed_back(account: str, target_user: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE follows SET followed_back=1, checked_at=? WHERE account=? AND target_user=? AND unfollowed_at IS NULL",
            (datetime.utcnow().isoformat(), account, target_user)
        )


def get_unfollow_candidates(account: str) -> list[str]:
    """Return usernames that followed_at > FOLLOW_BACK_WAIT_DAYS ago, no follow-back, not unfollowed, not on whitelist."""
    cutoff = (datetime.utcnow() - timedelta(days=FOLLOW_BACK_WAIT_DAYS)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT target_user FROM follows
               WHERE account=? AND followed_back=0 AND unfollowed_at IS NULL AND followed_at <= ?""",
            (account, cutoff)
        ).fetchall()
    candidates = [r["target_user"] for r in rows]
    return [u for u in candidates if u.lower() not in UNFOLLOW_WHITELIST]


def already_following(account: str, target_user: str) -> bool:
    """Return True if we currently follow this account (followed but not unfollowed)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM follows WHERE account=? AND target_user=? AND unfollowed_at IS NULL LIMIT 1",
            (account, target_user)
        ).fetchone()
    return row is not None


def update_last_engaged(account: str, target_user: str):
    """Update last_engaged_at timestamp for a currently-followed account."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE follows SET last_engaged_at=? WHERE account=? AND target_user=? AND unfollowed_at IS NULL",
            (datetime.utcnow().isoformat(), account, target_user)
        )


def get_reengage_candidates(account: str, cadence_days: int = 3) -> list[str]:
    """Return usernames of followed accounts due for re-engagement.

    An account is due if last_engaged_at is NULL (never engaged since follow)
    or last_engaged_at < (now - cadence_days).
    """
    cutoff = (datetime.utcnow() - timedelta(days=cadence_days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT target_user FROM follows
               WHERE account=? AND unfollowed_at IS NULL
               AND (last_engaged_at IS NULL OR last_engaged_at <= ?)
               ORDER BY last_engaged_at ASC""",
            (account, cutoff)
        ).fetchall()
    return [r["target_user"] for r in rows]


# ---------------------------------------------------------------------------
# Like tracking
# ---------------------------------------------------------------------------

def record_like(account: str, target_user: str, post_url: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO likes (account, target_user, post_url, created_at) VALUES (?,?,?,?)",
            (account, target_user, post_url, datetime.utcnow().isoformat())
        )


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _window_start(window: str) -> str:
    now = datetime.utcnow()
    if window == "hourly":
        return now.replace(minute=0, second=0, microsecond=0).isoformat()
    elif window == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    raise ValueError(f"Unknown window: {window}")


def _get_count(conn: sqlite3.Connection, account: str, action: str, window: str) -> int:
    ws = _window_start(window)
    row = conn.execute(
        "SELECT count FROM rate_counters WHERE account=? AND action=? AND window=? AND window_start=?",
        (account, action, window, ws)
    ).fetchone()
    return row["count"] if row else 0


def _increment(conn: sqlite3.Connection, account: str, action: str, window: str):
    ws = _window_start(window)
    conn.execute(
        """INSERT INTO rate_counters (account, action, window, window_start, count)
           VALUES (?,?,?,?,1)
           ON CONFLICT(account, action, window, window_start)
           DO UPDATE SET count = count + 1""",
        (account, action, window, ws)
    )


def check_rate_limit(account: str, action: str) -> bool:
    """Return True if the action is allowed (under both hourly and daily limits)."""
    limits = {
        "hourly": RATE_LIMITS_HOURLY,
        "daily": RATE_LIMITS_DAILY,
    }
    with get_conn() as conn:
        for window, limit_map in limits.items():
            current = _get_count(conn, account, action, window)
            if current >= limit_map.get(action, 9999):
                logger.warning(f"[{account}] Rate limit hit: {action} {window} ({current}/{limit_map[action]})")
                return False
    return True


def record_action(account: str, action: str):
    """Increment both hourly and daily counters for the given action."""
    with get_conn() as conn:
        _increment(conn, account, action, "hourly")
        _increment(conn, account, action, "daily")


# ---------------------------------------------------------------------------
# Stats / reporting
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Account metadata — ramp-up day tracking and limit multiplier
# ---------------------------------------------------------------------------

def get_or_set_account_start_date(account: str) -> datetime:
    """Return first-use date for the account. Creates the record on first call."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT start_date FROM account_meta WHERE account=?", (account,)
        ).fetchone()
        if row:
            return datetime.fromisoformat(row["start_date"])
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        conn.execute(
            "INSERT OR IGNORE INTO account_meta (account, start_date) VALUES (?,?)",
            (account, today.isoformat())
        )
        return today


def get_account_day_number(account: str) -> int:
    """Return the 1-based ramp-up day number for this account."""
    start = get_or_set_account_start_date(account)
    return (datetime.utcnow() - start).days + 1


def get_limit_multiplier(account: str) -> float:
    """Return the current limit multiplier (reduced to 0.5 after a hard 'try again later')."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT limit_multiplier FROM account_meta WHERE account=?", (account,)
        ).fetchone()
    return row["limit_multiplier"] if row else 1.0


def set_limit_multiplier(account: str, multiplier: float):
    """Permanently reduce daily limits for this account (RISEN hard-stop protocol)."""
    # Ensure the record exists
    get_or_set_account_start_date(account)
    with get_conn() as conn:
        conn.execute(
            "UPDATE account_meta SET limit_multiplier=? WHERE account=?",
            (multiplier, account)
        )
    logger.warning(f"[{account}] Limit multiplier permanently set to {multiplier:.1f}x")


def get_daily_stats(account: str) -> dict:
    """Return today's action counts for the given account."""
    ws = _window_start("daily")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT action, count FROM rate_counters WHERE account=? AND window='daily' AND window_start=?",
            (account, ws)
        ).fetchall()
    stats = {r["action"]: r["count"] for r in rows}
    return {
        "follows": stats.get("follows", 0),
        "comments": stats.get("comments", 0),
        "likes": stats.get("likes", 0),
    }
