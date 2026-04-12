"""
Resumes the TARSEN sheet setup. Idempotent - skips tabs that already exist
and uses batch writes (one API call per tab) to stay well under the
60-writes-per-minute quota.

Run after setup_sheet.py if it bails partway through.
"""
import json
import os
import time

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

TOKEN_PATH = os.path.expanduser(r"~\AppData\Roaming\gspread\authorized_user.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEET_ID = "1em3nkXBeQAEaAbVZbE-Aif6PmVtSV1QkPsurKnKPdWU"

TABS = {
    "banlist_political": [
        ["banned_keyword", "reason"],
        ["trump", "Political - hard skip per Rich's spec"],
        ["biden", "Political - hard skip"],
        ["election", "Political - hard skip"],
        ["abortion", "Political - hard skip"],
        ["israel", "Political - hard skip"],
        ["palestine", "Political - hard skip"],
        ["gaza", "Political - hard skip"],
        ["ukraine", "Political - hard skip"],
        ["religion", "Religious - hard skip"],
        ["christian", "Religious - hard skip"],
        ["muslim", "Religious - hard skip"],
        ["jewish", "Religious - hard skip"],
        ["doomer", "Doomer rhetoric - hard skip per spec"],
        ["AI will kill", "Doomer rhetoric"],
        ["replace humans", "Per Rich's standing rule - never engage with humans-replaced framing"],
        ["fire your", "Per Rich's standing rule - never encourage firing people"],
    ],
    "banlist_competitors": [
        ["competitor_name", "reason"],
    ],
    "skipped": [
        ["timestamp_et", "tweet_url", "skip_reason", "target_handle", "notes"],
    ],
    "failed_validation": [
        ["timestamp_et", "tweet_url", "draft_text", "failed_check", "details", "notes"],
    ],
    "kill_log": [
        ["timestamp_et", "workflow", "trigger_reason", "notes"],
    ],
}


def get_credentials():
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


def main():
    creds = get_credentials()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    existing = {ws.title for ws in sh.worksheets()}
    print(f"Existing tabs: {sorted(existing)}")

    for tab_name, rows in TABS.items():
        if tab_name in existing:
            print(f"[skip] '{tab_name}' already exists")
            continue
        ws = sh.add_worksheet(title=tab_name, rows=max(100, len(rows) + 50), cols=max(5, len(rows[0])))
        # Single batch write for all rows
        ws.update(values=rows, range_name=f"A1:{chr(ord('A') + len(rows[0]) - 1)}{len(rows)}")
        print(f"[ok]   '{tab_name}' created with {len(rows)} rows")
        time.sleep(2)  # be polite to the quota

    print()
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/")


if __name__ == "__main__":
    main()
