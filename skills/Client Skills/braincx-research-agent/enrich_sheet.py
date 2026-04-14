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

# Emails that are known fakes / placeholders — never write these to the sheet
# Companies that are job boards / aggregators -- never worth enriching
_SKIP_COMPANY_NAMES = {
    "indeed.com", "indeed", "linkedin.com", "linkedin", "ziprecruiter",
    "glassdoor", "glassdoor.com", "monster.com", "monster", "careerbuilder",
    "simplyhired", "snagajob", "podiatry",
}

_BAD_EMAIL_BLOCKLIST = {
    "jane@rocketreach.co", "jane@bmcofny.com", "jdoe@cmpractice.com",
    "development@cityofvancouver.us", "adaytonauto@gmail.com",
    "ais@parks.ca.gov", "rmgresumes@raleighmedicalgroup.com",
    "info@barrenriverregionalcancercenter.com",
    "bblock@podiatrym.com",  # podiatry trade magazine, not a lead
    "jane.doe@medcenterhealth.org",  # demo placeholder email
}

# Website domains that should never be written as a company's website
_BAD_WEBSITE_DOMAINS = {
    "unitedstateszipcodes.org", "crystal.k12.mo.us", "cityofvancouver.us",
    "parks.ca.gov", "instagram.com", "reddit.com", "similarweb.com",
    "semrush.com", "ahrefs.com",
}


import re as _re
_CITY_STATE_RE = _re.compile(r"^[A-Za-z\s]+,\s*[A-Z]{2}(\s+\d{5})?$")


def _is_location(s: str) -> bool:
    """True if the string looks like a city/state or city, ST ZIP — not a company name."""
    return bool(_CITY_STATE_RE.match(s.strip()))


def _parse_company(author: str, title: str, is_job: str) -> str:
    """Extract company name from sheet row — mirrors notifier.py logic."""
    skip = {"unknown", "", "n/a", "indeed.com", "linkedin.com"}
    if author and author.lower() not in skip and not _is_location(author):
        # LinkedIn jobs: "Company hiring Role" — take everything before " hiring "
        if " hiring " in author:
            return author.split(" hiring ")[0].strip()
        return author.strip()

    if is_job.lower() in ("yes", "true"):
        # Indeed: "Role - Location - Company" or "Role - Company"
        if " - " in title and not title.lower().startswith("apply today"):
            parts = title.split(" - ")
            if len(parts) >= 3:
                candidate = parts[-2].strip()
                if _is_location(candidate):
                    # parts[-2] is the location; try to use the last part as company
                    candidate = parts[-1].strip()
                if candidate and not _is_location(candidate):
                    return candidate
            elif len(parts) == 2:
                candidate = parts[0].strip()
                if candidate and not _is_location(candidate):
                    return candidate
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
        if not company or _is_location(company) or company.lower() in _SKIP_COMPANY_NAMES:
            skipped += 1
            continue

        print(f"\n[enrich] Row {sheet_row_num}: {company} (score={cell(C_SCORE)}, icp={icp})")

        # Contact enrichment — phone + website
        contact = contact_finder.ContactInfo()
        if not existing_phone or not existing_website:
            contact = contact_finder.lookup(company_name=company)
            time.sleep(0.5)

        # Use best available website — reject any data broker domains
        _bad_site_hints = {
            "zoominfo.com", "leadiq.com", "contactout.com", "pissedconsumer.com",
            "rocketreach.com", "rocketreach.co", "spokeo.com", "whitepages.com",
            "crunchbase.com", "dnb.com", "manta.com", "signalhire.com", "lusha.com",
        }
        def _is_bad_site(url: str) -> bool:
            return any(d in url for d in _bad_site_hints)

        def _strip_careers_subdomain(url: str) -> str:
            from urllib.parse import urlparse as _up2, urlunparse as _uu
            if not url:
                return url
            _p = _up2(url)
            _host = _p.netloc.lower()
            for _prefix in ("careers.", "jobs.", "hiring.", "apply.", "work."):
                if _host.startswith(_prefix):
                    return _uu((_p.scheme, _host[len(_prefix):], "/", "", "", ""))
            return url

        best_website = ""
        for candidate in [existing_website, contact.website]:
            if candidate and not _is_bad_site(candidate):
                best_website = _strip_careers_subdomain(candidate)
                break

        # Email/DM enrichment
        dm = email_finder.DecisionMaker()
        if not existing_email or not existing_dm_name:
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
            # Don't write known-bad website domains
            from urllib.parse import urlparse as _up
            _site_domain = _up(site_val).netloc.lower().replace("www.", "")
            if not any(d in _site_domain for d in _BAD_WEBSITE_DOMAINS):
                updates.append((sheet_row_num, C_WEBSITE, site_val))

        dm_name_val = dm.name or existing_dm_name
        if dm_name_val and dm_name_val != existing_dm_name:
            updates.append((sheet_row_num, C_DM_NAME, dm_name_val))

        dm_title_val = dm.title or cell(C_DM_TITLE)
        if dm_title_val and dm_title_val != cell(C_DM_TITLE):
            updates.append((sheet_row_num, C_DM_TITLE, dm_title_val))

        email_val = dm.email or existing_email
        if email_val and email_val != existing_email and email_val not in _BAD_EMAIL_BLOCKLIST:
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
