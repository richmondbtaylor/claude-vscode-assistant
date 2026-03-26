"""
Add a receipt entry to the Bishop AI expense tracker Google Sheet.
Usage: python add_receipt.py
"""
import gspread
import os

SHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
CREDS_PATH = os.path.expanduser(
    os.path.join(
        "~", ".claude", "skills", "bishop-research-agent",
        "client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
    )
)

# Receipt data from Staples - 2/26/26
ROWS = [
    {
        "Date": "2/26/2026",
        "Vendor": "Staples",
        "Amount": "$12.49",
        "Category": "Office & Supplies",
        "Payment Method": "Visa Credit x0404",
        "Drive Link": "",
        "Notes": "Scotch LG Mounting (051141253817)",
    },
    {
        "Date": "2/26/2026",
        "Vendor": "Staples",
        "Amount": "$8.99",
        "Category": "Office & Supplies",
        "Payment Method": "Visa Credit x0404",
        "Drive Link": "",
        "Notes": "Name Bdg LBL (072782051471)",
    },
]

HEADERS = ["Date", "Vendor", "Amount", "Category", "Payment Method", "Drive Link", "Notes"]
TAB = "Personal"


def main():
    print("Connecting to Google Sheets...")
    gc = gspread.oauth(credentials_filename=CREDS_PATH)
    spreadsheet = gc.open_by_key(SHEET_ID)

    ws = spreadsheet.worksheet(TAB)

    for row in ROWS:
        values = [row[h] for h in HEADERS]
        ws.append_row(values, value_input_option="USER_ENTERED")
        print(f"  Added: {row['Date']} | {row['Vendor']} | {row['Amount']} | {row['Notes']}")

    print(f"\nDone! Added {len(ROWS)} entries to the '{TAB}' tab.")


if __name__ == "__main__":
    main()
