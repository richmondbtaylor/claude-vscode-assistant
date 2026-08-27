"""Find a company website for seed rows that arrived without one.

Strict on purpose. A wrong domain poisons every downstream stage, so an
unresolved company is preferable to a mismatched one.
"""
import argparse
import re
import time

from rapidfuzz import fuzz

import config
from lib.records import read_jsonl, write_jsonl
from seed_jobs import brave_search
from lib.normalize import norm_name, registrable_domain

MATCH_THRESHOLD = 82

# Domain-stem similarity alone confuses "Collaer Enterprises" with
# "Collier Enterprises" because the generic token "enterprises" dominates
# the ratio. Below this ratio a candidate needs the company's own city or
# state to show up somewhere in its snippet before it is trusted; above it,
# a candidate is trusted unless it names a *different* state outright.
CORROBORATION_RATIO = 90

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

# These two-letter codes double as ordinary English words ("in", "or", "ok",
# "me", "hi", "de"). Brave snippets write real postal abbreviations in caps,
# so for these codes only, require an exact-case whole-word match. Every
# other code (and every full state name) matches case-insensitively.
AMBIGUOUS_STATE_CODES = {"IN", "OR", "OK", "ME", "HI", "DE"}

_STATE_NAME_PATTERNS = {
    code: re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
    for code, name in US_STATES.items()
}
_STATE_CODE_PATTERNS_CI = {
    code: re.compile(r"\b" + code + r"\b", re.IGNORECASE)
    for code in US_STATES if code not in AMBIGUOUS_STATE_CODES
}
_STATE_CODE_PATTERNS_CS = {
    code: re.compile(r"\b" + code + r"\b")  # no IGNORECASE: caps only
    for code in AMBIGUOUS_STATE_CODES
}


def _mentioned_states(text: str) -> set[str]:
    """US state codes named in text, matched as whole words/phrases only."""
    if not text:
        return set()
    found = set()
    for code, pattern in _STATE_NAME_PATTERNS.items():
        if pattern.search(text):
            found.add(code)
    for code, pattern in _STATE_CODE_PATTERNS_CI.items():
        if pattern.search(text):
            found.add(code)
    for code, pattern in _STATE_CODE_PATTERNS_CS.items():
        if pattern.search(text):
            found.add(code)
    return found


def _candidate_text(result: dict) -> str:
    return " ".join(
        str(result.get(k) or "") for k in ("title", "description", "url")
    )


def _conflicting_state(text: str, state: str) -> bool:
    """True if text names a US state other than the company's own."""
    state = (state or "").strip().upper()
    if not state:
        return False  # nothing to conflict with
    return any(code != state for code in _mentioned_states(text))


def _has_location_corroboration(text: str, city: str, state: str) -> bool:
    """True if the company's own city or state shows up in text."""
    city = (city or "").strip()
    if city and re.search(r"\b" + re.escape(city) + r"\b", text, re.IGNORECASE):
        return True
    state = (state or "").strip().upper()
    if state and state in _mentioned_states(text):
        return True
    return False


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
        ratio = fuzz.ratio(target, stem)
        if ratio < MATCH_THRESHOLD:
            continue
        text = _candidate_text(result)
        if _conflicting_state(text, state):
            continue  # names a different state outright: disqualified
        if ratio < CORROBORATION_RATIO and not _has_location_corroboration(text, city, state):
            continue  # below the corroboration floor with no supporting location
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
