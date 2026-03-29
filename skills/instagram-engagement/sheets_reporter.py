"""
Google Sheets reporter for Instagram Engagement sessions.

Appends one row per session to the configured spreadsheet.
Uses the same OAuth credentials as the receipt-filer pipeline.
Fails silently — never breaks an engagement run.
"""

import logging
import os
import json
from datetime import datetime, timezone

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)
TOKEN_PATH = os.path.expanduser(r"~\AppData\Roaming\gspread\authorized_user.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_credentials() -> Credentials:
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def log_session(
    account: str,
    focus: str,
    duration_minutes: int,
    day_number: int,
    dry_run: bool,
    followed: int,
    commented: int,
    liked: int,
    unfollowed: int,
    skipped: int,
    errors: int,
    daily_follows: int,
    daily_follows_limit: int,
    daily_comments: int,
    daily_comments_limit: int,
    daily_likes: int,
    daily_likes_limit: int,
    spreadsheet_id: str,
    tab_name: str = "Instagram Engagement",
):
    """Append one row to the Google Sheet. Logs a warning and returns on any error."""
    try:
        creds = _get_credentials()
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)

        try:
            ws = spreadsheet.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=20)
            ws.append_row([
                "Date", "Time (UTC)", "Account", "Focus Hashtag", "Duration (min)",
                "Ramp Day", "Dry Run", "Followed", "Commented", "Liked",
                "Unfollowed", "Skipped", "Errors",
                "Daily Follows", "Daily Follows Limit",
                "Daily Comments", "Daily Comments Limit",
                "Daily Likes", "Daily Likes Limit",
            ])

        now = datetime.now(timezone.utc)
        row = [
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            account,
            focus or "",
            duration_minutes,
            day_number,
            "Yes" if dry_run else "No",
            followed,
            commented,
            liked,
            unfollowed,
            skipped,
            errors,
            daily_follows,
            daily_follows_limit,
            daily_comments,
            daily_comments_limit,
            daily_likes,
            daily_likes_limit,
        ]
        ws.append_row(row)
        logger.info(f"[{account}] Session logged to Google Sheets ({tab_name})")

    except Exception as e:
        logger.warning(f"[{account}] Google Sheets logging failed (non-fatal): {e}")
