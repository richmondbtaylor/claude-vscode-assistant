"""
Sets up headers on all three tabs of the Bishop AI expense tracker.
Will open a browser for Google OAuth on first run.
"""
import gspread
import os

SHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)

HEADERS = ["Date", "Vendor", "Amount", "Category", "Payment Method", "Drive Link", "Notes"]
TABS = ["Bishop AI", "Prompt Anything", "Personal"]

gc = gspread.oauth(credentials_filename=CREDS_PATH)
spreadsheet = gc.open_by_key(SHEET_ID)

for tab_name in TABS:
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=10)
        print(f"Created tab: {tab_name}")

    existing = ws.row_values(1)
    if existing:
        print(f"{tab_name}: headers already exist ({existing}), skipping.")
    else:
        ws.append_row(HEADERS)
        print(f"{tab_name}: headers added.")

print("\nDone! All tabs are ready.")
