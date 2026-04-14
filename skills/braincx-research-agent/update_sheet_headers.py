"""One-time script: update sheet header to add Phone and Website columns."""
import os
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")
import gspread

creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
gc = gspread.oauth(credentials_filename=creds_path)
sh = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
ws = sh.worksheet("Leads")

new_headers = [
    "Timestamp", "Platform", "Source", "URL", "Author / Business",
    "Title / Snippet", "Relevance Score", "Lead Score", "ICP Category",
    "Business Type", "Pain Point", "Why It Fits", "Urgency",
    "Decision Maker", "Competitor Mentioned", "Is Job Posting",
    "Phone", "Website", "Claude Reasoning", "Status"
]
ws.update("A1:T1", [new_headers])
print(f"Header updated — {len(new_headers)} columns")
print(f"Sheet rows: {len(ws.get_all_values())}")
