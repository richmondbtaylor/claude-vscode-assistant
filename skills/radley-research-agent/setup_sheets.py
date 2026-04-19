"""
One-time Google Sheets OAuth setup.
Run this interactively first to authorize gspread.
"""

import os
from dotenv import load_dotenv

load_dotenv("C:/Users/docch/.claude/security/.env")

import gspread

creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
print(f"Using credentials from: {creds_path}")
print("A browser window will open for Google OAuth authorization...")

gc = gspread.oauth(credentials_filename=creds_path)
print("Authorization successful!")
print(f"Token cached at: ~/.config/gspread/authorized_user.json")

sheet_id = os.environ.get("RADLEY_SHEET_ID", "")
if sheet_id:
    try:
        spreadsheet = gc.open_by_key(sheet_id)
        print(f"Successfully accessed sheet: {spreadsheet.title}")
    except Exception as e:
        print(f"Could not access sheet {sheet_id}: {e}")
else:
    print("RADLEY_SHEET_ID not set in .env — set it after creating the Google Sheet")
