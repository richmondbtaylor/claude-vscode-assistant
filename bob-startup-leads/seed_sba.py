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
    """Parse a numeric string, tolerant of float-formatted integers.

    Real SBA data writes JobsSupported as "9.0", not "9" - int("9.0") raises
    ValueError, so we always parse through float first and cast from there.
    """
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return cast(parsed)


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
