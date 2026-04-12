"""
Google Sheet read/write wrapper for TARSEN.

Reads kill switch, banlists, seed accounts, and reply history.
Writes draft replies, skipped tweets, validation failures, and engagement updates.
"""
import json
import uuid
from datetime import datetime, date
from typing import Optional
from zoneinfo import ZoneInfo

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from config import (
    SHEET_ID, GSPREAD_TOKEN_PATH, GSPREAD_SCOPES, TIMEZONE,
    MAX_REPLIES_PER_ACCOUNT_PER_DAY,
)


def _get_credentials():
    with open(GSPREAD_TOKEN_PATH) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=GSPREAD_SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


class SheetClient:
    def __init__(self):
        self.gc = gspread.authorize(_get_credentials())
        self.sh = self.gc.open_by_key(SHEET_ID)
        self.tz = ZoneInfo(TIMEZONE)

    # --- Control / kill switch ---

    def is_paused(self) -> bool:
        ws = self.sh.worksheet("control")
        val = ws.acell("B2").value
        return (val or "").strip().upper() == "PAUSE"

    def manual_approval_on(self) -> bool:
        ws = self.sh.worksheet("control")
        val = ws.acell("B3").value
        return (val or "").strip().upper() == "ON"

    def daily_cap_override(self) -> Optional[int]:
        ws = self.sh.worksheet("control")
        val = (ws.acell("B4").value or "").strip()
        return int(val) if val.isdigit() else None

    def log_kill(self, workflow: str, reason: str, notes: str = ""):
        ws = self.sh.worksheet("kill_log")
        ws.append_row([self._now_iso(), workflow, reason, notes])

    # --- Banlists ---

    def load_banlists(self) -> dict:
        out = {"phrases": [], "political": [], "competitors": []}
        for tab, key in [
            ("banlist_phrases", "phrases"),
            ("banlist_political", "political"),
            ("banlist_competitors", "competitors"),
        ]:
            try:
                rows = self.sh.worksheet(tab).get_all_values()
                # skip header row, take first column, drop blanks
                out[key] = [r[0].strip().lower() for r in rows[1:] if r and r[0].strip()]
            except gspread.WorksheetNotFound:
                out[key] = []
        return out

    # --- Seed accounts ---

    def load_seed_accounts(self) -> list[dict]:
        ws = self.sh.worksheet("seed_accounts")
        rows = ws.get_all_records()
        return [r for r in rows if str(r.get("active", "")).strip().upper() == "TRUE"]

    # --- Reply history ---

    def replies_today(self) -> list[dict]:
        ws = self.sh.worksheet("replies")
        rows = ws.get_all_records()
        today_str = datetime.now(self.tz).date().isoformat()
        return [r for r in rows if str(r.get("timestamp_et", "")).startswith(today_str)]

    def can_reply_to_account(self, handle: str) -> bool:
        today_rows = self.replies_today()
        count = sum(
            1 for r in today_rows
            if str(r.get("target_handle", "")).lower() == handle.lower()
            and str(r.get("approval_status", "")) in ("auto", "manual_approved", "pending")
        )
        return count < MAX_REPLIES_PER_ACCOUNT_PER_DAY

    def replied_today_count(self) -> int:
        return sum(
            1 for r in self.replies_today()
            if str(r.get("approval_status", "")) in ("auto", "manual_approved")
        )

    def already_replied_to_tweet(self, tweet_url: str) -> bool:
        ws = self.sh.worksheet("replies")
        rows = ws.get_all_records()
        return any(str(r.get("tweet_url", "")) == tweet_url for r in rows)

    def insert_draft(self, draft: dict) -> str:
        """Insert a draft reply row, return the row id."""
        ws = self.sh.worksheet("replies")
        row_id = uuid.uuid4().hex[:8]
        row = [
            row_id,
            self._now_iso(),
            draft["target_handle"],
            draft["tweet_url"],
            (draft.get("tweet_text") or "")[:500],
            draft.get("thread_context", ""),
            draft.get("tweet_type", ""),
            draft.get("reply_style", ""),
            draft.get("reply_text", ""),
            draft.get("word_count", 0),
            draft.get("approval_status", "pending"),
            draft.get("approved_by", ""),
            "",  # posted_at - filled later
            0, 0, 0,  # engagement counters
            draft.get("notes", ""),
        ]
        ws.append_row(row)
        return row_id

    def log_skip(self, tweet_url: str, reason: str, handle: str = "", notes: str = ""):
        ws = self.sh.worksheet("skipped")
        ws.append_row([self._now_iso(), tweet_url, reason, handle, notes])

    def log_validation_failure(self, tweet_url: str, draft_text: str, failed_check: str, details: str = ""):
        ws = self.sh.worksheet("failed_validation")
        ws.append_row([self._now_iso(), tweet_url, draft_text[:500], failed_check, details, ""])

    # --- Helpers ---

    def _now_iso(self) -> str:
        return datetime.now(self.tz).isoformat(timespec="seconds")
