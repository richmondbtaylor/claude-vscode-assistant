"""
Update Google Sheet header row to match current SHEET_COLUMNS config.
"""

import os
from dotenv import load_dotenv

load_dotenv("C:/Users/docch/.claude/security/.env")

import gspread
from config import SHEET_COLUMNS, SHEET_WORKSHEET_NAME

creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
gc = gspread.oauth(credentials_filename=creds_path)

sheet_id = os.environ["RADLEY_SHEET_ID"]
spreadsheet = gc.open_by_key(sheet_id)

try:
    ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)
except gspread.WorksheetNotFound:
    ws = spreadsheet.add_worksheet(title=SHEET_WORKSHEET_NAME, rows=1000, cols=len(SHEET_COLUMNS))

ws.update(range_name="A1", values=[SHEET_COLUMNS])
print(f"Updated headers in '{SHEET_WORKSHEET_NAME}' ({len(SHEET_COLUMNS)} columns)")
