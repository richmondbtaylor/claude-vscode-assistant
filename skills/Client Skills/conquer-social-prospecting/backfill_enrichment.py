"""
Backfill contact enrichment for existing sheet leads via Apollo.io.
Reads all rows where Decision Maker Name is blank + Company Name is set,
calls Apollo, writes name/title/email/LinkedIn back to the sheet.

Usage:
    python backfill_enrichment.py [--dry-run] [--limit N]
"""

import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "conquer-social-prospecting.env")

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

from config import SHEET_COLUMNS, SHEET_WORKSHEET_NAME
import enrichment

# Column indices (0-based)
COL = {name: i for i, name in enumerate(SHEET_COLUMNS)}

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_TOKEN_PATH = Path(__file__).parent / "token.pickle"
_CREDS_PATH = Path(os.environ["GOOGLE_OAUTH_CREDENTIALS"])
_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]


def _get_sheet():
    creds = None
    if _TOKEN_PATH.exists():
        with open(_TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDS_PATH), _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    gc = gspread.authorize(creds)
    return gc.open_by_key(_SHEET_ID).worksheet(SHEET_WORKSHEET_NAME)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print matches, don't write")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to enrich (0 = all)")
    args = parser.parse_args()

    ws = _get_sheet()
    all_rows = ws.get_all_values()
    header = all_rows[0]
    data = all_rows[1:]

    name_col = COL["Decision Maker Name"]
    title_col = COL["Decision Maker Title"]
    email_col = COL["Estimated Email"]
    source_col = COL["Contact Source"]
    company_col = COL["Company Name"]
    job_col = COL["Job Title"]

    # Identify rows needing enrichment (1-indexed for gspread, +2 for header)
    to_enrich = []
    for i, row in enumerate(data):
        # pad short rows
        while len(row) < len(SHEET_COLUMNS):
            row.append("")
        company = row[company_col].strip()
        existing_name = row[name_col].strip()
        # Skip separators, blanks, already enriched
        if not company or company.lower() in ("unknown", ""):
            continue
        if company.startswith("***") or company.startswith("==="):
            continue
        if existing_name:
            continue
        to_enrich.append((i + 2, row))  # gspread row = data index + 2

    total = len(to_enrich)
    if args.limit:
        to_enrich = to_enrich[:args.limit]

    print(f"Found {total} rows needing enrichment. Processing {len(to_enrich)}...")
    if args.dry_run:
        print("DRY RUN — no writes.\n")

    enriched = 0
    skipped = 0

    for sheet_row, row in to_enrich:
        company = row[company_col].strip()
        job = row[job_col].strip()
        result = enrichment.enrich(company, job)

        if not result:
            print(f"  [no match] Row {sheet_row}: {company}")
            skipped += 1
            continue

        name = f"{result.get('first_name', '')} {result.get('last_name', '')}".strip()
        title = result.get("title", "")
        email = result.get("email", "")
        source_note = result.get("source", "")

        print(f"  [found] Row {sheet_row}: {company} -> {name} ({title}) {email}")

        if not args.dry_run:
            # Write cells individually to avoid overwriting other columns
            ws.update_cell(sheet_row, name_col + 1, name)
            ws.update_cell(sheet_row, title_col + 1, title)
            ws.update_cell(sheet_row, email_col + 1, email)
            ws.update_cell(sheet_row, source_col + 1, source_note)
            time.sleep(1.2)  # Sheets API rate limit

        enriched += 1

    print(f"\nDone. Enriched: {enriched} | No match: {skipped} | Total processed: {enriched + skipped}")


if __name__ == "__main__":
    main()
