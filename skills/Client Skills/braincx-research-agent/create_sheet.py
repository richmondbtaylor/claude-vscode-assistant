"""
One-time script to create a new BrainCX Lead Intelligence Google Sheet.
Prints the Sheet ID so you can add it to .env.
"""
import os
from dotenv import load_dotenv
import gspread

load_dotenv()

creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
gc = gspread.oauth(credentials_filename=creds_path)

sh = gc.create("BrainCX Lead Intelligence")
sh.share(None, perm_type="anyone", role="writer")  # anyone with link can edit

print(f"Sheet created: {sh.title}")
print(f"URL: https://docs.google.com/spreadsheets/d/{sh.id}/edit")
print(f"Sheet ID: {sh.id}")
print(f"\nAdd this to your .env:\nGOOGLE_SHEET_ID={sh.id}")
