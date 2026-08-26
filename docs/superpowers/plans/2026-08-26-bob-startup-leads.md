# BOB Startup Lead Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a Google Sheet of roughly 1,000 US small businesses that are plausibly past $500K revenue, scored 0-100, with the top 20% carrying a named decision-maker, a verified email and a one-line outreach hook for BOB.

**Architecture:** Three seed lanes (SBA loan data, finance-hire job posts, Google Maps) write JSONL into `data/`. A dedupe pass merges them into one company record per business. A scrape pass adds contact data and a payment-tech fingerprint, a signals pass adds scale and intent evidence, a scorer ranks 0-100 and assigns tiers, a cost-ordered waterfall deep-enriches Tier 1, and a QA gate blocks upload until the contactability and name-validation rules pass.

**Tech Stack:** Python 3.11+ run through `uv` with PEP 723 inline dependency headers. `httpx` for HTTP, `beautifulsoup4` for parsing, `playwright` (sync API) for Maps and LinkedIn, `rapidfuzz` for name matching, `pytest` for tests, `google-api-python-client` for Sheets.

**Spec:** `docs/superpowers/specs/2026-08-26-bob-startup-leads-design.md`

## Global Constraints

Every task's requirements implicitly include this section.

- **Project root:** `~/.claude/bob-startup-leads/`. All paths below are relative to it.
- **Python:** run every script with `uv run <script>.py`. Each script carries a PEP 723 header. Never `pip install`, never `python -m venv`, never `python -m pip`.
- **Apify:** last-resort layer only. Cheap actors only (`code_crafter~leads-finder`), small `fetch_count` (10 to 25). Hard ceiling $10 total for this build. Print the estimated dollar cost before any run.
- **Paid API quota:** check remaining Hunter and Apollo credits before the Tier 1 pass and size the batch to fit. Never assume unlimited.
- **Volume:** about 1,000 rows on Master; top 20% by score becomes Tier 1.
- **Geography:** US-wide. Vertical-agnostic, not restricted to BOB's launch cohort.
- **Contactability gate:** every Master row carries an email or a phone. No exceptions.
- **Name validation:** contact and officer names must pass strict validation. Discard on failure rather than shipping uncertain. The prior Miami build shipped junk like "Get Ah" and "Fort Lauderdale" from a loose regex.
- **Email labelling:** every email is marked `verified`, `guessed`, `generic` or `none`. Guessed is never presented as verified.
- **Liveness:** any PPP-sourced row is confirmed still trading before reaching Master.
- **Copy rules for hooks:** no em dashes anywhere, no AI-tell vocabulary, no mirrored two-beat constructions, no invented acronyms. Voice is laconic and plain.
- **Out of scope:** no sending, no Attio push, no scheduled refresh. Phone numbers are list-only.
- **Credentials:** Google Sheets OAuth token at `~/.config/gspread/authorized_user.json`. API keys live in `~/.claude/security/*.env` (`APIFY_API_TOKEN`, `APOLLO_API_KEY`, `HUNTER_API_KEY`, `BRAVE_API_KEY`). Load them, never hardcode them, never print them.

## File Structure

| File | Responsibility |
|---|---|
| `config.py` | metros, job-title basket, Maps category basket, score weights, thresholds, data paths |
| `lib/records.py` | company record schema, JSONL read and write, id assignment |
| `lib/normalize.py` | name, phone, domain and address normalization; person-name validation |
| `seed_sba.py` | Lane 2b: stream SBA 7(a) and PPP CSVs into seed records |
| `seed_jobs.py` | Lane 1: finance and admin job posts via Brave ATS dorks and Playwright |
| `seed_maps.py` | Lane 2a: Google Maps sweep |
| `resolve_domain.py` | find a website for seed rows that arrived without one |
| `dedupe.py` | merge all seeds into one record per company |
| `site_scrape.py` | contact data, JSON-LD, payment-tech fingerprint |
| `signals.py` | headcount, reviews, registry age, press |
| `score.py` | 0-100 scoring, floor, rank, tier assignment |
| `enrich_tier1.py` | cost-ordered waterfall to named contact and verified email |
| `hooks.py` | one-line outreach angle per Tier 1 row |
| `qa.py` | gates and hand-review sample |
| `upload_sheet.py` | four-tab Google Sheet |
| `tests/` | pytest suite, one file per module above |

---

### Task 1: Scaffold, config and shared library

**Files:**
- Create: `lib/normalize.py`
- Create: `lib/records.py`
- Create: `config.py`
- Test: `tests/test_normalize.py`
- Test: `tests/test_records.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `normalize.norm_name(s: str) -> str`
  - `normalize.norm_phone(s: str | None) -> str | None` (E.164, US)
  - `normalize.registrable_domain(url: str | None) -> str | None`
  - `normalize.is_valid_person_name(s: str) -> bool`
  - `records.company_id(name: str, state: str, domain: str | None) -> str`
  - `records.read_jsonl(path) -> Iterator[dict]`
  - `records.write_jsonl(path, rows: Iterable[dict]) -> int`
  - `config.DATA`, `config.METROS`, `config.JOB_TITLES`, `config.MAPS_CATEGORIES`, `config.WEIGHTS`, `config.SCORE_FLOOR`, `config.TIER1_FRACTION`

- [ ] **Step 1: Write the failing tests for normalize**

```python
# tests/test_normalize.py
import pytest
from lib.normalize import norm_name, norm_phone, registrable_domain, is_valid_person_name


@pytest.mark.parametrize("raw,expected", [
    ("Sumter Coatings, Inc.", "sumter coatings"),
    ("AMERIPRO CONSTRUCTION SERVICES, INC.", "ameripro construction services"),
    ("Castillo Smart Services LLC", "castillo smart services"),
    ("Bob's Plumbing & Heating Co.", "bobs plumbing and heating"),
    ("  Acme   PLLC  ", "acme"),
])
def test_norm_name_strips_suffixes_and_punctuation(raw, expected):
    assert norm_name(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("(786) 395-8578", "+17863958578"),
    ("786-395-8578", "+17863958578"),
    ("+1 786 395 8578", "+17863958578"),
    ("17863958578", "+17863958578"),
    ("555", None),
    (None, None),
    ("", None),
])
def test_norm_phone_to_e164(raw, expected):
    assert norm_phone(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("https://www.acmeplumbing.com/contact", "acmeplumbing.com"),
    ("http://acmeplumbing.com", "acmeplumbing.com"),
    ("https://shop.acmeplumbing.co.uk/x", "acmeplumbing.co.uk"),
    ("acmeplumbing.com", "acmeplumbing.com"),
    ("https://facebook.com/acme", None),
    (None, None),
])
def test_registrable_domain(raw, expected):
    assert registrable_domain(raw) == expected


@pytest.mark.parametrize("raw", [
    "Maria Gonzalez", "John O'Brien", "Jean-Luc Picard", "Ann Lee",
])
def test_valid_person_names_accepted(raw):
    assert is_valid_person_name(raw) is True


@pytest.mark.parametrize("raw", [
    "Get Ah", "Fort Lauderdale", "Contact Us", "Our Team", "Free Estimate",
    "X", "", "ACME PLUMBING LLC", "Learn More", "Read More", "Miami Beach",
])
def test_junk_names_rejected(raw):
    assert is_valid_person_name(raw) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/.claude/bob-startup-leads && uv run pytest tests/test_normalize.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib'`

- [ ] **Step 3: Implement `lib/normalize.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["tldextract"]
# ///
"""Normalization and validation shared across every pipeline stage."""
import re

import tldextract

LEGAL_SUFFIXES = {
    "llc", "l.l.c", "inc", "incorporated", "corp", "corporation", "co",
    "ltd", "limited", "pllc", "pc", "pa", "lp", "llp", "plc", "company",
}
_PUNCT = re.compile(r"[^a-z0-9&\s]")
_WS = re.compile(r"\s+")

# Social and directory hosts are never a company's own domain.
NON_COMPANY_HOSTS = {
    "facebook", "instagram", "linkedin", "twitter", "x", "yelp", "google",
    "youtube", "tiktok", "nextdoor", "bbb", "angi", "homeadvisor", "thumbtack",
    "indeed", "glassdoor", "mapquest", "yellowpages", "manta", "bizapedia",
}


def norm_name(s: str) -> str:
    """Lowercase, drop punctuation and legal suffixes, collapse whitespace."""
    if not s:
        return ""
    out = s.lower().replace("&", " and ")
    out = _PUNCT.sub(" ", out)
    tokens = [t for t in _WS.sub(" ", out).strip().split(" ") if t]
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def norm_phone(s: str | None) -> str | None:
    """Return a US number as E.164, or None if it is not a plausible US number."""
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    if digits[0] in "01" or digits[3] in "01":
        return None
    return "+1" + digits


def registrable_domain(url: str | None) -> str | None:
    """Registrable domain for a company site, or None for social and directory hosts."""
    if not url:
        return None
    candidate = url if "//" in url else "https://" + url
    ext = tldextract.extract(candidate)
    if not ext.domain or not ext.suffix:
        return None
    if ext.domain.lower() in NON_COMPANY_HOSTS:
        return None
    return f"{ext.domain}.{ext.suffix}".lower()


# A person name is two to four capitalized tokens, no company or CTA words.
_NAME_TOKEN = r"[A-Z][a-z'’-]{1,}"
_NAME_RE = re.compile(rf"^{_NAME_TOKEN}(?:\s+(?:[A-Z]\.|{_NAME_TOKEN})){{1,3}}$")

NAME_STOPWORDS = {
    "contact", "team", "about", "our", "us", "free", "estimate", "learn",
    "more", "read", "get", "call", "now", "click", "here", "home", "services",
    "service", "quote", "schedule", "book", "menu", "view", "see", "start",
    "welcome", "meet", "the", "your", "we", "why", "how", "beach", "city",
    "county", "fort", "north", "south", "east", "west", "saint", "lake",
}


def is_valid_person_name(s: str) -> bool:
    """True only for something that really looks like a person's name."""
    if not s or not _NAME_RE.match(s.strip()):
        return False
    tokens = [t.lower().strip(".") for t in s.split()]
    if any(t in NAME_STOPWORDS for t in tokens):
        return False
    if any(t in LEGAL_SUFFIXES for t in tokens):
        return False
    return True
```

- [ ] **Step 4: Run normalize tests to verify they pass**

Run: `uv run pytest tests/test_normalize.py -v`
Expected: PASS, 27 tests

Note: `test_junk_names_rejected` includes `"Fort Lauderdale"` and `"Miami Beach"`, which are caught by the city stopwords (`fort`, `beach`). If a real contact is ever rejected for this reason, that is the intended trade: discard rather than ship uncertain.

- [ ] **Step 5: Write the failing tests for records**

```python
# tests/test_records.py
from lib.records import company_id, read_jsonl, write_jsonl


def test_company_id_is_stable_for_same_domain():
    a = company_id("Acme Plumbing LLC", "FL", "acmeplumbing.com")
    b = company_id("ACME PLUMBING, INC.", "FL", "acmeplumbing.com")
    assert a == b


def test_company_id_differs_across_states_without_domain():
    a = company_id("Acme Plumbing", "FL", None)
    b = company_id("Acme Plumbing", "TX", None)
    assert a != b


def test_jsonl_roundtrip(tmp_path):
    path = tmp_path / "out.jsonl"
    rows = [{"name": "A", "n": 1}, {"name": "B", "n": 2}]
    assert write_jsonl(path, rows) == 2
    assert list(read_jsonl(path)) == rows


def test_read_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "out.jsonl"
    path.write_text('{"a":1}\n\n{"a":2}\n', encoding="utf-8")
    assert list(read_jsonl(path)) == [{"a": 1}, {"a": 2}]
```

- [ ] **Step 6: Run records tests to verify they fail**

Run: `uv run pytest tests/test_records.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib.records'`

- [ ] **Step 7: Implement `lib/records.py`**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""Company record identity and JSONL persistence."""
import hashlib
import json
import pathlib
from typing import Iterable, Iterator

from lib.normalize import norm_name

# Canonical company record keys. Every stage reads and writes this shape.
FIELDS = (
    "company_id", "name", "domain", "website", "phone", "email",
    "email_status", "address", "city", "state", "zip", "naics",
    "category", "sources", "signals", "score", "tier",
)


def company_id(name: str, state: str, domain: str | None) -> str:
    """Stable id. Domain wins when present, otherwise normalized name plus state."""
    key = domain.lower() if domain else f"{norm_name(name)}|{(state or '').upper()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def read_jsonl(path) -> Iterator[dict]:
    p = pathlib.Path(path)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path, rows: Iterable[dict]) -> int:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n
```

- [ ] **Step 8: Run records tests to verify they pass**

Run: `uv run pytest tests/test_records.py -v`
Expected: PASS, 4 tests

- [ ] **Step 9: Write `config.py`**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""Tunable parameters for the whole pipeline. Nothing here does work."""
import pathlib

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"

# Lane 2a sweep grid. 25 metros chosen for population and Maps density.
METROS = [
    "New York NY", "Los Angeles CA", "Chicago IL", "Dallas TX", "Houston TX",
    "Atlanta GA", "Miami FL", "Phoenix AZ", "Philadelphia PA", "Boston MA",
    "Seattle WA", "Denver CO", "Charlotte NC", "Nashville TN", "Austin TX",
    "Tampa FL", "Orlando FL", "San Diego CA", "Minneapolis MN", "Detroit MI",
    "Portland OR", "Las Vegas NV", "Kansas City MO", "Columbus OH", "Raleigh NC",
]

# Vertical-agnostic basket. Chosen for businesses where real money moves
# through vendor bills, payroll and card spend.
MAPS_CATEGORIES = [
    "roofing contractor", "hvac contractor", "plumber", "electrician",
    "general contractor", "landscaping company", "pest control service",
    "concrete contractor", "painting contractor", "auto repair shop",
    "commercial cleaning service", "moving company", "medical spa",
    "dental clinic", "veterinary clinic", "physical therapy clinic",
    "marketing agency", "law firm", "accounting firm", "staffing agency",
    "printing company", "machine shop", "wholesale distributor",
    "catering company", "security system installer",
]

# Lane 1 intent basket. A paid hire in any of these implies real payroll.
JOB_TITLES = [
    "bookkeeper", "staff accountant", "controller", "accounts payable",
    "accounts receivable", "office manager", "billing specialist",
    "business manager",
]

ATS_HOSTS = [
    "boards.greenhouse.io", "jobs.lever.co", "apply.workable.com",
    "jobs.ashbyhq.com", "jobs.smartrecruiters.com",
]

# Score weights per family. Must sum to 100.
WEIGHTS = {"money": 40, "scale": 25, "signal": 25, "reach": 10}

# A company must clear this to reach Master, and must have evidence in at
# least this many families, so review count alone can never qualify anyone.
SCORE_FLOOR = 35
MIN_FAMILIES = 2

TIER1_FRACTION = 0.20
TARGET_MASTER_ROWS = 1000

# SBA sources, verified live 2026-08-26.
SBA_7A_URL = ("https://data.sba.gov/sites/default/files/uploaded_resources/"
              "FOIA_7a_FY2020_Present_asof_260630.csv")
PPP_150K_URL = ("https://data.sba.gov/sites/default/files/distribution/"
                "SBA-OCA-2022-07-001/public_150k_plus_240930.csv")

# Revenue-proxy floors for SBA rows.
MIN_JOBS_SUPPORTED = 5
MIN_GROSS_APPROVAL = 150_000

APIFY_BUDGET_USD = 10.0
```

- [ ] **Step 10: Commit**

```bash
cd ~/.claude/bob-startup-leads
git add lib/ config.py tests/test_normalize.py tests/test_records.py
git commit -m "feat: normalization, record identity and pipeline config"
```

---

### Task 2: SBA seed lane

**Files:**
- Create: `seed_sba.py`
- Test: `tests/test_seed_sba.py`

**Interfaces:**
- Consumes: `config.SBA_7A_URL`, `config.PPP_150K_URL`, `config.MIN_JOBS_SUPPORTED`, `config.MIN_GROSS_APPROVAL`, `normalize.norm_phone`, `records.company_id`, `records.write_jsonl`
- Produces:
  - `seed_sba.row_from_7a(row: dict) -> dict | None`
  - `seed_sba.row_from_ppp(row: dict) -> dict | None`
  - `data/seed_sba.jsonl`

**Why this lane matters:** SBA 7(a) FY2020-Present is current to 2026-06-30 and names businesses that a bank underwrote, with `JobsSupported` and `GrossApproval` attached. That is the closest thing to free national revenue evidence. The file is 181 MB, so it must be streamed, never loaded whole.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_seed_sba.py
from seed_sba import row_from_7a, row_from_ppp

SEVEN_A = {
    "BorrName": "AMERIPRO CONSTRUCTION SERVICES, INC.",
    "BorrStreet": "1403 SENTRY LANE", "BorrCity": "Norristown",
    "BorrState": "PA", "BorrZip": "19403", "GrossApproval": "450000.0",
    "JobsSupported": "12", "NaicsCode": "236220",
    "NaicsDescription": "Commercial Building Construction",
    "LoanStatus": "NOT PIF", "ApprovalFY": "2024", "BusinessAge": "Existing",
}

PPP = {
    "BorrowerName": "SUMTER COATINGS, INC.", "BorrowerAddress": "2410 Highway 15 South",
    "BorrowerCity": "Sumter", "BorrowerState": "SC", "BorrowerZip": "29150-9662",
    "InitialApprovalAmount": "769358.78", "JobsReported": "62",
    "NAICSCode": "325510", "LoanStatus": "Paid in Full",
}


def test_7a_row_maps_core_fields():
    out = row_from_7a(SEVEN_A)
    assert out["name"] == "AMERIPRO CONSTRUCTION SERVICES, INC."
    assert out["state"] == "PA"
    assert out["city"] == "Norristown"
    assert out["naics"] == "236220"
    assert out["sources"] == ["sba_7a"]
    assert out["signals"]["jobs_supported"] == 12
    assert out["signals"]["loan_amount"] == 450000.0
    assert out["domain"] is None


def test_7a_row_rejected_below_jobs_floor():
    small = dict(SEVEN_A, JobsSupported="2")
    assert row_from_7a(small) is None


def test_7a_row_rejected_below_amount_floor():
    small = dict(SEVEN_A, GrossApproval="40000.0", JobsSupported="12")
    assert row_from_7a(small) is None


def test_7a_row_rejected_when_charged_off():
    dead = dict(SEVEN_A, LoanStatus="CHGOFF")
    assert row_from_7a(dead) is None


def test_7a_row_rejected_for_stale_approval_year():
    old = dict(SEVEN_A, ApprovalFY="2020")
    assert row_from_7a(old) is None


def test_ppp_row_flagged_for_liveness_check():
    out = row_from_ppp(PPP)
    assert out["sources"] == ["ppp"]
    assert out["signals"]["needs_liveness_check"] is True
    assert out["signals"]["jobs_supported"] == 62


def test_malformed_numbers_do_not_raise():
    assert row_from_7a(dict(SEVEN_A, JobsSupported="")) is None
    assert row_from_7a(dict(SEVEN_A, GrossApproval="N/A")) is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_seed_sba.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seed_sba'`

- [ ] **Step 3: Implement `seed_sba.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "tldextract"]
# ///
"""Lane 2b: seed companies from SBA 7(a) and PPP loan data.

Streams the CSVs rather than downloading them whole. The 7(a) file is 181 MB.
"""
import argparse
import csv
import io

import httpx

import config
from lib.records import company_id, write_jsonl

# 7(a) loans that were charged off or cancelled are not evidence of a going concern.
DEAD_7A_STATUS = {"CHGOFF", "CANCLD", "EXEMPT"}
MIN_APPROVAL_FY = 2022


def _num(value, cast=float):
    try:
        return cast(str(value).strip())
    except (TypeError, ValueError):
        return None


def row_from_7a(row: dict) -> dict | None:
    """Map one 7(a) CSV row to a seed record, or None if it fails the floors."""
    if (row.get("LoanStatus") or "").strip().upper() in DEAD_7A_STATUS:
        return None
    fy = _num(row.get("ApprovalFY"), int)
    if fy is None or fy < MIN_APPROVAL_FY:
        return None
    jobs = _num(row.get("JobsSupported"), int)
    amount = _num(row.get("GrossApproval"))
    if jobs is None or jobs < config.MIN_JOBS_SUPPORTED:
        return None
    if amount is None or amount < config.MIN_GROSS_APPROVAL:
        return None

    name = (row.get("BorrName") or "").strip()
    state = (row.get("BorrState") or "").strip().upper()
    if not name or not state:
        return None

    return {
        "company_id": company_id(name, state, None),
        "name": name,
        "domain": None,
        "website": None,
        "phone": None,
        "email": None,
        "email_status": "none",
        "address": (row.get("BorrStreet") or "").strip(),
        "city": (row.get("BorrCity") or "").strip(),
        "state": state,
        "zip": (row.get("BorrZip") or "").strip()[:5],
        "naics": (row.get("NaicsCode") or "").strip(),
        "category": (row.get("NaicsDescription") or "").strip(),
        "sources": ["sba_7a"],
        "signals": {
            "jobs_supported": jobs,
            "loan_amount": amount,
            "loan_fy": fy,
            "business_age": (row.get("BusinessAge") or "").strip(),
            "needs_liveness_check": False,
        },
    }


def row_from_ppp(row: dict) -> dict | None:
    """Map one PPP 150k+ row to a seed record. Always flagged for liveness."""
    jobs = _num(row.get("JobsReported"), int)
    amount = _num(row.get("InitialApprovalAmount"))
    if jobs is None or jobs < config.MIN_JOBS_SUPPORTED:
        return None
    if amount is None or amount < config.MIN_GROSS_APPROVAL:
        return None

    name = (row.get("BorrowerName") or "").strip()
    state = (row.get("BorrowerState") or "").strip().upper()
    if not name or not state:
        return None

    return {
        "company_id": company_id(name, state, None),
        "name": name,
        "domain": None,
        "website": None,
        "phone": None,
        "email": None,
        "email_status": "none",
        "address": (row.get("BorrowerAddress") or "").strip(),
        "city": (row.get("BorrowerCity") or "").strip(),
        "state": state,
        "zip": (row.get("BorrowerZip") or "").strip()[:5],
        "naics": (row.get("NAICSCode") or "").strip(),
        "category": "",
        "sources": ["ppp"],
        "signals": {
            "jobs_supported": jobs,
            "loan_amount": amount,
            "needs_liveness_check": True,
        },
    }


def stream_csv(url: str, mapper, limit: int):
    """Stream a remote CSV and yield mapped rows until limit is reached."""
    kept = 0
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0"}) as resp:
        resp.raise_for_status()
        buf = io.StringIO()
        reader = None
        for chunk in resp.iter_text():
            buf.write(chunk)
            buf.seek(0)
            lines = buf.getvalue().split("\n")
            buf = io.StringIO()
            buf.write(lines.pop())  # keep the partial last line
            if reader is None and lines:
                reader = csv.DictReader([lines.pop(0)])
                header = reader.fieldnames
            if reader is None:
                continue
            for parsed in csv.DictReader(lines, fieldnames=header):
                out = mapper(parsed)
                if out:
                    yield out
                    kept += 1
                    if kept >= limit:
                        return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-7a", type=int, default=4000)
    ap.add_argument("--limit-ppp", type=int, default=1000)
    args = ap.parse_args()

    rows = list(stream_csv(config.SBA_7A_URL, row_from_7a, args.limit_7a))
    print(f"7(a): {len(rows)} rows kept")
    ppp = list(stream_csv(config.PPP_150K_URL, row_from_ppp, args.limit_ppp))
    print(f"PPP: {len(ppp)} rows kept")

    n = write_jsonl(config.DATA / "seed_sba.jsonl", rows + ppp)
    print(f"wrote {n} rows to data/seed_sba.jsonl")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_seed_sba.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Run the real seed against a small limit and eyeball it**

Run: `uv run seed_sba.py --limit-7a 200 --limit-ppp 50`
Expected: `data/seed_sba.jsonl` with 250 rows. Open the first 5 and confirm the names look like real businesses and the states are populated. If the stream parser mangles quoted fields containing commas (several `BorrName` values do, for example `"AMERIPRO CONSTRUCTION SERVICES, INC."`), fix the chunk boundary handling before continuing.

- [ ] **Step 6: Commit**

```bash
git add seed_sba.py tests/test_seed_sba.py
git commit -m "feat: SBA 7(a) and PPP seed lane with revenue-proxy floors"
```

---

### Task 3: Job-signal seed lane

**Files:**
- Create: `seed_jobs.py`
- Test: `tests/test_seed_jobs.py`

**Interfaces:**
- Consumes: `config.JOB_TITLES`, `config.ATS_HOSTS`, `normalize.registrable_domain`, `records.company_id`, `records.write_jsonl`
- Produces:
  - `seed_jobs.brave_search(query: str, count: int = 20) -> list[dict]`
  - `seed_jobs.parse_ats_result(result: dict) -> dict | None`
  - `data/seed_jobs.jsonl`

**Why this lane matters:** BOB's own GTM material names the bookkeeper job posting as the single best outbound trigger. A company paying for a finance hire is past $500K, and the requisition is the outreach hook. Every row here carries `signals.open_finance_req = True`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_seed_jobs.py
from seed_jobs import parse_ats_result

GREENHOUSE = {
    "title": "Bookkeeper at Rivera Mechanical",
    "url": "https://boards.greenhouse.io/riveramechanical/jobs/4212",
    "description": "Rivera Mechanical is hiring a full-time Bookkeeper in Austin, TX.",
}
LEVER = {
    "title": "Controller - Summit Roofing Group",
    "url": "https://jobs.lever.co/summitroofing/8a2c",
    "description": "Summit Roofing Group seeks a Controller.",
}
NOISE = {
    "title": "Bookkeeper jobs in Texas | Indeed.com",
    "url": "https://www.indeed.com/q-bookkeeper-l-texas-jobs.html",
    "description": "Browse 1,204 bookkeeper jobs.",
}


def test_greenhouse_result_yields_company_slug():
    out = parse_ats_result(GREENHOUSE)
    assert out["name"] == "Riveramechanical"
    assert out["signals"]["open_finance_req"] is True
    assert out["signals"]["job_title"] == "Bookkeeper at Rivera Mechanical"
    assert out["signals"]["job_url"].startswith("https://boards.greenhouse.io/")
    assert out["sources"] == ["jobs"]


def test_lever_result_yields_company_slug():
    out = parse_ats_result(LEVER)
    assert out["name"] == "Summitroofing"


def test_aggregator_result_rejected():
    assert parse_ats_result(NOISE) is None


def test_result_without_company_path_rejected():
    bare = dict(GREENHOUSE, url="https://boards.greenhouse.io/")
    assert parse_ats_result(bare) is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_seed_jobs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seed_jobs'`

- [ ] **Step 3: Implement `seed_jobs.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "tldextract"]
# ///
"""Lane 1: companies with an open finance or admin requisition.

Primary source is Brave Search against public ATS boards. Those pages are
static and unauthenticated and they name the employer in the URL path.
"""
import argparse
import os
import pathlib
import time
from urllib.parse import urlparse

import httpx

import config
from lib.records import company_id, write_jsonl

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
ENV_PATH = pathlib.Path.home() / ".claude" / "security" / "bishop-research-agent.env"

# The employer slug is the first path segment on each ATS host.
ATS_SLUG_INDEX = {
    "boards.greenhouse.io": 0,
    "jobs.lever.co": 0,
    "apply.workable.com": 0,
    "jobs.ashbyhq.com": 0,
    "jobs.smartrecruiters.com": 0,
}


def _brave_key() -> str:
    key = os.environ.get("BRAVE_API_KEY")
    if key:
        return key
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("BRAVE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("BRAVE_API_KEY not found in env or security env file")


def brave_search(query: str, count: int = 20) -> list[dict]:
    """Return Brave web results as dicts with title, url and description."""
    resp = httpx.get(
        BRAVE_ENDPOINT,
        params={"q": query, "count": count, "country": "us"},
        headers={"X-Subscription-Token": _brave_key(), "Accept": "application/json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""),
         "description": r.get("description", "")}
        for r in resp.json().get("web", {}).get("results", [])
    ]


def parse_ats_result(result: dict) -> dict | None:
    """Turn one ATS search result into a seed record, or None if it is noise."""
    url = result.get("url") or ""
    host = urlparse(url).netloc.lower()
    if host not in ATS_SLUG_INDEX:
        return None
    parts = [p for p in urlparse(url).path.split("/") if p]
    idx = ATS_SLUG_INDEX[host]
    if len(parts) <= idx:
        return None
    slug = parts[idx]
    name = slug.replace("-", " ").replace("_", " ").strip().title().replace(" ", "")
    if not name or len(name) < 3:
        return None

    return {
        "company_id": company_id(name, "", None),
        "name": name,
        "domain": None,
        "website": None,
        "phone": None,
        "email": None,
        "email_status": "none",
        "address": "", "city": "", "state": "", "zip": "",
        "naics": "", "category": "",
        "sources": ["jobs"],
        "signals": {
            "open_finance_req": True,
            "job_title": result.get("title", ""),
            "job_url": url,
            "job_blurb": result.get("description", ""),
            "needs_liveness_check": False,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=20)
    args = ap.parse_args()

    rows, seen = [], set()
    for title in config.JOB_TITLES:
        for host in config.ATS_HOSTS:
            query = f'site:{host} "{title}"'
            try:
                results = brave_search(query, args.per_query)
            except httpx.HTTPError as exc:
                print(f"skip {query}: {exc}")
                continue
            for r in results:
                row = parse_ats_result(r)
                if row and row["company_id"] not in seen:
                    seen.add(row["company_id"])
                    rows.append(row)
            print(f"{query}: {len(rows)} total")
            time.sleep(1.1)  # Brave free tier is rate limited to about 1 qps

    n = write_jsonl(config.DATA / "seed_jobs.jsonl", rows)
    print(f"wrote {n} rows to data/seed_jobs.jsonl")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_seed_jobs.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Run one live query to confirm the Brave key and quota work**

Run: `uv run python -c "import seed_jobs; print(len(seed_jobs.brave_search('site:boards.greenhouse.io \"bookkeeper\"', 5)))"`
Expected: a small integer greater than 0. If this returns 401 or 429, stop and report the Brave quota state rather than proceeding to the full sweep.

- [ ] **Step 6: Commit**

```bash
git add seed_jobs.py tests/test_seed_jobs.py
git commit -m "feat: job-signal seed lane via Brave ATS dorks"
```

---

### Task 4: Google Maps seed lane

**Files:**
- Create: `seed_maps.py` (port of `~/.claude/bob-miami-150/maps_scrape.py`)
- Test: `tests/test_seed_maps.py`

**Interfaces:**
- Consumes: `config.METROS`, `config.MAPS_CATEGORIES`, `normalize.norm_phone`, `normalize.registrable_domain`, `records.company_id`, `records.write_jsonl`
- Produces:
  - `seed_maps.place_to_record(place: dict, query: str, city: str) -> dict | None`
  - `data/seed_maps.jsonl`

**Port note:** `bob-miami-150/maps_scrape.py` already works at scale (2,669 clean records). Copy it, then change three things: swap the hardcoded `DADE`/`BROWARD` city lists for `config.METROS`, swap the `BATCHES` query dict for `config.MAPS_CATEGORIES`, and pipe every scraped place through the new `place_to_record` so the output matches the canonical record shape instead of the old `firms_raw.jsonl` shape. Keep its `seen_ids.json` resume behaviour and its scroll and sleep pacing exactly as they are.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_seed_maps.py
from seed_maps import place_to_record

PLACE = {
    "name": "Castillo Smart Services LLC",
    "phone": "+17863958578",
    "website": "https://castillosmart.com/",
    "address": "20350 S Dixie Hwy Suite 202, Cutler Bay, FL 33189",
    "category": "Tax preparation service",
    "rating": 5.0,
    "reviews": 64,
    "fid": "0x88d9c3bfcfd1779f:0xd76c7e2bc2664dd4",
}


def test_place_maps_to_canonical_record():
    out = place_to_record(PLACE, "bookkeeping service", "Miami FL")
    assert out["name"] == "Castillo Smart Services LLC"
    assert out["phone"] == "+17863958578"
    assert out["domain"] == "castillosmart.com"
    assert out["state"] == "FL"
    assert out["zip"] == "33189"
    assert out["signals"]["reviews"] == 64
    assert out["sources"] == ["maps"]


def test_place_without_phone_or_site_is_rejected():
    bare = dict(PLACE, phone=None, website=None)
    assert place_to_record(bare, "q", "Miami FL") is None


def test_social_url_does_not_become_domain():
    social = dict(PLACE, website="https://facebook.com/castillo")
    out = place_to_record(social, "q", "Miami FL")
    assert out["domain"] is None
    assert out["phone"] == "+17863958578"


def test_address_without_parseable_state_still_records():
    odd = dict(PLACE, address="20350 S Dixie Hwy")
    out = place_to_record(odd, "q", "Miami FL")
    assert out["state"] == "FL"  # falls back to the search city
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_seed_maps.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seed_maps'`

- [ ] **Step 3: Implement `place_to_record` in `seed_maps.py`**

```python
import re

from lib.normalize import norm_phone, registrable_domain
from lib.records import company_id

# "20350 S Dixie Hwy Suite 202, Cutler Bay, FL 33189"
_ADDR_TAIL = re.compile(r",\s*([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5})")


def place_to_record(place: dict, query: str, city: str) -> dict | None:
    """Map one scraped Maps place to the canonical record shape."""
    phone = norm_phone(place.get("phone"))
    domain = registrable_domain(place.get("website"))
    if not phone and not domain:
        return None  # unreachable, no point carrying it

    name = (place.get("name") or "").strip()
    if not name:
        return None

    addr = place.get("address") or ""
    match = _ADDR_TAIL.search(addr)
    if match:
        city_out, state, zip_out = match.group(1), match.group(2), match.group(3)
    else:
        city_out, state, zip_out = city.rsplit(" ", 1)[0], city.rsplit(" ", 1)[-1], ""

    return {
        "company_id": company_id(name, state, domain),
        "name": name,
        "domain": domain,
        "website": place.get("website"),
        "phone": phone,
        "email": None,
        "email_status": "none",
        "address": addr,
        "city": city_out,
        "state": state,
        "zip": zip_out,
        "naics": "",
        "category": place.get("category") or "",
        "sources": ["maps"],
        "signals": {
            "reviews": place.get("reviews") or 0,
            "rating": place.get("rating"),
            "maps_query": query,
            "maps_city": city,
            "needs_liveness_check": False,
        },
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_seed_maps.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Port the scraper body**

Copy `~/.claude/bob-miami-150/maps_scrape.py` into `seed_maps.py` below `place_to_record`. Keep `load_seen`, `save_seen`, `feature_id`, `scroll_feed`, `get_attr` and `scrape_place` unchanged. Rewrite `run()` to iterate `config.METROS` crossed with `config.MAPS_CATEGORIES`, pass each scraped place through `place_to_record`, and append accepted records to `data/seed_maps.jsonl`.

- [ ] **Step 6: Smoke-test the live scraper on one cell**

Run: `uv run seed_maps.py --metros "Tampa FL" --categories "roofing contractor"`
Expected: 15 to 40 records in `data/seed_maps.jsonl`, each with a phone or a domain. Open three and confirm the addresses parse into `city`, `state` and `zip`.

- [ ] **Step 7: Commit**

```bash
git add seed_maps.py tests/test_seed_maps.py
git commit -m "feat: Maps seed lane ported from bob-miami-150"
```

---

### Task 5: Domain resolution for contactless seeds

**Files:**
- Create: `resolve_domain.py`
- Test: `tests/test_resolve_domain.py`

**Interfaces:**
- Consumes: `seed_jobs.brave_search`, `normalize.norm_name`, `normalize.registrable_domain`, `records.read_jsonl`, `records.write_jsonl`
- Produces:
  - `resolve_domain.pick_domain(company_name: str, city: str, state: str, results: list[dict]) -> str | None`
  - `data/resolved.jsonl`

**Why this task exists:** SBA rows arrive with a name and a postal address and nothing else. Job rows arrive with an ATS slug. Neither has a website, and every downstream stage (site scrape, tech fingerprint, Hunter, Apollo) is keyed on domain. Without this step, roughly two thirds of the seed pool is dead weight.

The matching rule is deliberately strict. A wrong domain silently poisons every later stage, so an unresolved company is better than a mismatched one.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_resolve_domain.py
from resolve_domain import pick_domain

RESULTS = [
    {"title": "Rivera Mechanical | HVAC in Austin TX",
     "url": "https://riveramechanical.com/", "description": "Austin HVAC since 1998."},
    {"title": "Rivera Mechanical - Yelp",
     "url": "https://www.yelp.com/biz/rivera-mechanical-austin", "description": ""},
]


def test_picks_matching_company_domain():
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", RESULTS) == "riveramechanical.com"


def test_skips_directory_hosts():
    only_yelp = [RESULTS[1]]
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", only_yelp) is None


def test_rejects_unrelated_domain():
    unrelated = [{"title": "Austin HVAC Pros", "url": "https://austinhvacpros.com/",
                  "description": "Best HVAC in Austin"}]
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", unrelated) is None


def test_accepts_abbreviated_domain_when_tokens_match():
    abbrev = [{"title": "Rivera Mechanical", "url": "https://rivera-mechanical.net/",
               "description": "Austin, TX"}]
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", abbrev) == "rivera-mechanical.net"


def test_empty_results_return_none():
    assert pick_domain("Rivera Mechanical LLC", "Austin", "TX", []) is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_resolve_domain.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'resolve_domain'`

- [ ] **Step 3: Implement `resolve_domain.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "tldextract", "rapidfuzz"]
# ///
"""Find a company website for seed rows that arrived without one.

Strict on purpose. A wrong domain poisons every downstream stage, so an
unresolved company is preferable to a mismatched one.
"""
import argparse
import time

from rapidfuzz import fuzz

import config
from lib.normalize import norm_name, registrable_domain
from lib.records import read_jsonl, write_jsonl
from seed_jobs import brave_search

MATCH_THRESHOLD = 82


def pick_domain(company_name: str, city: str, state: str,
                results: list[dict]) -> str | None:
    """Return the best matching company domain, or None if nothing matches well."""
    target = norm_name(company_name).replace(" ", "")
    if not target:
        return None

    for result in results:
        domain = registrable_domain(result.get("url"))
        if not domain:
            continue  # social and directory hosts are filtered by registrable_domain
        stem = domain.rsplit(".", 1)[0].replace("-", "").replace("_", "")
        if fuzz.ratio(target, stem) >= MATCH_THRESHOLD:
            return domain
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="companies.jsonl")
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()

    rows, resolved, attempted = [], 0, 0
    for row in read_jsonl(config.DATA / args.infile):
        if row.get("domain") or attempted >= args.limit:
            rows.append(row)
            continue
        attempted += 1
        query = " ".join(x for x in [row["name"], row.get("city"), row.get("state")] if x)
        try:
            results = brave_search(query, count=8)
        except Exception as exc:
            print(f"skip {row['name']}: {exc}")
            rows.append(row)
            continue
        domain = pick_domain(row["name"], row.get("city", ""), row.get("state", ""), results)
        if domain:
            row["domain"] = domain
            row["website"] = f"https://{domain}"
            resolved += 1
        rows.append(row)
        time.sleep(1.1)

    n = write_jsonl(config.DATA / "resolved.jsonl", rows)
    print(f"attempted {attempted}, resolved {resolved}, wrote {n} rows")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_resolve_domain.py -v`
Expected: PASS, 5 tests

- [ ] **Step 5: Check the live resolution rate on a small batch**

Run: `uv run resolve_domain.py --limit 40`
Expected: a printed resolve rate. If fewer than 40% resolve, lower `MATCH_THRESHOLD` to 75 and hand-check 10 matches for false positives before accepting the change. Report the rate, since it determines how many SBA rows survive to Master.

- [ ] **Step 6: Commit**

```bash
git add resolve_domain.py tests/test_resolve_domain.py
git commit -m "feat: strict domain resolution for SBA and job seeds"
```

---

### Task 6: Dedupe and merge

**Files:**
- Create: `dedupe.py`
- Test: `tests/test_dedupe.py`

**Interfaces:**
- Consumes: `normalize.norm_name`, `normalize.norm_phone`, `records.read_jsonl`, `records.write_jsonl`
- Produces:
  - `dedupe.merge_pair(a: dict, b: dict) -> dict`
  - `dedupe.dedupe(rows: list[dict]) -> list[dict]`
  - `data/companies.jsonl`

**Merge rule:** domain first, then E.164 phone, then normalized name plus state. Merged records keep the union of populated fields, a merged `signals` dict, and a `sources` list of every contributing lane. Multi-lane agreement is itself a scoring signal, so `sources` must never be overwritten.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dedupe.py
from dedupe import dedupe, merge_pair

SBA = {"company_id": "a", "name": "Rivera Mechanical LLC", "domain": "riveramechanical.com",
       "website": None, "phone": None, "email": None, "email_status": "none",
       "address": "9 Elm St", "city": "Austin", "state": "TX", "zip": "78701",
       "naics": "238220", "category": "", "sources": ["sba_7a"],
       "signals": {"jobs_supported": 14, "loan_amount": 500000.0}}

MAPS = {"company_id": "b", "name": "Rivera Mechanical", "domain": "riveramechanical.com",
        "website": "https://riveramechanical.com", "phone": "+15125550111",
        "email": None, "email_status": "none", "address": "9 Elm St",
        "city": "Austin", "state": "TX", "zip": "78701", "naics": "",
        "category": "HVAC contractor", "sources": ["maps"],
        "signals": {"reviews": 212, "rating": 4.8}}

JOBS = {"company_id": "c", "name": "Riveramechanical", "domain": None, "website": None,
        "phone": None, "email": None, "email_status": "none", "address": "",
        "city": "", "state": "", "zip": "", "naics": "", "category": "",
        "sources": ["jobs"], "signals": {"open_finance_req": True, "job_url": "https://x/y"}}


def test_merge_unions_sources_and_signals():
    out = merge_pair(SBA, MAPS)
    assert sorted(out["sources"]) == ["maps", "sba_7a"]
    assert out["signals"]["jobs_supported"] == 14
    assert out["signals"]["reviews"] == 212


def test_merge_fills_empty_fields_without_overwriting():
    out = merge_pair(SBA, MAPS)
    assert out["phone"] == "+15125550111"
    assert out["naics"] == "238220"       # SBA value survives
    assert out["category"] == "HVAC contractor"  # Maps fills the blank


def test_dedupe_collapses_on_domain():
    out = dedupe([SBA, MAPS])
    assert len(out) == 1
    assert sorted(out[0]["sources"]) == ["maps", "sba_7a"]


def test_dedupe_collapses_on_phone_when_domain_missing():
    a = dict(SBA, domain=None, phone="+15125550111")
    out = dedupe([a, MAPS])
    assert len(out) == 1


def test_dedupe_collapses_on_name_and_state():
    a = dict(SBA, domain=None, phone=None)
    b = dict(MAPS, domain=None, phone=None)
    out = dedupe([a, b])
    assert len(out) == 1


def test_dedupe_keeps_same_name_in_different_states_apart():
    a = dict(SBA, domain=None, phone=None)
    b = dict(MAPS, domain=None, phone=None, state="FL")
    assert len(dedupe([a, b])) == 2


def test_dedupe_is_order_independent():
    assert len(dedupe([MAPS, SBA, JOBS])) == len(dedupe([JOBS, SBA, MAPS]))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_dedupe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dedupe'`

- [ ] **Step 3: Implement `dedupe.py`**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""Merge every seed lane into one record per company."""
import argparse

import config
from lib.normalize import norm_name
from lib.records import read_jsonl, write_jsonl

SEED_FILES = ("seed_sba.jsonl", "seed_jobs.jsonl", "seed_maps.jsonl")
SCALAR_FIELDS = ("name", "domain", "website", "phone", "email", "address",
                 "city", "state", "zip", "naics", "category")


def merge_pair(a: dict, b: dict) -> dict:
    """Merge b into a. Existing populated values win; blanks get filled."""
    out = dict(a)
    for field in SCALAR_FIELDS:
        if not out.get(field) and b.get(field):
            out[field] = b[field]
    out["signals"] = {**b.get("signals", {}), **a.get("signals", {})}
    out["sources"] = sorted(set(a.get("sources", [])) | set(b.get("sources", [])))
    if b.get("signals", {}).get("needs_liveness_check") is False:
        out["signals"]["needs_liveness_check"] = False
    return out


def _keys(row: dict) -> list[str]:
    """Identity keys in precedence order."""
    keys = []
    if row.get("domain"):
        keys.append("d:" + row["domain"].lower())
    if row.get("phone"):
        keys.append("p:" + row["phone"])
    name = norm_name(row.get("name", ""))
    if name:
        keys.append(f"n:{name}|{(row.get('state') or '').upper()}")
    return keys


def dedupe(rows: list[dict]) -> list[dict]:
    """Collapse rows that share any identity key. Order independent."""
    index: dict[str, int] = {}
    merged: list[dict | None] = []

    for row in rows:
        hits = sorted({index[k] for k in _keys(row) if k in index})
        if not hits:
            slot = len(merged)
            merged.append(dict(row))
        else:
            slot = hits[0]
            base = merged[slot]
            for other in hits[1:]:
                base = merge_pair(base, merged[other])
                merged[other] = None
            merged[slot] = merge_pair(base, row)

        for key in _keys(merged[slot]):
            index[key] = slot
        for key in _keys(row):
            index[key] = slot

    return [m for m in merged if m is not None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="companies.jsonl")
    args = ap.parse_args()

    rows = []
    for name in SEED_FILES:
        batch = list(read_jsonl(config.DATA / name))
        print(f"{name}: {len(batch)} rows")
        rows.extend(batch)

    out = dedupe(rows)
    print(f"{len(rows)} seed rows collapsed to {len(out)} companies")
    write_jsonl(config.DATA / args.out, out)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_dedupe.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Commit**

```bash
git add dedupe.py tests/test_dedupe.py
git commit -m "feat: multi-key dedupe merging all three seed lanes"
```

---

### Task 7: Site scrape and payment-tech fingerprint

**Files:**
- Create: `site_scrape.py` (port of `~/.claude/bob-miami-150/site_scrape.py`)
- Test: `tests/test_site_scrape.py`

**Interfaces:**
- Consumes: `normalize.norm_phone`, `normalize.is_valid_person_name`, `records.read_jsonl`, `records.write_jsonl`
- Produces:
  - `site_scrape.clean_emails(found: set[str], domain: str) -> list[str]`
  - `site_scrape.classify_email(email: str, domain: str) -> str`
  - `site_scrape.fingerprint_tech(html: str) -> list[str]`
  - `site_scrape.extract_jsonld_org(html: str) -> dict`
  - `data/sites.jsonl`

**Port note:** `bob-miami-150/site_scrape.py` already has the fetch, path-walk (`"", contact, contact-us, about, about-us, team, our-team, staff`), email regex and junk filter working under a `ThreadPoolExecutor`. Reuse all of it. Add the three new functions below and drop its loose `NAME_RE` owner extraction in favour of `is_valid_person_name` from Task 1, since that regex is what produced "Get Ah".

- [ ] **Step 1: Write the failing test**

```python
# tests/test_site_scrape.py
from site_scrape import classify_email, clean_emails, extract_jsonld_org, fingerprint_tech


def test_clean_emails_drops_asset_and_vendor_noise():
    found = {"info@acme.com", "logo@2x.png", "sentry@sentry.io",
             "a@wixpress.com", "owner@acme.com", "test@example.com"}
    assert sorted(clean_emails(found, "acme.com")) == ["info@acme.com", "owner@acme.com"]


def test_clean_emails_prefers_matching_domain():
    found = {"info@acme.com", "hello@gmail.com"}
    assert clean_emails(found, "acme.com") == ["info@acme.com"]


def test_classify_email_generic_vs_personal():
    assert classify_email("info@acme.com", "acme.com") == "generic"
    assert classify_email("sales@acme.com", "acme.com") == "generic"
    assert classify_email("maria.gonzalez@acme.com", "acme.com") == "personal"


def test_fingerprint_detects_payment_stack():
    html = ('<script src="https://js.stripe.com/v3/"></script>'
            '<script>window.Shopify={};</script>'
            '<a href="https://quickbooks.intuit.com/app">books</a>')
    assert sorted(fingerprint_tech(html)) == ["quickbooks", "shopify", "stripe"]


def test_fingerprint_returns_empty_for_plain_page():
    assert fingerprint_tech("<html><body>hello</body></html>") == []


def test_extract_jsonld_org_pulls_phone_and_address():
    html = '''<script type="application/ld+json">
    {"@type":"LocalBusiness","name":"Acme","telephone":"(512) 555-0111",
     "address":{"streetAddress":"9 Elm St","addressLocality":"Austin",
     "addressRegion":"TX","postalCode":"78701"}}</script>'''
    out = extract_jsonld_org(html)
    assert out["phone"] == "+15125550111"
    assert out["city"] == "Austin"
    assert out["state"] == "TX"


def test_extract_jsonld_org_survives_broken_json():
    assert extract_jsonld_org('<script type="application/ld+json">{oops</script>') == {}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_site_scrape.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'site_scrape'`

- [ ] **Step 3: Implement the new functions in `site_scrape.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "beautifulsoup4", "tldextract"]
# ///
import json
import re

from bs4 import BeautifulSoup

from lib.normalize import norm_phone

JUNK = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", ".gif",
        ".webp", ".svg", "godaddy", "squarespace", "yourdomain", "domain.com")

GENERIC_LOCALPARTS = {
    "info", "hello", "contact", "sales", "support", "admin", "office",
    "team", "mail", "enquiries", "inquiries", "help", "service", "billing",
}

# Fingerprints for the money stack. Presence implies real transactions.
TECH_PATTERNS = {
    "stripe": r"js\.stripe\.com|stripe\.com/v3",
    "shopify": r"cdn\.shopify\.com|window\.Shopify",
    "square": r"squareup\.com|square\.site",
    "quickbooks": r"quickbooks\.intuit\.com|qbo\.intuit\.com",
    "billcom": r"bill\.com",
    "gusto": r"gusto\.com",
    "adp": r"adp\.com",
    "servicetitan": r"servicetitan\.com",
    "jobber": r"getjobber\.com",
    "housecallpro": r"housecallpro\.com",
}


def clean_emails(found: set[str], domain: str) -> list[str]:
    """Filter asset and vendor noise, prefer addresses on the company domain."""
    keep = []
    for email in found:
        low = email.lower()
        if any(j in low for j in JUNK):
            continue
        if low.count("@") != 1 or len(low) > 80:
            continue
        keep.append(low)
    on_domain = [e for e in keep if e.endswith("@" + domain.lower())]
    return sorted(on_domain) if on_domain else sorted(keep)


def classify_email(email: str, domain: str) -> str:
    """Label an address as generic or personal."""
    local = email.split("@", 1)[0].lower()
    return "generic" if local in GENERIC_LOCALPARTS else "personal"


def fingerprint_tech(html: str) -> list[str]:
    """Return which payment and finance platforms appear in the page source."""
    return sorted(name for name, pattern in TECH_PATTERNS.items()
                  if re.search(pattern, html, re.I))


def extract_jsonld_org(html: str) -> dict:
    """Pull phone and address from schema.org markup. Never raises."""
    out = {}
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            blob = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for node in (blob if isinstance(blob, list) else [blob]):
            if not isinstance(node, dict):
                continue
            phone = norm_phone(node.get("telephone"))
            if phone:
                out["phone"] = phone
            addr = node.get("address")
            if isinstance(addr, dict):
                out.setdefault("address", addr.get("streetAddress", ""))
                out.setdefault("city", addr.get("addressLocality", ""))
                out.setdefault("state", addr.get("addressRegion", ""))
                out.setdefault("zip", str(addr.get("postalCode", ""))[:5])
    return out
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_site_scrape.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Port the crawl body**

Copy the `fetch`, `scrape_domain` and `ThreadPoolExecutor` main loop from `~/.claude/bob-miami-150/site_scrape.py`. Change the input to `data/resolved.jsonl` and the output to `data/sites.jsonl`. For each company write: `emails` (through `clean_emails`), `email_status` per `classify_email`, `phone` (JSON-LD first, then the existing footer regex, through `norm_phone`), `tech` from `fingerprint_tech` over the concatenated page sources, and `has_pricing_page` / `has_careers_page` booleans set when those paths return HTTP 200. Delete the old `NAME_RE` block entirely.

- [ ] **Step 6: Run against a 50-row sample**

Run: `uv run site_scrape.py --limit 50`
Expected: `data/sites.jsonl` with 50 rows. Confirm at least a third carry an email and that no email in the output is an image filename.

- [ ] **Step 7: Commit**

```bash
git add site_scrape.py tests/test_site_scrape.py
git commit -m "feat: site scrape with payment-tech fingerprint and JSON-LD extraction"
```

---

### Task 8: Signals pass

**Files:**
- Create: `signals.py`
- Test: `tests/test_signals.py`

**Interfaces:**
- Consumes: `seed_jobs.brave_search`, `records.read_jsonl`, `records.write_jsonl`
- Produces:
  - `signals.linkedin_headcount(page, domain: str) -> int | None`
  - `signals.press_hits(name: str, city: str) -> int`
  - `signals.marketplace_presence(name: str, domain: str) -> list[str]`
  - `data/signals.jsonl`

**Cost note:** this stage is the slowest and the most rate-limited. It runs only against companies that already cleared the site scrape with a domain, never against the whole seed pool.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_signals.py
from signals import parse_headcount, score_marketplace_results

def test_parse_headcount_from_linkedin_copy():
    assert parse_headcount("51-200 employees") == 200
    assert parse_headcount("11-50 employees · Construction") == 50
    assert parse_headcount("2-10 employees") == 10
    assert parse_headcount("10,001+ employees") == 10001

def test_parse_headcount_returns_none_for_noise():
    assert parse_headcount("") is None
    assert parse_headcount("See jobs") is None

def test_marketplace_results_detect_known_platforms():
    results = [
        {"url": "https://www.g2.com/products/acme/reviews", "title": "Acme Reviews"},
        {"url": "https://www.bbb.org/us/tx/austin/profile/hvac/acme-123", "title": "BBB"},
        {"url": "https://randomblog.com/acme", "title": "blog"},
    ]
    assert sorted(score_marketplace_results(results)) == ["bbb", "g2"]

def test_marketplace_results_empty_when_nothing_matches():
    assert score_marketplace_results([{"url": "https://x.com/y", "title": "z"}]) == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_signals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'signals'`

- [ ] **Step 3: Implement `signals.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "playwright"]
# ///
"""Scale, intent and credibility signals for companies that have a domain."""
import re
import time

import config
from lib.records import read_jsonl, write_jsonl
from seed_jobs import brave_search

MARKETPLACES = {
    "g2": r"g2\.com/products/",
    "capterra": r"capterra\.com/p/",
    "bbb": r"bbb\.org/.+/profile/",
    "angi": r"angi\.com/companylist/",
    "trustpilot": r"trustpilot\.com/review/",
}

_HEADCOUNT = re.compile(r"([\d,]+)\s*(?:-|to|–)\s*([\d,]+)\s*employees", re.I)
_HEADCOUNT_PLUS = re.compile(r"([\d,]+)\+\s*employees", re.I)


def parse_headcount(text: str) -> int | None:
    """Upper bound of a LinkedIn employee-count band."""
    if not text:
        return None
    plus = _HEADCOUNT_PLUS.search(text)
    if plus:
        return int(plus.group(1).replace(",", ""))
    band = _HEADCOUNT.search(text)
    if band:
        return int(band.group(2).replace(",", ""))
    return None


def score_marketplace_results(results: list[dict]) -> list[str]:
    """Which review marketplaces list this company."""
    hits = set()
    for result in results:
        url = result.get("url", "")
        for name, pattern in MARKETPLACES.items():
            if re.search(pattern, url, re.I):
                hits.add(name)
    return sorted(hits)


def press_hits(name: str, city: str) -> int:
    """Count news and funding mentions. Cheap proxy for momentum."""
    query = f'"{name}" ({city}) (raised OR acquired OR expands OR "named" OR award)'
    try:
        return len(brave_search(query, count=10))
    except Exception:
        return 0


def marketplace_presence(name: str, domain: str) -> list[str]:
    try:
        return score_marketplace_results(brave_search(f'"{name}" {domain} reviews', count=10))
    except Exception:
        return []


def linkedin_headcount(page, domain: str) -> int | None:
    """Read the employee band off a LinkedIn company page using the saved session."""
    try:
        page.goto(f"https://www.linkedin.com/company/{domain.split('.')[0]}/about/",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(1500)
        return parse_headcount(page.inner_text("body")[:6000])
    except Exception:
        return None


def main():
    rows = []
    for row in read_jsonl(config.DATA / "sites.jsonl"):
        domain = row.get("domain")
        if not domain:
            rows.append(row)
            continue
        sig = row.setdefault("signals", {})
        sig["marketplaces"] = marketplace_presence(row["name"], domain)
        sig["press_hits"] = press_hits(row["name"], row.get("city", ""))
        rows.append(row)
        time.sleep(1.1)

    write_jsonl(config.DATA / "signals.jsonl", rows)
    print(f"wrote {len(rows)} rows to data/signals.jsonl")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_signals.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Commit**

```bash
git add signals.py tests/test_signals.py
git commit -m "feat: scale, marketplace and press signal pass"
```

---

### Task 9: Scoring and tiering

**Files:**
- Create: `score.py`
- Test: `tests/test_score.py`

**Interfaces:**
- Consumes: `config.WEIGHTS`, `config.SCORE_FLOOR`, `config.MIN_FAMILIES`, `config.TIER1_FRACTION`, `records.read_jsonl`, `records.write_jsonl`
- Produces:
  - `score.family_scores(row: dict) -> dict[str, float]` (keys `money`, `scale`, `signal`, `reach`, each 0.0 to 1.0)
  - `score.total_score(row: dict) -> int`
  - `score.assign_tiers(rows: list[dict]) -> list[dict]`
  - `data/scored.jsonl`

**Design note:** each family returns a 0.0 to 1.0 fraction, then the weights in `config.WEIGHTS` convert it to points. `MIN_FAMILIES` counts how many families produced any evidence at all, which is what stops a company qualifying on Maps review count alone.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_score.py
import config
from score import assign_tiers, family_scores, total_score

RICH = {"name": "Rivera Mechanical", "domain": "riveramechanical.com",
        "phone": "+15125550111", "email": "maria@riveramechanical.com",
        "email_status": "verified", "sources": ["sba_7a", "maps", "jobs"],
        "signals": {"jobs_supported": 40, "loan_amount": 900000.0,
                    "tech": ["stripe", "quickbooks"], "has_pricing_page": True,
                    "reviews": 300, "headcount": 120, "open_finance_req": True,
                    "press_hits": 6, "marketplaces": ["bbb", "g2"]}}

THIN = {"name": "Tiny Shop", "domain": None, "phone": "+15125550112",
        "email": None, "email_status": "none", "sources": ["maps"],
        "signals": {"reviews": 12}}


def test_weights_sum_to_100():
    assert sum(config.WEIGHTS.values()) == 100


def test_family_scores_are_fractions():
    for value in family_scores(RICH).values():
        assert 0.0 <= value <= 1.0


def test_rich_company_scores_high():
    assert total_score(RICH) >= 75


def test_thin_company_scores_below_floor():
    assert total_score(THIN) < config.SCORE_FLOOR


def test_score_is_bounded_0_to_100():
    assert 0 <= total_score(THIN) <= 100
    assert 0 <= total_score(RICH) <= 100


def test_open_req_alone_still_needs_a_second_family():
    only_req = {"name": "X", "domain": None, "phone": None, "email": None,
                "email_status": "none", "sources": ["jobs"],
                "signals": {"open_finance_req": True}}
    out = assign_tiers([only_req])
    assert out[0]["tier"] == "reject"
    assert "families" in out[0]["reject_reason"]


def test_assign_tiers_marks_top_fraction_as_tier1():
    rows = []
    for i in range(100):
        row = dict(RICH, name=f"co{i}")
        row["signals"] = dict(RICH["signals"], jobs_supported=100 - i, reviews=300 - i)
        rows.append(row)
    out = assign_tiers(rows)
    tier1 = [r for r in out if r["tier"] == "tier1"]
    assert len(tier1) == int(100 * config.TIER1_FRACTION)
    assert all(r["score"] >= max(x["score"] for x in out if x["tier"] == "master")
               for r in tier1)


def test_rows_below_floor_are_rejected_with_a_reason():
    out = assign_tiers([THIN])
    assert out[0]["tier"] == "reject"
    assert out[0]["reject_reason"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_score.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'score'`

- [ ] **Step 3: Implement `score.py`**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""Score every company 0-100 across four evidence families, then tier."""
import argparse

import config
from lib.records import read_jsonl, write_jsonl


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def family_scores(row: dict) -> dict[str, float]:
    """Each family returns a 0.0 to 1.0 fraction of its available evidence."""
    sig = row.get("signals", {})

    # Money proof: loan evidence, payment stack, a real pricing surface.
    money = 0.0
    money += _clamp((sig.get("loan_amount") or 0) / 1_000_000) * 0.5
    money += _clamp(len(sig.get("tech") or []) / 3) * 0.35
    money += 0.15 if sig.get("has_pricing_page") else 0.0

    # Operating scale: headcount, payroll size, footprint.
    scale = 0.0
    scale += _clamp((sig.get("headcount") or 0) / 200) * 0.4
    scale += _clamp((sig.get("jobs_supported") or 0) / 50) * 0.4
    scale += _clamp((sig.get("reviews") or 0) / 400) * 0.2

    # Buying signal: an open finance req is the strongest single trigger.
    signal = 0.0
    signal += 0.5 if sig.get("open_finance_req") else 0.0
    signal += _clamp((sig.get("press_hits") or 0) / 8) * 0.25
    signal += _clamp(len(sig.get("marketplaces") or []) / 2) * 0.25

    # Reachability: a named verified contact beats a generic inbox.
    reach = 0.0
    if row.get("email_status") == "verified":
        reach += 0.6
    elif row.get("email_status") in ("personal", "guessed"):
        reach += 0.4
    elif row.get("email"):
        reach += 0.2
    if row.get("phone"):
        reach += 0.4

    return {"money": _clamp(money), "scale": _clamp(scale),
            "signal": _clamp(signal), "reach": _clamp(reach)}


def total_score(row: dict) -> int:
    fams = family_scores(row)
    return round(sum(fams[name] * config.WEIGHTS[name] for name in config.WEIGHTS))


def _families_with_evidence(row: dict) -> int:
    return sum(1 for value in family_scores(row).values() if value > 0)


def assign_tiers(rows: list[dict]) -> list[dict]:
    """Score, reject below the floor, then mark the top fraction as tier1."""
    scored = []
    for row in rows:
        out = dict(row)
        out["score"] = total_score(row)
        families = _families_with_evidence(row)
        if families < config.MIN_FAMILIES:
            out["tier"] = "reject"
            out["reject_reason"] = f"only {families} evidence families"
        elif out["score"] < config.SCORE_FLOOR:
            out["tier"] = "reject"
            out["reject_reason"] = f"score {out['score']} below floor {config.SCORE_FLOOR}"
        else:
            out["tier"] = "master"
            out["reject_reason"] = ""
        scored.append(out)

    keepers = sorted([r for r in scored if r["tier"] == "master"],
                     key=lambda r: r["score"], reverse=True)
    cutoff = int(len(keepers) * config.TIER1_FRACTION)
    for row in keepers[:cutoff]:
        row["tier"] = "tier1"
    return scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="signals.jsonl")
    args = ap.parse_args()

    rows = assign_tiers(list(read_jsonl(config.DATA / args.infile)))
    counts = {}
    for row in rows:
        counts[row["tier"]] = counts.get(row["tier"], 0) + 1
    print(counts)
    write_jsonl(config.DATA / "scored.jsonl", rows)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_score.py -v`
Expected: PASS, 8 tests

- [ ] **Step 5: Inspect the real distribution and tune**

Run: `uv run score.py`
Expected: printed tier counts. If `master` plus `tier1` lands far from `config.TARGET_MASTER_ROWS`, adjust `SCORE_FLOOR` rather than the weights, then rerun. Report the final floor and the resulting counts.

- [ ] **Step 6: Commit**

```bash
git add score.py tests/test_score.py
git commit -m "feat: four-family 0-100 scoring with evidence floor and tiering"
```

---

### Task 10: Tier 1 enrichment waterfall

**Files:**
- Create: `enrich_tier1.py`
- Test: `tests/test_enrich_tier1.py`

**Interfaces:**
- Consumes: `normalize.is_valid_person_name`, `records.read_jsonl`, `records.write_jsonl`, `config.APIFY_BUDGET_USD`
- Produces:
  - `enrich_tier1.hunter_domain_search(domain: str) -> dict`
  - `enrich_tier1.hunter_verify(email: str) -> str`
  - `enrich_tier1.apollo_contact(domain: str) -> dict | None`
  - `enrich_tier1.waterfall(row: dict, budget: Budget) -> dict`
  - `data/enriched.jsonl`

**Waterfall order,** each step skipped once the row is satisfied. A row is satisfied when it has a valid contact name and an email whose status is `verified`.

1. site scrape output already on the row (free)
2. Maps phone already on the row (free)
3. state registry officer lookup (free, Florida only for this build)
4. LinkedIn company page decision-maker (free, saved session)
5. Hunter domain search plus verification (existing key)
6. Apollo people search by domain and title (existing key)
7. Apify `code_crafter~leads-finder` (paid, hard $10 ceiling)

**Registry note:** `~/.claude/bob-miami-150/sunbiz_fill.py` is the working Florida implementation. Sunbiz is Cloudflare-gated and needs headful Chrome through Playwright; the clearance cookie persists per browser context. Import it for `state == "FL"` rows and skip step 3 entirely for every other state. Do not attempt to generalize registry lookup in this build.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_enrich_tier1.py
import pytest
from enrich_tier1 import Budget, BudgetExceeded, is_satisfied, pick_best_contact


def test_row_with_verified_named_contact_is_satisfied():
    row = {"contact_name": "Maria Gonzalez", "contact_email": "maria@acme.com",
           "contact_email_status": "verified"}
    assert is_satisfied(row) is True


def test_row_with_guessed_email_is_not_satisfied():
    row = {"contact_name": "Maria Gonzalez", "contact_email": "maria@acme.com",
           "contact_email_status": "guessed"}
    assert is_satisfied(row) is False


def test_row_with_junk_name_is_not_satisfied():
    row = {"contact_name": "Get Ah", "contact_email": "info@acme.com",
           "contact_email_status": "verified"}
    assert is_satisfied(row) is False


def test_pick_best_contact_prefers_decision_maker_titles():
    people = [
        {"name": "Sam Reed", "title": "Marketing Intern", "email": "sam@acme.com"},
        {"name": "Maria Gonzalez", "title": "Owner", "email": "maria@acme.com"},
        {"name": "Lee Park", "title": "Technician", "email": "lee@acme.com"},
    ]
    assert pick_best_contact(people)["name"] == "Maria Gonzalez"


def test_pick_best_contact_rejects_invalid_names():
    people = [{"name": "Contact Us", "title": "Owner", "email": "info@acme.com"}]
    assert pick_best_contact(people) is None


def test_budget_blocks_spend_over_ceiling():
    budget = Budget(limit_usd=0.05)
    budget.charge(0.04)
    with pytest.raises(BudgetExceeded):
        budget.charge(0.03)


def test_budget_reports_remaining():
    budget = Budget(limit_usd=10.0)
    budget.charge(2.5)
    assert budget.remaining() == pytest.approx(7.5)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_enrich_tier1.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'enrich_tier1'`

- [ ] **Step 3: Implement `enrich_tier1.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Cost-ordered enrichment for Tier 1 rows. Free steps first, Apify last."""
import argparse
import os
import pathlib

import httpx

import config
from lib.normalize import is_valid_person_name
from lib.records import read_jsonl, write_jsonl

SECURITY = pathlib.Path.home() / ".claude" / "security"

DECISION_TITLES = (
    "owner", "founder", "co-founder", "president", "ceo", "principal",
    "partner", "managing", "general manager", "coo", "cfo", "controller",
    "vice president", "director of operations", "office manager",
)


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Hard ceiling on paid enrichment. Raises rather than overspending."""

    def __init__(self, limit_usd: float):
        self.limit_usd = limit_usd
        self.spent = 0.0

    def charge(self, amount: float) -> None:
        if self.spent + amount > self.limit_usd:
            raise BudgetExceeded(
                f"${self.spent + amount:.2f} would exceed ${self.limit_usd:.2f}")
        self.spent += amount

    def remaining(self) -> float:
        return self.limit_usd - self.spent


def _key(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    for path in SECURITY.glob("*.env"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(f"{name} not found")


def is_satisfied(row: dict) -> bool:
    """A row is done when it has a real name and a verified email."""
    name = row.get("contact_name") or ""
    return (is_valid_person_name(name)
            and row.get("contact_email_status") == "verified")


def pick_best_contact(people: list[dict]) -> dict | None:
    """Highest-ranking valid decision-maker from a list of people."""
    best, best_rank = None, len(DECISION_TITLES)
    for person in people:
        if not is_valid_person_name(person.get("name") or ""):
            continue
        title = (person.get("title") or "").lower()
        for rank, keyword in enumerate(DECISION_TITLES):
            if keyword in title and rank < best_rank:
                best, best_rank = person, rank
                break
    return best


def hunter_domain_search(domain: str) -> dict:
    """Hunter emails for a domain. Returns {'emails': [...], 'pattern': str}."""
    resp = httpx.get("https://api.hunter.io/v2/domain-search",
                     params={"domain": domain, "api_key": _key("HUNTER_API_KEY"),
                             "limit": 10},
                     timeout=30.0)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return {
        "pattern": data.get("pattern") or "",
        "emails": [{"name": " ".join(x for x in [e.get("first_name"),
                                                 e.get("last_name")] if x),
                    "title": e.get("position") or "",
                    "email": e.get("value"),
                    "confidence": e.get("confidence", 0)}
                   for e in data.get("emails", [])],
    }


def hunter_verify(email: str) -> str:
    """Return 'verified', 'guessed' or 'none' for one address."""
    try:
        resp = httpx.get("https://api.hunter.io/v2/email-verifier",
                         params={"email": email, "api_key": _key("HUNTER_API_KEY")},
                         timeout=30.0)
        resp.raise_for_status()
        result = resp.json().get("data", {}).get("result")
    except httpx.HTTPError:
        return "guessed"
    return "verified" if result == "deliverable" else "guessed"


def apollo_contact(domain: str) -> dict | None:
    """One decision-maker from Apollo for this domain."""
    try:
        resp = httpx.post(
            "https://api.apollo.io/v1/mixed_people/search",
            json={"api_key": _key("APOLLO_API_KEY"),
                  "q_organization_domains": domain,
                  "person_titles": list(DECISION_TITLES[:8]),
                  "page": 1, "per_page": 5},
            timeout=30.0)
        resp.raise_for_status()
        people = [{"name": p.get("name"), "title": p.get("title"),
                   "email": p.get("email")}
                  for p in resp.json().get("people", []) if p.get("email")]
    except httpx.HTTPError:
        return None
    return pick_best_contact(people)


def waterfall(row: dict, budget: Budget) -> dict:
    """Run the cost-ordered steps until the row is satisfied."""
    out = dict(row)
    domain = out.get("domain")
    if not domain:
        return out

    # Step 5: Hunter.
    if not is_satisfied(out):
        try:
            found = hunter_domain_search(domain)
            best = pick_best_contact(found["emails"])
            if best:
                out["contact_name"] = best["name"]
                out["contact_title"] = best["title"]
                out["contact_email"] = best["email"]
                out["contact_email_status"] = hunter_verify(best["email"])
        except (httpx.HTTPError, RuntimeError) as exc:
            out.setdefault("enrich_errors", []).append(f"hunter: {exc}")

    # Step 6: Apollo.
    if not is_satisfied(out):
        best = apollo_contact(domain)
        if best:
            out["contact_name"] = best["name"]
            out["contact_title"] = best["title"]
            out["contact_email"] = best["email"]
            out["contact_email_status"] = hunter_verify(best["email"])

    # Step 7: Apify, last and cheapest actor only.
    if not is_satisfied(out) and budget.remaining() > 0.05:
        try:
            budget.charge(0.05)
            out.setdefault("enrich_errors", []).append("apify: pending manual run")
        except BudgetExceeded:
            out.setdefault("enrich_errors", []).append("apify: budget exhausted")

    if out.get("contact_name") and not is_valid_person_name(out["contact_name"]):
        out["contact_name"] = ""
        out["contact_email_status"] = "none"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=250)
    args = ap.parse_args()

    budget = Budget(config.APIFY_BUDGET_USD)
    rows, done = [], 0
    for row in read_jsonl(config.DATA / "scored.jsonl"):
        if row.get("tier") == "tier1" and done < args.limit:
            row = waterfall(row, budget)
            done += 1
        rows.append(row)

    print(f"enriched {done} tier1 rows, Apify spend ${budget.spent:.2f}")
    write_jsonl(config.DATA / "enriched.jsonl", rows)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_enrich_tier1.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Check API quota before any real batch**

Run: `uv run python -c "import enrich_tier1 as e, httpx; print(httpx.get('https://api.hunter.io/v2/account', params={'api_key': e._key('HUNTER_API_KEY')}).json()['data']['requests'])"`
Expected: printed request quota. Report the remaining searches and verifications, then size `--limit` to fit. Stop and report rather than burning the quota if it is nearly exhausted.

- [ ] **Step 6: Commit**

```bash
git add enrich_tier1.py tests/test_enrich_tier1.py
git commit -m "feat: cost-ordered Tier 1 enrichment waterfall with hard Apify ceiling"
```

---

### Task 11: Hooks

**Files:**
- Create: `hooks.py`
- Test: `tests/test_hooks.py`

**Interfaces:**
- Consumes: `records.read_jsonl`, `records.write_jsonl`
- Produces:
  - `hooks.hook_for(row: dict) -> str`
  - `hooks.lint_hook(text: str) -> list[str]` (returns violations, empty means clean)
  - `data/hooks.jsonl`

**Copy rules, enforced by `lint_hook`:** no em dashes, no banned AI-tell vocabulary, no mirrored two-beat constructions, at most 25 words. Lane 1 rows get the requisition angle by default, which maps to BOB's documented "cancel the req" framing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hooks.py
from hooks import hook_for, lint_hook

JOB_ROW = {"name": "Rivera Mechanical", "city": "Austin", "state": "TX",
           "signals": {"open_finance_req": True, "job_title": "Bookkeeper at Rivera Mechanical",
                       "job_url": "https://boards.greenhouse.io/rivera/jobs/1"}}
TECH_ROW = {"name": "Summit Roofing", "city": "Denver", "state": "CO",
            "signals": {"tech": ["quickbooks", "stripe"], "jobs_supported": 30}}
BARE_ROW = {"name": "Plain Co", "city": "Tampa", "state": "FL", "signals": {}}


def test_job_row_gets_requisition_hook():
    hook = hook_for(JOB_ROW)
    assert "bookkeeper" in hook.lower()
    assert lint_hook(hook) == []


def test_tech_row_gets_stack_hook():
    hook = hook_for(TECH_ROW)
    assert "quickbooks" in hook.lower()
    assert lint_hook(hook) == []


def test_bare_row_gets_no_hook():
    assert hook_for(BARE_ROW) == ""


def test_lint_flags_em_dash():
    assert "em dash" in " ".join(lint_hook("You posted a bookkeeper role — worth a look"))


def test_lint_flags_banned_vocabulary():
    violations = lint_hook("This seamlessly and genuinely leverages your stack")
    assert len(violations) >= 2


def test_lint_flags_overlong_hook():
    long_hook = " ".join(["word"] * 40)
    assert any("too long" in v for v in lint_hook(long_hook))


def test_every_generated_hook_passes_lint():
    for row in (JOB_ROW, TECH_ROW):
        assert lint_hook(hook_for(row)) == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_hooks.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'hooks'`

- [ ] **Step 3: Implement `hooks.py`**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""One-line outreach angle per Tier 1 row, built from that company's own material."""
import re

import config
from lib.records import read_jsonl, write_jsonl

BANNED = {
    "actually", "genuinely", "seamless", "seamlessly", "leverage", "leverages",
    "robust", "cutting-edge", "game-changer", "unlock", "delve", "elevate",
    "streamline", "supercharge", "revolutionize", "transformative",
}
MAX_WORDS = 25
_MIRROR = re.compile(r"\bnot\s+\w+[,;]?\s+but\s+\w+", re.I)


def lint_hook(text: str) -> list[str]:
    """Return copy-rule violations. Empty list means the hook can ship."""
    problems = []
    if "—" in text or "--" in text:
        problems.append("em dash present")
    words = re.findall(r"[a-z'-]+", text.lower())
    for word in words:
        if word in BANNED:
            problems.append(f"banned word: {word}")
    if len(words) > MAX_WORDS:
        problems.append(f"too long: {len(words)} words")
    if _MIRROR.search(text):
        problems.append("mirrored two-beat construction")
    return problems


def hook_for(row: dict) -> str:
    """Build the angle. Requisition first, then stack, then nothing."""
    sig = row.get("signals", {})
    name = row.get("name", "")

    if sig.get("open_finance_req"):
        title = (sig.get("job_title") or "").split(" at ")[0].strip() or "bookkeeper"
        return f"{name} is hiring a {title}. BOB does that work, so the req can wait."

    tech = sig.get("tech") or []
    if "quickbooks" in tech:
        return f"{name} runs QuickBooks. BOB reads it and handles the bills around it."
    if tech:
        return f"{name} runs {tech[0].title()}. BOB sits on top and watches the money move."

    return ""


def main():
    rows = []
    for row in read_jsonl(config.DATA / "enriched.jsonl"):
        if row.get("tier") == "tier1":
            hook = hook_for(row)
            problems = lint_hook(hook) if hook else []
            row["hook"] = "" if problems else hook
            if problems:
                row.setdefault("enrich_errors", []).append(f"hook lint: {problems}")
        rows.append(row)

    written = sum(1 for r in rows if r.get("hook"))
    print(f"{written} hooks written")
    write_jsonl(config.DATA / "hooks.jsonl", rows)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_hooks.py -v`
Expected: PASS, 7 tests

- [ ] **Step 5: Commit**

```bash
git add hooks.py tests/test_hooks.py
git commit -m "feat: Tier 1 outreach hooks with copy-rule lint gate"
```

---

### Task 12: QA gate

**Files:**
- Create: `qa.py`
- Test: `tests/test_qa.py`

**Interfaces:**
- Consumes: `normalize.is_valid_person_name`, `records.read_jsonl`
- Produces:
  - `qa.check_row(row: dict) -> list[str]` (violations, empty means the row can ship)
  - `qa.run_gates(rows: list[dict]) -> dict` (summary with `passed`, `failed`, `by_reason`)
  - `qa.sample(rows: list[dict], n: int = 25) -> list[dict]`
  - `data/qa_report.json`

**This task blocks the upload.** `upload_sheet.py` refuses to run unless `qa_report.json` shows zero blocking failures and the hand sample has been reviewed.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qa.py
from qa import check_row, run_gates, sample

GOOD = {"name": "Rivera Mechanical", "phone": "+15125550111", "email": "info@rivera.com",
        "email_status": "generic", "tier": "master", "contact_name": "",
        "signals": {"needs_liveness_check": False}}
GOOD_T1 = {"name": "Summit Roofing", "phone": "+13035550111",
           "email": "maria@summit.com", "email_status": "personal", "tier": "tier1",
           "contact_name": "Maria Gonzalez", "contact_email": "maria@summit.com",
           "contact_email_status": "verified", "hook": "Summit Roofing is hiring.",
           "signals": {"needs_liveness_check": False}}


def test_good_rows_pass():
    assert check_row(GOOD) == []
    assert check_row(GOOD_T1) == []


def test_row_without_email_or_phone_fails():
    bad = dict(GOOD, phone=None, email=None)
    assert any("contactable" in v for v in check_row(bad))


def test_junk_contact_name_fails():
    bad = dict(GOOD_T1, contact_name="Get Ah")
    assert any("name" in v for v in check_row(bad))


def test_unchecked_liveness_flag_fails():
    bad = dict(GOOD, signals={"needs_liveness_check": True})
    assert any("liveness" in v for v in check_row(bad))


def test_guessed_email_labelled_verified_fails():
    bad = dict(GOOD_T1, contact_email_status="verified", contact_email="")
    assert any("email" in v for v in check_row(bad))


def test_run_gates_counts_by_reason():
    out = run_gates([GOOD, dict(GOOD, phone=None, email=None)])
    assert out["passed"] == 1
    assert out["failed"] == 1
    assert out["by_reason"]


def test_sample_is_deterministic():
    rows = [dict(GOOD, name=f"co{i}") for i in range(100)]
    assert [r["name"] for r in sample(rows, 25)] == [r["name"] for r in sample(rows, 25)]


def test_sample_returns_all_when_fewer_than_n():
    rows = [dict(GOOD, name=f"co{i}") for i in range(5)]
    assert len(sample(rows, 25)) == 5
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_qa.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'qa'`

- [ ] **Step 3: Implement `qa.py`**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""Gates that block the upload. Every rule here exists because it failed before."""
import json
import random

import config
from lib.normalize import is_valid_person_name
from lib.records import read_jsonl

SAMPLE_SEED = 20260826


def check_row(row: dict) -> list[str]:
    """Return blocking violations for one row."""
    problems = []

    if not row.get("phone") and not row.get("email"):
        problems.append("not contactable: no email and no phone")

    if row.get("signals", {}).get("needs_liveness_check"):
        problems.append("liveness not confirmed for a PPP-sourced row")

    name = row.get("contact_name") or ""
    if name and not is_valid_person_name(name):
        problems.append(f"invalid contact name: {name!r}")

    status = row.get("contact_email_status")
    if status == "verified" and not row.get("contact_email"):
        problems.append("email status is verified but no address is present")

    if row.get("tier") == "tier1":
        if not row.get("contact_name"):
            problems.append("tier1 row has no contact name")
        if not row.get("hook"):
            problems.append("tier1 row has no hook")

    return problems


def run_gates(rows: list[dict]) -> dict:
    passed, failed, by_reason = 0, 0, {}
    for row in rows:
        problems = check_row(row)
        if problems:
            failed += 1
            for problem in problems:
                key = problem.split(":")[0]
                by_reason[key] = by_reason.get(key, 0) + 1
        else:
            passed += 1
    return {"passed": passed, "failed": failed, "by_reason": by_reason}


def sample(rows: list[dict], n: int = 25) -> list[dict]:
    """Deterministic hand-review sample."""
    if len(rows) <= n:
        return list(rows)
    return random.Random(SAMPLE_SEED).sample(rows, n)


def main():
    rows = [r for r in read_jsonl(config.DATA / "hooks.jsonl")
            if r.get("tier") in ("master", "tier1")]
    report = run_gates(rows)
    report["total"] = len(rows)
    report["sample"] = [
        {k: r.get(k) for k in ("name", "city", "state", "phone", "email",
                               "email_status", "score", "tier", "contact_name",
                               "contact_email", "contact_email_status", "hook")}
        for r in sample(rows, 25)
    ]
    (config.DATA / "qa_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "sample"}, indent=2))
    print("\nHand-review sample written to data/qa_report.json")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_qa.py -v`
Expected: PASS, 8 tests

- [ ] **Step 5: Run the gates and show Rich the sample**

Run: `uv run qa.py`
Expected: a printed summary and 25 sampled rows in `data/qa_report.json`. Show the 25 rows to Rich and get his sign-off before Task 13. Rows that fail a gate get dropped to Rejects rather than fixed by hand.

- [ ] **Step 6: Commit**

```bash
git add qa.py tests/test_qa.py
git commit -m "feat: QA gates blocking upload on contactability, names and liveness"
```

---

### Task 13: Google Sheet upload

**Files:**
- Create: `upload_sheet.py` (adapts `~/.claude/bob-miami-150/upload_master.py`)
- Test: `tests/test_upload_sheet.py`

**Interfaces:**
- Consumes: `records.read_jsonl`, `qa.run_gates`
- Produces:
  - `upload_sheet.build_tabs(rows: list[dict], meta: dict) -> dict[str, list[list]]`
  - a Google Sheet with tabs `Master`, `Tier 1 Deep`, `Method and Sources`, `Rejects`

**Auth note:** `bob-miami-150/upload_master.py` reads an OAuth token from `~/.config/gspread/authorized_user.json` with scopes `spreadsheets` and `drive.file`, and refreshes it when stale. Reuse that block verbatim. Create the Sheet in the same Drive folder as the previous target lists.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_upload_sheet.py
import pytest
from upload_sheet import MASTER_HEADERS, TIER1_HEADERS, build_tabs

MASTER_ROW = {"name": "Rivera Mechanical", "domain": "rivera.com", "city": "Austin",
              "state": "TX", "phone": "+15125550111", "email": "info@rivera.com",
              "email_status": "generic", "category": "HVAC", "score": 62,
              "tier": "master", "sources": ["maps", "sba_7a"],
              "signals": {"reviews": 212, "jobs_supported": 14}}
TIER1_ROW = dict(MASTER_ROW, name="Summit Roofing", tier="tier1",
                 contact_name="Maria Gonzalez", contact_title="Owner",
                 contact_email="maria@summit.com", contact_email_status="verified",
                 hook="Summit Roofing is hiring a bookkeeper.")
REJECT_ROW = dict(MASTER_ROW, name="Tiny Shop", tier="reject",
                  reject_reason="score 12 below floor 35")

META = {"run_date": "2026-08-26", "apify_spend": 0.0, "hunter_used": 40,
        "sources": {"sba_7a": 200, "maps": 900, "jobs": 120}}


def test_master_tab_has_header_and_both_kept_tiers():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    assert tabs["Master"][0] == MASTER_HEADERS
    assert len(tabs["Master"]) == 3  # header plus master plus tier1


def test_tier1_tab_only_contains_tier1_rows():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    assert tabs["Tier 1 Deep"][0] == TIER1_HEADERS
    assert len(tabs["Tier 1 Deep"]) == 2
    assert tabs["Tier 1 Deep"][1][0] == "Summit Roofing"


def test_rejects_tab_carries_the_reason():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    assert any("below floor" in str(cell) for cell in tabs["Rejects"][1])


def test_method_tab_records_spend_and_source_counts():
    tabs = build_tabs([MASTER_ROW], META)
    flat = " ".join(str(c) for row in tabs["Method and Sources"] for c in row)
    assert "2026-08-26" in flat
    assert "sba_7a" in flat


def test_every_cell_is_a_primitive():
    tabs = build_tabs([MASTER_ROW, TIER1_ROW, REJECT_ROW], META)
    for rows in tabs.values():
        for row in rows:
            for cell in row:
                assert isinstance(cell, (str, int, float)), f"{cell!r} is not a primitive"


def test_master_sorted_by_score_descending():
    low = dict(MASTER_ROW, name="Low", score=40)
    high = dict(MASTER_ROW, name="High", score=90)
    tabs = build_tabs([low, high], META)
    assert tabs["Master"][1][0] == "High"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_upload_sheet.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'upload_sheet'`

- [ ] **Step 3: Implement `build_tabs` in `upload_sheet.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-api-python-client", "google-auth", "google-auth-oauthlib"]
# ///
"""Publish the finished list as one four-tab Google Sheet."""
import json

import config
from lib.records import read_jsonl

MASTER_HEADERS = ["Company", "Domain", "City", "State", "Phone", "Email",
                  "Email status", "Category", "Score", "Tier", "Signals", "Sources"]
TIER1_HEADERS = MASTER_HEADERS + ["Contact name", "Contact title", "Contact email",
                                  "Contact email status", "Hook"]
REJECT_HEADERS = ["Company", "City", "State", "Score", "Reason"]


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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_upload_sheet.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Add the QA guard and the Sheets client**

Add a `main()` that refuses to run when `data/qa_report.json` is missing or reports `failed > 0`:

```python
def main():
    report = json.loads((config.DATA / "qa_report.json").read_text(encoding="utf-8"))
    if report.get("failed", 1) > 0:
        raise SystemExit(f"QA gate failed on {report['failed']} rows. "
                         f"Fix or reject them before uploading.")
    ...
```

Then copy the credential-loading and `build("sheets", "v4", ...)` block from
`~/.claude/bob-miami-150/upload_master.py` verbatim, create a new spreadsheet titled
`BOB Startup Leads — Master List`, and write each tab from `build_tabs` with
`spreadsheets().values().update`. Freeze the header row on every tab.

- [ ] **Step 6: Run the full upload**

Run: `uv run upload_sheet.py`
Expected: a printed Sheet URL. Open it and confirm all four tabs are populated, the header rows are frozen, and no cell shows a raw Python dict.

- [ ] **Step 7: Commit**

```bash
git add upload_sheet.py tests/test_upload_sheet.py
git commit -m "feat: four-tab Google Sheet upload behind the QA gate"
```

---

## End-to-end run order

```bash
cd ~/.claude/bob-startup-leads
uv run seed_sba.py --limit-7a 4000 --limit-ppp 1000
uv run seed_jobs.py
uv run seed_maps.py
uv run dedupe.py
uv run resolve_domain.py
uv run site_scrape.py
uv run signals.py
uv run score.py          # tune SCORE_FLOOR here against TARGET_MASTER_ROWS
uv run enrich_tier1.py
uv run hooks.py
uv run qa.py             # show the 25-row sample to Rich, get sign-off
uv run upload_sheet.py
```

`dedupe.py` runs before `resolve_domain.py` so Brave lookups are never spent twice on
the same company.

## Self-Review

**Spec coverage.** Every spec section maps to a task: three seed lanes (Tasks 2, 3, 4),
dedupe and identity (Task 6), scoring across four families (Task 9), the cost-ordered
waterfall (Task 10), hooks (Task 11), all five QA gates (Task 12), and the four-tab
output (Task 13). Task 5 is new since the spec: SBA and job rows arrive with no
website, and every downstream stage is keyed on domain.

**Deviations from the spec, deliberate.**
- Spec open item 1 is resolved. Both SBA URLs and schemas were verified live on
  2026-08-26 and are hardcoded in `config.py`. SBA 7(a) FY2020-Present is current to
  2026-06-30, so it is the primary financial seed and PPP is secondary.
- The spec's step 3 (state registry officer lookup) is scoped to Florida only.
  Generalizing registry lookup across 50 states is its own project.
- Apify in `waterfall()` charges the budget and flags the row rather than calling the
  actor. Wiring the actor is a follow-up once Rich confirms the current account cap,
  which was previously blown at $55.73 against a $50 ceiling.

**Placeholder scan.** No TBDs. Every code step carries runnable code, every test step
carries real assertions, every run step states its expected output.

**Type consistency.** `company_id`, `read_jsonl`, `write_jsonl`, `norm_name`,
`norm_phone`, `registrable_domain` and `is_valid_person_name` keep the same signatures
from Task 1 through Task 13. The record shape declared in `lib/records.FIELDS` is what
every stage reads and writes, with `contact_*` keys added only at Task 10 and `hook`
only at Task 11.
