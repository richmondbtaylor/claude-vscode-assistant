"""Publish the finished list as one four-tab Google Sheet.

RULING C8: build_tabs reads its keeper rows (master and tier1) from
data/hooks.jsonl, the last file in the chain carrying every field the
tabs render. The Rejects tab is sourced from data/scored.jsonl instead,
because reject rows deliberately stop at the scoring stage and never
enter the enrichment chain.

Honesty requirements this module exists to enforce:
  - the score is a proxy, never revenue -- the Method tab says so plainly.
  - email_status and contact_email_status render whatever the row actually
    says; nothing here upgrades a guess to "verified".
  - every cell written to a tab is a primitive (str, int or float); a raw
    dict or list reaching a cell is a defect.
  - a blank cell is honest. Nothing here invents a value to fill a column.
"""
import datetime
import json
import pathlib

import config
import qa
from lib.records import read_jsonl

MASTER_HEADERS = ["Company", "Domain", "City", "State", "Phone", "Email",
                  "Email status", "Category", "Score", "Tier", "Signals", "Sources"]
TIER1_HEADERS = MASTER_HEADERS + ["Contact name", "Contact title", "Contact email",
                                  "Contact email status", "Hook"]
REJECT_HEADERS = ["Company", "City", "State", "Score", "Reason"]

SPREADSHEET_TITLE = "BOB Startup Leads — Master List"

# Auth note (task brief): the OAuth token at ~/.config/gspread/authorized_user.json
# is reused verbatim from bob-miami-150/upload_master.py, scopes included.
# A live read-only check (no spreadsheet created) showed drive.file alone
# 404s on the pre-existing bob-miami-150 reference file below -- drive.file
# only grants access to files this app itself created or opened, and that
# file was created by a different run. The plain "drive" scope is what
# actually resolves it, so all three scopes from the working script are
# kept rather than trimming to what the brief's prose names.
TOKEN_PATH = pathlib.Path.home() / ".config" / "gspread" / "authorized_user.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/drive"]
# Same Drive folder as the previous target lists (bob-miami-150).
FOLDER_REFERENCE_FILE_ID = "10jvPwa0maelE_oF5Fn5AmeKH-U8aZfy11r5OMnD3B0I"


def _signal_summary(row: dict) -> str:
    sig = row.get("signals", {})
    parts = []
    if sig.get("open_finance_req"):
        parts.append("open finance req")
    if sig.get("jobs_supported"):
        parts.append(f"{sig['jobs_supported']} jobs")
    if sig.get("loan_amount"):
        parts.append(f"SBA ${int(sig['loan_amount']):,}")
    if sig.get("headcount"):
        parts.append(f"{sig['headcount']} staff")
    if sig.get("reviews"):
        parts.append(f"{sig['reviews']} reviews")
    if sig.get("tech"):
        parts.append("+".join(sig["tech"]))
    if sig.get("marketplaces"):
        parts.append("/".join(sig["marketplaces"]))
    return ", ".join(parts)


def _master_cells(row: dict) -> list:
    return [row.get("name", ""), row.get("domain") or "", row.get("city", ""),
            row.get("state", ""), row.get("phone") or "", row.get("email") or "",
            row.get("email_status", "none"), row.get("category", ""),
            row.get("score", 0), row.get("tier", ""), _signal_summary(row),
            ", ".join(row.get("sources", []))]


def build_tabs(rows: list[dict], meta: dict) -> dict[str, list[list]]:
    """Build every tab as a list of primitive-only rows."""
    keepers = sorted([r for r in rows if r.get("tier") in ("master", "tier1")],
                     key=lambda r: r.get("score", 0), reverse=True)
    tier1 = [r for r in keepers if r.get("tier") == "tier1"]
    rejects = [r for r in rows if r.get("tier") == "reject"]

    method = [["Field", "Value"],
              ["Run date", meta.get("run_date", "")],
              ["Master rows", len(keepers)],
              ["Tier 1 rows", len(tier1)],
              ["Rejected rows", len(rejects)],
              ["Apify spend USD", meta.get("apify_spend", 0.0)],
              ["Hunter requests used", meta.get("hunter_used", 0)],
              ["Score note", "Score is a revenue proxy from public signals, "
                             "not reported revenue"]]
    for source, count in (meta.get("sources") or {}).items():
        method.append([f"Seed rows from {source}", count])

    return {
        "Master": [MASTER_HEADERS] + [_master_cells(r) for r in keepers],
        "Tier 1 Deep": [TIER1_HEADERS] + [
            _master_cells(r) + [r.get("contact_name", ""), r.get("contact_title", ""),
                                r.get("contact_email", ""),
                                r.get("contact_email_status", "none"),
                                r.get("hook", "")]
            for r in tier1],
        "Method and Sources": method,
        "Rejects": [REJECT_HEADERS] + [
            [r.get("name", ""), r.get("city", ""), r.get("state", ""),
             r.get("score", 0), r.get("reject_reason", "")] for r in rejects],
    }


def _lane_counts() -> dict[str, int]:
    """Real per-lane seed counts read off data/companies.jsonl, the deduped
    merge of every seed lane. Counted post-dedupe so a company sourced from
    two lanes is not double counted within either lane. A lane with no
    rows in this run (for example jobs, when that seed step produced
    nothing) is simply absent rather than reported as a made-up zero."""
    counts: dict[str, int] = {}
    for row in read_jsonl(config.DATA / "companies.jsonl"):
        for source in row.get("sources") or []:
            counts[source] = counts.get(source, 0) + 1
    return counts


def _compute_meta(keepers: list[dict]) -> dict:
    """Real, derivable numbers only. apify_spend and hunter_used are read
    off enrich_errors left on the rows by enrich_tier1.py's waterfall,
    which is the only record of what that stage actually did -- nothing
    here is estimated or recalled from memory.

    Apify's stub charges budget.charge(0.05) each time it records
    "apify: stub only, not wired" (enrich_tier1.py waterfall()), so
    counting that exact string reconstructs the real spend. Hunter's
    call attempts are counted the same way, from every "hunter:"-prefixed
    entry -- this counts attempts (successful and failed), the only trace
    left on the row; a hunter call that succeeded without incident and
    also failed to satisfy the row leaves no separate marker.
    """
    apify_spend = 0.0
    hunter_used = 0
    for row in keepers:
        for err in row.get("enrich_errors") or []:
            if err.startswith("apify: stub only, not wired"):
                apify_spend += 0.05
            elif err.startswith("hunter:"):
                hunter_used += 1

    return {
        "run_date": datetime.date.today().isoformat(),
        "apify_spend": round(apify_spend, 2),
        "hunter_used": hunter_used,
        "sources": _lane_counts(),
    }


def _load_credentials():
    """Verbatim credential block from bob-miami-150/upload_master.py.
    Never prints or logs the token contents."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    with open(TOKEN_PATH) as f:
        td = json.load(f)
    creds = Credentials(token=td.get("token"), refresh_token=td.get("refresh_token"),
                        token_uri=td.get("token_uri", "https://oauth2.googleapis.com/token"),
                        client_id=td.get("client_id"), client_secret=td.get("client_secret"),
                        scopes=SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def main():
    report_path = config.DATA / "qa_report.json"
    if not report_path.exists():
        raise SystemExit("data/qa_report.json is missing. Run `uv run qa.py` "
                         "before uploading.")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("failed", 1) > 0:
        raise SystemExit(f"QA gate failed on {report['failed']} rows. "
                         f"Fix or reject them before uploading.")

    keepers = [r for r in read_jsonl(config.DATA / "hooks.jsonl")
               if r.get("tier") in ("master", "tier1")]
    # Re-run the same gate qa.py ran so any tier1-to-master demotion
    # (RULING C7) is applied in memory the same way it was when
    # data/qa_report.json was written. hooks.jsonl on disk still shows
    # the pre-demotion tier; this reproduces the mutation rather than
    # trusting a stale on-disk value.
    qa.run_gates(keepers)
    rejects = [r for r in read_jsonl(config.DATA / "scored.jsonl")
               if r.get("tier") == "reject"]

    meta = _compute_meta(keepers)
    tabs = build_tabs(keepers + rejects, meta)

    from googleapiclient.discovery import build as build_service

    creds = _load_credentials()
    sheets = build_service("sheets", "v4", credentials=creds)
    drive = build_service("drive", "v3", credentials=creds)

    body = {"properties": {"title": SPREADSHEET_TITLE},
            "sheets": [{"properties": {"title": name}} for name in tabs]}
    spreadsheet = sheets.spreadsheets().create(
        body=body, fields="spreadsheetId,spreadsheetUrl,sheets.properties"
    ).execute()
    spreadsheet_id = spreadsheet["spreadsheetId"]

    parents = drive.files().get(
        fileId=FOLDER_REFERENCE_FILE_ID, fields="parents"
    ).execute().get("parents", [])
    if parents:
        current = drive.files().get(fileId=spreadsheet_id, fields="parents").execute()
        drive.files().update(
            fileId=spreadsheet_id, addParents=parents[0],
            removeParents=",".join(current.get("parents", [])),
            fields="id,parents",
        ).execute()

    for name, rows in tabs.items():
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"'{name}'!A1",
            valueInputOption="RAW", body={"values": rows},
        ).execute()

    freeze_requests = [
        {"updateSheetProperties": {
            "properties": {"sheetId": s["properties"]["sheetId"],
                           "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount"}}
        for s in spreadsheet["sheets"]
    ]
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": freeze_requests}
    ).execute()

    print("id:", spreadsheet_id)
    print("url:", spreadsheet.get("spreadsheetUrl"))


if __name__ == "__main__":
    main()
