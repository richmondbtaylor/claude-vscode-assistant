"""Find a company website for seed rows that arrived without one.

Strict on purpose. A wrong domain poisons every downstream stage, so an
unresolved company is preferable to a mismatched one.

RULING C52: this is a network stage (one Brave query per unresolved
company) and gets the same resume discipline as site_scrape.py and
signals.py. It used to rewrite data/resolved.jsonl wholesale on every
run with no memory of what it had already attempted, so a re-run
re-spent one query per company that had already been queried and simply
came back with no match, roughly 74% of the pool at the measured 25.7%
resolve rate. The subtlety: a company that was attempted and did NOT
resolve must still be recorded as attempted (domain_resolve_attempted),
or it is retried forever -- "no domain" and "never tried" would be
indistinguishable on the next run otherwise.
"""
import argparse
import re
import time

from rapidfuzz import fuzz

import config
from lib.records import append_jsonl, read_jsonl, row_key
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

# RULING C18: enumerating "ambiguous" codes (CO for "Company", IN/OR/OK/ME/HI/DE
# for ordinary words, etc.) is a losing game, and a caps-only gate breaks on
# stylized all-caps titles. Instead, a two-letter code counts as a state
# reference ONLY in postal form: preceded by a comma (optional whitespace), or
# immediately followed by a five-digit ZIP. Nothing else counts, in either
# letter case. Full state names still match as whole words/phrases,
# case-insensitively, anywhere -- they carry most real cases, including the
# Collaer/Collier regression, which names "Florida" outright.
_STATE_NAME_PATTERNS = {
    code: re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
    for code, name in US_STATES.items()
}
_STATE_CODE_COMMA_PATTERNS = {
    code: re.compile(r",\s*" + code + r"\b", re.IGNORECASE)
    for code in US_STATES
}
_STATE_CODE_ZIP_PATTERNS = {
    code: re.compile(r"\b" + code + r"(?=\s+\d{5}\b)", re.IGNORECASE)
    for code in US_STATES
}


def _mentioned_states(text: str) -> set[str]:
    """US states named in text: full names anywhere, two-letter codes only
    in postal form (", TX" or "TX 78701")."""
    if not text:
        return set()
    found = set()
    for code, pattern in _STATE_NAME_PATTERNS.items():
        if pattern.search(text):
            found.add(code)
    for code, pattern in _STATE_CODE_COMMA_PATTERNS.items():
        if pattern.search(text):
            found.add(code)
    for code, pattern in _STATE_CODE_ZIP_PATTERNS.items():
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

    out_path = config.DATA / "resolved.jsonl"
    # RULING C52: resume. A row already checkpointed to resolved.jsonl is
    # skipped -- whether it resolved a domain or was genuinely queried and
    # came back with no match (marked via domain_resolve_attempted below).
    # Only the second case is the subtlety: without that marker, a company
    # Brave could never match would be indistinguishable from one never
    # tried, and would be re-queried, and billed, on every future run.
    done_keys = {row_key(row) for row in read_jsonl(out_path)}
    all_rows = list(read_jsonl(config.DATA / args.infile))
    skipped = sum(1 for r in all_rows if row_key(r) in done_keys)
    pending = [r for r in all_rows if row_key(r) not in done_keys]
    print(f"{len(pending)} rows to consider this run, {skipped} already done "
          f"and skipped", flush=True)

    resolved, attempted, n = 0, 0, 0
    for row in pending:
        if not row.get("domain") and attempted >= args.limit:
            # Limit reached this run -- leave it genuinely unattempted (do
            # not checkpoint it) so a future run still considers it.
            continue
        if not row.get("domain"):
            attempted += 1
            query = " ".join(x for x in [row["name"], row.get("city"), row.get("state")] if x)
            try:
                results = brave_search(query, count=8)
            except Exception as exc:
                print(f"skip {row['name']}: {exc}")
                results = None
            if results is not None:
                domain = pick_domain(row["name"], row.get("city", ""),
                                     row.get("state", ""), results)
                if domain:
                    row["domain"] = domain
                    row["website"] = f"https://{domain}"
                    resolved += 1
            time.sleep(1.1)
        # Checkpoint every row this run touches, including one that
        # already had a domain coming in (no query needed) and one that
        # was queried and came back with no match -- both must be marked
        # attempted so a future run does not reconsider them.
        row["domain_resolve_attempted"] = True
        append_jsonl(out_path, [row])
        n += 1

    print(f"attempted {attempted}, resolved {resolved}, wrote {n} rows this run "
          f"-> data/resolved.jsonl")


if __name__ == "__main__":
    main()
