"""
One-time script to update the Google Sheet header row to match current SHEET_COLUMNS.
Run this once after adding new columns to config.py.
"""
import os
from dotenv import load_dotenv
import gspread

load_dotenv()

from config import SHEET_COLUMNS, SHEET_WORKSHEET_NAME

creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
gc = gspread.oauth(credentials_filename=creds_path)
spreadsheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)

# Overwrite row 1 with the new headers
ws.update("A1", [SHEET_COLUMNS])
print(f"Updated headers ({len(SHEET_COLUMNS)} columns):")
for i, col in enumerate(SHEET_COLUMNS, 1):
    print(f"  {i:2}. {col}")
