"""
Upload radley_leads.csv to Google Sheets.
Run after radley-lead-finder.js completes.

Usage: python upload_to_sheets.py
"""

import csv
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "radley-research-agent.env")

import gspread

WORKSHEET_NAME = "Leads"
HEADERS = [
    "Rank",
    "Intent Score",
    "Platform",
    "Buyer Persona",
    "Inferred Role",
    "Company",
    "Author / Handle",
    "Profile URL",
    "Post URL",
    "Date Posted",
    "Pain Signal",
    "Outreach Angle",
    "Contact Hint",
    "Post Title",
]

def main():
    csv_path = Path(__file__).parent / "radley_leads.csv"
    if not csv_path.exists():
        print(f"[FAIL] radley_leads.csv not found at {csv_path}")
        sys.exit(1)

    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")

    if not creds_path or not sheet_id:
        print("[FAIL] Missing GOOGLE_OAUTH_CREDENTIALS or GOOGLE_SHEET_ID in env")
        sys.exit(1)

    # Resolve relative creds path from security/ dir
    if not Path(creds_path).is_absolute():
        creds_path = str(Path.home() / ".claude" / "security" / creds_path)

    print("Connecting to Google Sheets...")
    gc = gspread.oauth(credentials_filename=creds_path)
    spreadsheet = gc.open_by_key(sheet_id)
    print(f"[OK] Opened: {spreadsheet.title}")

    # Get or create worksheet
    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)
        print(f"[OK] Found worksheet '{WORKSHEET_NAME}' — clearing old data")
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=500, cols=len(HEADERS))
        print(f"[OK] Created worksheet '{WORKSHEET_NAME}'")

    # Write headers
    ws.append_row(HEADERS, value_input_option="RAW")

    # Read CSV and upload
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip CSV header row
        rows = list(reader)

    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"[OK] Uploaded {len(rows)} leads to '{WORKSHEET_NAME}'")
    else:
        print("[WARN] No leads in CSV to upload")

    print(f"\nSheet: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")


if __name__ == "__main__":
    main()
