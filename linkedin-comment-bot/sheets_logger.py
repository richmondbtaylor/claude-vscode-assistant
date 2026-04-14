"""
Google Sheets logger — appends one row per replied comment.
Tab: "Comment Log" (auto-created if missing).

Sheet columns:
  Timestamp | Post URL | Post Snippet | Commenter | Profile URL |
  Comment | Lead Score | Reply | Status
"""

import os
import datetime
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
CREDENTIALS_FILE = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
TAB_NAME = "Comment Log"

HEADERS = [
    "Timestamp",
    "Post URL",
    "Post Snippet",
    "Commenter Name",
    "Commenter Profile",
    "Comment Text",
    "Lead Score",
    "Reply",
    "Status",
]


class SheetsLogger:
    def __init__(self):
        if not SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID not set in .env")
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"Google credentials not found at {CREDENTIALS_FILE}. "
                "See setup instructions."
            )

        import gspread
        self.gc = gspread.oauth(credentials_filename=CREDENTIALS_FILE)
        self.spreadsheet = self.gc.open_by_key(SHEET_ID)
        self.ws = self._get_or_create_tab()

    def _get_or_create_tab(self):
        try:
            return self.spreadsheet.worksheet(TAB_NAME)
        except Exception:
            ws = self.spreadsheet.add_worksheet(title=TAB_NAME, rows=2000, cols=len(HEADERS))
            ws.append_row(HEADERS, value_input_option="USER_ENTERED")
            return ws

    def _entry_to_row(self, entry: dict) -> list:
        return [
            entry.get("timestamp", datetime.datetime.now().isoformat()),
            entry.get("postUrl", ""),
            entry.get("postSnippet", ""),
            entry.get("commenterName", ""),
            entry.get("commenterProfile", ""),
            entry.get("commentText", ""),
            entry.get("leadScore", ""),
            entry.get("reply", ""),
            entry.get("status", "Replied"),
        ]

    def log(self, entry: dict):
        """Append one row."""
        self.ws.append_row(self._entry_to_row(entry), value_input_option="USER_ENTERED")

    def log_batch(self, entries: list):
        """Append all rows in a single API call to avoid rate limits."""
        if not entries:
            return
        rows = [self._entry_to_row(e) for e in entries]
        self.ws.append_rows(rows, value_input_option="USER_ENTERED")
