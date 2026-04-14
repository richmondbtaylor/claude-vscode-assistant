"""
Retroactive enrichment script — reads existing leads from Google Sheet,
finds rows missing Phone/Website/Email/DM data, enriches them, and patches
the cells in-place.

Run: python enrich_sheet.py
     python enrich_sheet.py --min-score 50   (default)
     python enrich_sheet.py --min-score 70   (hot leads only)
"""

import argparse
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import gspread

import apollo_enrichment
import contact_finder
import email_finder
from config import SHEET_COLUMNS, SHEET_WORKSHEET_NAME

# Column indices (1-based for gspread)
_COL = {name: idx + 1 for idx, name in enumerate(SHEET_COLUMNS)}

# Columns we care about
C_AUTHOR    = _COL["Author / Business"]
C_TITLE     = _COL["Title / Snippet"]
C_SCORE     = _COL["Relevance Score"]
C_ICP       = _COL["ICP Category"]
C_IS_JOB    = _COL["Is Job Posting"]
C_PHONE     = _COL["Phone"]
C_WEBSITE   = _COL["Website"]
C_DM_NAME   = _COL["DM Name"]
C_DM_TITLE  = _COL["DM Title"]
C_EMAIL     = _COL["Email"]


def _parse_company(author: str, title: str, is_job: str) -> str:
    """Extract company name from sheet row — mirrors notifier.py logic."""
    skip = {"unknown", "", "n/a", "indeed.com", "linkedin.com"}
    if author and author.lower() not in skip:
        # LinkedIn jobs: "Company hiring Role" — take everything before " hiring "
        if " hiring " in author:
            return author.split(" hiring ")[0].strip()
        return author.strip()

    if is_job.lower() in ("yes", "true"):
        # Indeed: "Role - Location - Company" or "Role - Company"
        if " - " in title and not title.lower().startswith("apply today"):
            parts = title.split(" - ")
            if len(parts) >= 3:
                return parts[-2].strip()
            elif len(parts) == 2:
                return parts[0].strip()
        # LinkedIn job in title
        if " hiring " in title:
            return title.split(" hiring ")[0].strip()

    return ""


def _needs_enrichment(row: list, min_score: int) -> bool:
    """True if this row should be enriched."""
    def cell(col):
        idx = col - 1
        return row[idx].strip() if idx < len(row) else ""

    try:
        score = int(cell(C_SCORE))
    except ValueError:
        return False

    if score < min_score:
        return False

    # Already has both email AND phone — skip
    has_email = bool(cell(C_EMAIL))
    has_phone = bool(cell(C_PHONE))
    has_website = bool(cell(C_WEBSITE))
    if has_email and has_phone:
        return False

    return True


def enrich_sheet(min_score: int = 50):
    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
    gc = gspread.oauth(credentials_filename=creds_path)
    spreadsheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)

    all_rows = ws.get_all_values()
    header = all_rows[0]
    data_rows = all_rows[1:]  # skip header

    print(f"[enrich] Sheet has {len(data_rows)} data rows. Enriching rows with score >= {min_score}...")

    enriched = 0
    skipped = 0

    for i, row in enumerate(data_rows):
        sheet_row_num = i + 2  # 1-indexed, +1 for header

        def cell(col):
            idx = col - 1
            return row[idx].strip() if idx < len(row) else ""

        if not _needs_enrichment(row, min_score):
            skipped += 1
            continue

        author  = cell(C_AUTHOR)
        title   = cell(C_TITLE)
        is_job  = cell(C_IS_JOB)
        icp     = cell(C_ICP)
        website = cell(C_WEBSITE)
        existing_phone   = cell(C_PHONE)
        existing_website = cell(C_WEBSITE)
        existing_dm_name = cell(C_DM_NAME)
        existing_email   = cell(C_EMAIL)

        company = _parse_company(author, title, is_job)
        if not company:
            skipped += 1
            continue

        print(f"\n[enrich] Row {sheet_row_num}: {company} (score={cell(C_SCORE)}, icp={icp})")

        # Contact enrichment — phone + website
        contact = contact_finder.ContactInfo()
        if not existing_phone or not existing_website:
            contact = contact_finder.lookup(company_name=company)
            time.sleep(0.5)

        # Use best available website (existing wins if it's a real one)
        best_website = existing_website or contact.website
        _skip_sites = {"zoominfo.com", "leadiq.com", "contactout.com", "pissedconsumer.com"}
        if best_website and any(s in best_website for s in _skip_sites):
            best_website = contact.website if contact.website not in best_website else ""

        # Email/DM enrichment: Apollo first, then existing email_finder fallback
        dm = email_finder.DecisionMaker()
        if not existing_email or not existing_dm_name:
            apollo = apollo_enrichment.enrich(company, icp)
            if apollo:
                dm = email_finder.DecisionMaker(
                    name=f"{apollo.get('first_name', '')} {apollo.get('last_name', '')}".strip(),
                    title=apollo.get("title", ""),
                    email=apollo.get("email", ""),
                    source=apollo.get("source", "apollo.io"),
                )
            else:
                dm = email_finder.lookup(
                    company_name=company,
                    website=best_website,
                    icp_category=icp,
                )
            time.sleep(0.5)

        # Build updates — only write cells that improved
        updates = []

        phone_val = contact.phone or existing_phone
        if phone_val and phone_val != existing_phone:
            updates.append((sheet_row_num, C_PHONE, phone_val))

        site_val = best_website or existing_website
        if site_val and site_val != existing_website:
            updates.append((sheet_row_num, C_WEBSITE, site_val))

        dm_name_val = dm.name or existing_dm_name
        if dm_name_val and dm_name_val != existing_dm_name:
            updates.append((sheet_row_num, C_DM_NAME, dm_name_val))

        dm_title_val = dm.title or cell(C_DM_TITLE)
        if dm_title_val and dm_title_val != cell(C_DM_TITLE):
            updates.append((sheet_row_num, C_DM_TITLE, dm_title_val))

        email_val = dm.email or existing_email
        if email_val and email_val != existing_email:
            updates.append((sheet_row_num, C_EMAIL, email_val))

        if updates:
            for row_num, col_num, value in updates:
                ws.update_cell(row_num, col_num, value)
                time.sleep(0.1)
            print(f"  [OK] Updated {len(updates)} cells: { {c: v for _, c, v in updates} }")
            enriched += 1
        else:
            print(f"  [--] No new data found")

    print(f"\n[enrich] Done. Enriched: {enriched} rows | Skipped: {skipped} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-score", type=int, default=50)
    args = parser.parse_args()
    enrich_sheet(min_score=args.min_score)
