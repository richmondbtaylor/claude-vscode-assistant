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

RULING C47: the Sheet discloses its own limitations. A blank column or an
empty tab must never be left for the reader to guess at. The Method tab
carries a fixed LIMITATIONS block (no Hunter key, dead LinkedIn, what
press hits actually measure, why hooks are blank by design, Apify never
wired) alongside the existing score-proxy note, and an empty Tier 1 Deep
tab gets a one-line note explaining why, derived from the real demotion
reason on the rows rather than assumed.

RULING C49: a figure on the Method tab must correspond to something that
actually happened. apify_spend is a constant 0.00 because the Apify step
never issues a real HTTP call, full stop. hunter_used counts only
enrich_errors entries that prove Hunter's API was actually reached; an
entry that only proves the call was blocked before it was ever attempted
(no key configured) is not counted, and is disclosed in words instead.
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

# RULING C47: the Sheet discloses its own limitations. These are known,
# permanent facts about this build, not run-specific numbers, so they are
# fixed rows rather than anything computed from meta. Written for someone
# opening the Sheet cold: plain sentences, no hedging, no marketing.
LIMITATIONS = [
    ["Limitation: email verification",
     "No Hunter API key is configured, so no email can be marked verified. "
     "Every address is generic, personal or guessed."],
    ["Limitation: headcount",
     "The LinkedIn session does not authenticate, so headcount is blank "
     "for every company."],
    ["Limitation: press hits",
     "Press hits count only third party coverage that names the company. "
     "This is near zero for small local businesses and is an honest "
     "measurement, not a gap."],
    ["Limitation: hooks",
     "Hooks are written only where a payment or accounting platform was "
     "detected. Blank elsewhere by design."],
    ["Limitation: Apify",
     "The Apify step is stubbed and not wired to a live actor. No HTTP "
     "call is ever made there, so Apify spend is always 0.00 in this "
     "build. The zero is structural, not a run that happened to spend "
     "nothing."],
]

SPREADSHEET_TITLE = "BOB Startup Leads - Master List"

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


def _tier1_empty_note(keepers: list[dict]) -> str:
    """One honest sentence explaining an empty Tier 1 Deep tab, derived
    from what actually happened to these rows rather than a fixed
    assumption. qa.run_gates() is the only thing that ever sets
    demoted_from_tier1, and only on a row it actually demoted (RULING
    C7), so this reads real state, not a guess. If several rows were
    demoted for different reasons, every distinct reason is listed."""
    demoted = [r for r in keepers if r.get("demoted_from_tier1")]
    if demoted:
        reasons = sorted({r["demoted_from_tier1"] for r in demoted})
        reason_text = "; ".join(reasons)
        return (f"No tier1 rows in this run. {len(demoted)} row(s) reached "
                f"tier1 during scoring but were demoted to master because: "
                f"{reason_text}. See the Method and Sources tab for why "
                f"contact enrichment is limited right now.")
    return ("No tier1 rows in this run. No row both cleared the tier1 "
            "score threshold and kept tier1 status through the QA gate.")


def build_tabs(rows: list[dict], meta: dict) -> dict[str, list[list]]:
    """Build every tab as a list of primitive-only rows."""
    keepers = sorted([r for r in rows if r.get("tier") in ("master", "tier1")],
                     key=lambda r: r.get("score", 0), reverse=True)
    tier1 = [r for r in keepers if r.get("tier") == "tier1"]
    rejects = [r for r in rows if r.get("tier") == "reject"]

    # RULING C49: a count or a dollar figure in this tab must correspond to
    # something that actually happened. hunter_used is 0 either way here,
    # but when that 0 is specifically because no API key is configured
    # (hunter_key_missing), say so in words rather than leaving a bare 0
    # that a reader could misread as "0 calls happened to be needed."
    hunter_used = meta.get("hunter_used", 0)
    hunter_value = hunter_used
    if meta.get("hunter_key_missing") and not hunter_used:
        hunter_value = "No Hunter API key configured, 0 calls made"

    method = [["Field", "Value"],
              ["Run date", meta.get("run_date", "")],
              ["Master rows", len(keepers)],
              ["Tier 1 rows", len(tier1)],
              ["Rejected rows", len(rejects)],
              ["Apify spend USD", meta.get("apify_spend", 0.0)],
              ["Hunter requests used", hunter_value],
              ["Score note", "Score is a revenue proxy from public signals, "
                             "not reported revenue"]]
    method.extend(LIMITATIONS)
    for source, count in (meta.get("sources") or {}).items():
        method.append([f"Seed rows from {source}", count])

    tier1_body = [
        _master_cells(r) + [r.get("contact_name", ""), r.get("contact_title", ""),
                            r.get("contact_email", ""),
                            r.get("contact_email_status", "none"),
                            r.get("hook", "")]
        for r in tier1
    ]
    if not tier1_body:
        tier1_body = [[_tier1_empty_note(keepers)]]

    return {
        "Master": [MASTER_HEADERS] + [_master_cells(r) for r in keepers],
        "Tier 1 Deep": [TIER1_HEADERS] + tier1_body,
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
    """Real, derivable numbers only -- and RULING C49: a number here must
    correspond to something that actually happened, never to an entry
    that only proves an attempt was made or could not be made at all.

    Apify's step 7 (enrich_tier1.py waterfall()) is fully stubbed: no
    apify-client import, no HTTP call, ever. "apify: stub only, not
    wired" is bookkeeping against the local Budget object only, not a
    record of money leaving anyone's account. There is no marker in this
    codebase that could ever mean a real Apify call happened, so
    apify_spend is a constant 0.00, not something counted off a marker
    that misrepresents its own meaning.

    Hunter is different: hunter_domain_search() (enrich_tier1.py) really
    does call httpx.get() against Hunter's API, so a real call CAN
    happen and CAN fail after actually reaching the network. But
    hunter_domain_search() also calls _key("HUNTER_API_KEY") to build
    its params, and _key() raises RuntimeError synchronously, before
    httpx.get() ever runs, when no key is configured. So a "hunter:
    RuntimeError" entry in enrich_errors is proof a call was blocked
    before it was ever issued; any other "hunter:"-prefixed entry (an
    HTTP status, a connection error, a timeout) can only exist after
    httpx.get() actually ran, which is proof a real call was made. Only
    the second kind is counted. hunter_key_missing is set when at least
    one RuntimeError entry is seen, so callers can render "no key
    configured" instead of a bare 0 that could be misread as "zero calls
    happened to be needed."
    """
    hunter_used = 0
    hunter_key_missing = False
    for row in keepers:
        for err in row.get("enrich_errors") or []:
            if not err.startswith("hunter:"):
                continue
            reason = err.split(":", 1)[1].strip()
            if reason == "RuntimeError":
                hunter_key_missing = True
            else:
                hunter_used += 1

    return {
        "run_date": datetime.date.today().isoformat(),
        "apify_spend": 0.0,
        "hunter_used": hunter_used,
        "hunter_key_missing": hunter_key_missing,
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
