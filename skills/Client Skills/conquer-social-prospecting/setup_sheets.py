"""
Run this once to authorize Google Sheets and create the header row.
A browser window will open — sign in and click Allow.
After authorization, the main agent writes to Sheets automatically.

Usage:  python setup_sheets.py
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import gspread
from config import SHEET_COLUMNS, SHEET_WORKSHEET_NAME


def main():
    print("Conquer.io — Setting up Google Sheets...")
    print("A browser window will open — sign in and click Allow.\n")

    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")

    try:
        gc = gspread.oauth(credentials_filename=creds_path)
        print("[OK] Google authorization successful!")
    except Exception as e:
        print(f"[FAIL] Authorization failed: {e}")
        print("\nMake sure:")
        print(f"  1. The credentials file exists at: {creds_path}")
        print("  2. GOOGLE_OAUTH_CREDENTIALS is set in your .env file")
        sys.exit(1)

    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id or sheet_id == "your_google_sheet_id_here":
        print("[FAIL] GOOGLE_SHEET_ID is not set in your .env file")
        print("  Create a new Google Sheet and paste its ID into .env")
        sys.exit(1)

    try:
        spreadsheet = gc.open_by_key(sheet_id)
        print(f"[OK] Opened sheet: '{spreadsheet.title}'")
    except Exception as e:
        print(f"[FAIL] Could not open sheet: {e}")
        print("Make sure the Sheet ID in .env is correct and the sheet is shared with your Google account.")
        sys.exit(1)

    try:
        ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)
        print(f"[OK] Found existing worksheet '{SHEET_WORKSHEET_NAME}'")
        first_row = ws.row_values(1)
        if not first_row:
            ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
            print(f"[OK] Header row added ({len(SHEET_COLUMNS)} columns)")
        else:
            print(f"[OK] Headers already present: {first_row[:4]}...")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=SHEET_WORKSHEET_NAME,
            rows=2000,
            cols=len(SHEET_COLUMNS),
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        print(f"[OK] Created worksheet '{SHEET_WORKSHEET_NAME}' with {len(SHEET_COLUMNS)} columns")

    # Write a test row so you can confirm it's working
    from datetime import datetime, timezone
    test_row = [
        datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M"),
        "TEST",                          # Platform
        "setup",                         # Source Community
        "https://example.com",           # URL
        "setup_script",                  # Poster Handle
        "Setup test row — delete me",   # Post Snippet
        0,                               # Intent Score
        "Low",                           # Score Tier
        "unknown",                       # Job Title
        "unknown",                       # Company Name
        "No",                            # Salesforce Confirmed
        "No",                            # GDPR Flag
        "unknown",                       # Industry Signal
        "unknown",                       # Company Size Signal
        "not_relevant",                  # Pain Category
        "",                              # Competitor Mentioned
        "",                              # Post Age Days
        "",                              # Outreach - Public Forum
        "",                              # Outreach - DM Pivot
        "",                              # Outreach - Direct Internal
        "No",                            # Should Contact
        "log_only",                      # Escalation
        "not needed",                    # CRM Check
        "Setup test row",                # Claude Reasoning
        "DELETE ME",                     # Status
    ]
    ws.append_row(test_row, value_input_option="USER_ENTERED")
    print(f"[OK] Test row written — check your Google Sheet and delete it.")

    print(f"\n{'='*50}")
    print(f"Setup complete!")
    print(f"Sheet: {spreadsheet.title}")
    print(f"Worksheet: {SHEET_WORKSHEET_NAME}")
    print(f"Columns: {len(SHEET_COLUMNS)}")
    print(f"\nYou can now run: python main.py --once")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
