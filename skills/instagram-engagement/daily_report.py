"""
Daily Report — Instagram Engagement Automation

Runs at 5 AM via Windows Task Scheduler.
Queries yesterday's engagement data from SQLite and appends one summary row
to the 'Daily Summary' tab in Google Sheets.

Usage:
  python daily_report.py --account main_account
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "instagram-engagement.env")

import engagement_tracker as tracker
import gspread
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DAILY REPORT] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)
TOKEN_PATH = os.path.expanduser(r"~\AppData\Roaming\gspread\authorized_user.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TAB_DAILY    = "Daily Summary"
TAB_FOLLOWS  = "Follow Tracker"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_gspread_client():
    """Authenticate with Google Sheets. If token is missing or expired, auto-triggers browser OAuth flow."""
    token_path = Path(TOKEN_PATH)
    if not token_path.exists():
        logger.warning("No saved Google token found — opening browser to authenticate...")
    try:
        return gspread.oauth(credentials_filename=CREDS_PATH)
    except Exception as e:
        logger.warning(f"Auth failed ({e}) — retrying with fresh OAuth flow...")
        # Delete stale token and retry — gspread will open the browser
        if token_path.exists():
            token_path.unlink()
            logger.info("Stale token removed, re-authenticating...")
        return gspread.oauth(credentials_filename=CREDS_PATH)


# ---------------------------------------------------------------------------
# Data queries
# ---------------------------------------------------------------------------

def get_yesterday_range() -> tuple[str, str]:
    """Return ISO start/end for yesterday (UTC)."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return yesterday.isoformat(), today.isoformat()


def query_yesterday_stats(account: str) -> dict:
    """Pull all engagement counts for yesterday from SQLite."""
    start, end = get_yesterday_range()
    date_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    with tracker.get_conn() as conn:
        follows = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE account=? AND followed_at >= ? AND followed_at < ?",
            (account, start, end)
        ).fetchone()[0]

        unfollows = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE account=? AND unfollowed_at >= ? AND unfollowed_at < ?",
            (account, start, end)
        ).fetchone()[0]

        comments = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE account=? AND created_at >= ? AND created_at < ?",
            (account, start, end)
        ).fetchone()[0]

        likes = conn.execute(
            "SELECT COUNT(*) FROM likes WHERE account=? AND created_at >= ? AND created_at < ?",
            (account, start, end)
        ).fetchone()[0]

        follow_backs = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE account=? AND followed_back=1 AND checked_at >= ? AND checked_at < ?",
            (account, start, end)
        ).fetchone()[0]

        # Cumulative totals (all time)
        total_following = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE account=? AND unfollowed_at IS NULL",
            (account,)
        ).fetchone()[0]

        total_follows_ever = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE account=?",
            (account,)
        ).fetchone()[0]

        total_follow_backs_ever = conn.execute(
            "SELECT COUNT(*) FROM follows WHERE account=? AND followed_back=1",
            (account,)
        ).fetchone()[0]

    follow_back_rate = round(
        (total_follow_backs_ever / total_follows_ever * 100) if total_follows_ever > 0 else 0, 1
    )
    net_gain = follows - unfollows

    return {
        "date": date_str,
        "account": account,
        "follows": follows,
        "comments": comments,
        "likes": likes,
        "unfollows": unfollows,
        "follow_backs_received": follow_backs,
        "net_gain": net_gain,
        "total_currently_following": total_following,
        "total_follows_ever": total_follows_ever,
        "total_follow_backs_ever": total_follow_backs_ever,
        "follow_back_rate_pct": follow_back_rate,
    }


def get_all_follows(account: str) -> list[dict]:
    """Return full follow tracker data for this account."""
    with tracker.get_conn() as conn:
        rows = conn.execute(
            """SELECT target_user, followed_at, followed_back, checked_at,
                      unfollowed_at, last_engaged_at
               FROM follows WHERE account=?
               ORDER BY followed_at DESC""",
            (account,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Sheet helpers
# ---------------------------------------------------------------------------

def ensure_tab(spreadsheet, tab_name: str, headers: list[str]):
    """Get or create a worksheet with the given headers on row 1."""
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=5000, cols=len(headers))
        ws.append_row(headers)
        logger.info(f"Created tab: {tab_name}")
    return ws


def push_daily_summary(ws, stats: dict):
    """Append one daily summary row. Skip if today's row already exists."""
    existing = ws.col_values(1)  # column A = dates
    if stats["date"] in existing:
        logger.info(f"Daily summary for {stats['date']} already logged — skipping")
        return

    row = [
        stats["date"],
        stats["account"],
        stats["follows"],
        stats["comments"],
        stats["likes"],
        stats["unfollows"],
        stats["follow_backs_received"],
        stats["net_gain"],
        stats["total_currently_following"],
        stats["total_follows_ever"],
        stats["total_follow_backs_ever"],
        f"{stats['follow_back_rate_pct']}%",
    ]
    ws.append_row(row)
    logger.info(f"Daily summary appended for {stats['date']}")


def push_follow_tracker(ws, follows: list[dict]):
    """Full overwrite of the follow tracker tab (clear + rewrite)."""
    ws.clear()
    headers = [
        "Username", "Followed At", "Followed Back?", "Checked At",
        "Unfollowed At", "Last Engaged At", "Status"
    ]
    rows = [headers]
    for f in follows:
        if f["unfollowed_at"]:
            status = "Unfollowed"
        elif f["followed_back"]:
            status = "Follows Back"
        else:
            status = "Pending"
        rows.append([
            f["target_user"],
            f["followed_at"][:10] if f["followed_at"] else "",
            "Yes" if f["followed_back"] else "No",
            f["checked_at"][:10] if f["checked_at"] else "",
            f["unfollowed_at"][:10] if f["unfollowed_at"] else "",
            f["last_engaged_at"][:10] if f["last_engaged_at"] else "",
            status,
        ])
    ws.update(rows, "A1")
    logger.info(f"Follow tracker updated: {len(follows)} records")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Daily Sheets report for Instagram Engagement")
    parser.add_argument("--account", required=True, help="Account key (e.g. main_account)")
    args = parser.parse_args()

    spreadsheet_id = os.environ.get("SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        logger.error("SHEETS_SPREADSHEET_ID not set in .env")
        sys.exit(1)

    tracker.init_db()

    logger.info(f"Generating daily report for: {args.account}")
    stats = query_yesterday_stats(args.account)
    follows = get_all_follows(args.account)

    logger.info(f"Yesterday: {stats['follows']} follows | {stats['comments']} comments | "
                f"{stats['likes']} likes | {stats['unfollows']} unfollows | "
                f"net gain: {stats['net_gain']:+d}")

    try:
        gc = get_gspread_client()
        spreadsheet = gc.open_by_key(spreadsheet_id)

        # Tab 1: Daily Summary
        ws_daily = ensure_tab(spreadsheet, TAB_DAILY, [
            "Date", "Account", "Follows", "Comments", "Likes", "Unfollows",
            "Follow-backs Received", "Net Gain", "Currently Following",
            "Total Follows (Ever)", "Total Follow-backs (Ever)", "Follow-back Rate %"
        ])
        push_daily_summary(ws_daily, stats)

        # Tab 2: Follow Tracker (full sync)
        ws_follows = ensure_tab(spreadsheet, TAB_FOLLOWS, [
            "Username", "Followed At", "Followed Back?", "Checked At",
            "Unfollowed At", "Last Engaged At", "Status"
        ])
        push_follow_tracker(ws_follows, follows)

        logger.info("Daily report complete.")

    except Exception as e:
        logger.error(f"Sheets update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
