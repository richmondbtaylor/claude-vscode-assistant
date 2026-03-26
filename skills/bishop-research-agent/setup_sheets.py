"""
Run this once to authorize Google Sheets and create the header row.
A browser window will open — sign in and click Allow.
After that, the main agent writes to Sheets automatically with no browser needed.

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
    print("Setting up Google Sheets...")
    print("A browser window will open — sign in and click Allow.\n")

    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")

    try:
        gc = gspread.oauth(credentials_filename=creds_path)
        print("[OK] Google authorization successful!")
    except Exception as e:
        print(f"[FAIL] Authorization failed: {e}")
        print("\nMake sure:")
        print(f"  1. The credentials file exists at: {creds_path}")
        print("  2. GOOGLE_OAUTH_CREDENTIALS is set in your .env")
        sys.exit(1)

    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id or sheet_id == "your_google_sheet_id_here":
        print("[FAIL] GOOGLE_SHEET_ID is not set in your .env file")
        sys.exit(1)

    try:
        spreadsheet = gc.open_by_key(sheet_id)
        print(f"[OK] Opened sheet: '{spreadsheet.title}'")
    except Exception as e:
        print(f"[FAIL] Could not open sheet: {e}")
        print("Make sure the Sheet ID in .env is correct.")
        sys.exit(1)

    # Create or find the Leads worksheet
    try:
        ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)
        print(f"[OK] Found existing worksheet '{SHEET_WORKSHEET_NAME}'")
        first_row = ws.row_values(1)
        if not first_row:
            ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
            print(f"[OK] Header row added")
        else:
            print(f"[OK] Headers already present: {first_row[:4]}...")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=SHEET_WORKSHEET_NAME,
            rows=1000,
            cols=len(SHEET_COLUMNS),
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        print(f"[OK] Created worksheet '{SHEET_WORKSHEET_NAME}' with headers")

    # Write a test row so you can confirm it's working in the sheet
    from datetime import datetime, timezone
    test_row = [
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "TEST",
        "https://example.com",
        "setup_script",
        "Setup test row — delete me",
        "N/A", "N/A", "N/A", "N/A", "N/A", "N/A",
        "DELETE ME",
    ]
    ws.append_row(test_row, value_input_option="USER_ENTERED")
    print(f"[OK] Test row written to sheet — check your Google Sheet now!")
    print(f"\nSetup complete. You can now run: python main.py")

if __name__ == "__main__":
    main()
