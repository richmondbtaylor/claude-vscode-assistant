"""Scale, intent and credibility signals for companies that have a domain.

Runs only against companies that already cleared the site scrape with a
domain (data/sites.jsonl), never the whole seed pool. This is the slowest,
most rate-limited stage in the pipeline: two Brave queries per company plus
one LinkedIn page load, so it defaults to a small --limit and checkpoints
with append_jsonl so an interrupted run is resumable.

Usage: uv run signals.py [--limit N]
Input: data/sites.jsonl
Output: data/signals.jsonl
"""
import argparse
import json
import os
import pathlib
import re
import time

import tldextract
from playwright.sync_api import sync_playwright

import config
from lib.normalize import NON_COMPANY_HOSTS, norm_name, registrable_domain
from lib.records import append_jsonl, company_id, read_jsonl
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

# RULING C33: a Brave result only counts as press evidence when its own
# title/description names the company AND carries one of these terms.
# Brave returns something for almost any query, so raw result count is
# close to a constant and is not evidence about the company by itself.
_PRESS_TERM_RE = re.compile(
    r"\b(raised|raises|acquired|acquisition|acquires|expands?|expansion|"
    r"funding|funded|named|award(?:ed)?|series [a-z]\b|investment|merger)\b",
    re.I,
)

# RULING C34: LinkedIn's soft-404 renders as a normal 200 page with this
# kind of copy rather than an HTTP 404, so a real HTTP 404 status is
# checked first and this text is the fallback.
_NOT_FOUND_MARKERS = (
    "page not found",
    "this page doesn't exist",
    "sorry, we couldn't find that page",
)

# Key name looked up inside each ~/.claude/security/*.env file when
# LINKEDIN_COOKIES_FILE is not already set in the environment.
_SECURITY_DIR = pathlib.Path.home() / ".claude" / "security"
_LINKEDIN_KEY = "LINKEDIN_COOKIES_FILE"


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


def _is_directory_or_social_host(url: str) -> bool:
    """RULING C36: a directory or badge-listing page (angi, buildzoom, the
    company's own Facebook post, etc.) names the company and often carries
    the word "award" on a certification badge, which is exactly the false
    positive pattern press scoring needs to reject. Reuses the same
    NON_COMPANY_HOSTS set registrable_domain already maintains rather than
    keeping a second list in sync."""
    ext = tldextract.extract(url or "")
    return ext.domain.lower() in NON_COMPANY_HOSTS


def _mentions_company(text: str, target: str) -> bool:
    """RULING C36: whole-word match, not a raw substring. Without a
    boundary, target "roof x" (from a company literally named "Roof X")
    is a substring of "roof xpress", a different company entirely."""
    if not target:
        return False
    return bool(re.search(r"\b" + re.escape(target) + r"\b", norm_name(text)))


def score_press_results(results: list[dict], name: str, domain: str | None = None) -> int:
    """Count only results that actually name the company AND carry a press
    or funding term, excluding directory/social listing pages and the
    company's own site. RULING C33: a result whose title/description
    mentions neither is not evidence about that company, and raw Brave
    volume alone is close to a constant across almost any query. RULING
    C36: directory/badge hosts are excluded outright, and the name match
    is whole-word anchored. RULING C37: press coverage is third-party by
    definition, so a result on the company's own domain is excluded too;
    domain is optional and a falsy value simply skips that check (a row
    with no domain never reaches this function via press_hits anyway,
    since main() returns it unchanged before any query is spent)."""
    target = norm_name(name)
    if not target:
        return 0
    own_domain = domain.lower() if domain else None
    count = 0
    for r in results:
        url = r.get("url", "")
        if _is_directory_or_social_host(url):
            continue
        if own_domain and registrable_domain(url) == own_domain:
            continue
        text = f"{r.get('title', '')} {r.get('description', '')}"
        if _mentions_company(text, target) and _PRESS_TERM_RE.search(text):
            count += 1
    return count


def press_hits(name: str, city: str, domain: str | None = None) -> int:
    """Count news and funding mentions that actually name the company on a
    third-party site. RULING C33/C36/C37: filtered through
    score_press_results rather than a raw result count; domain is threaded
    through so a result on the company's own site is excluded."""
    query = f'"{name}" ({city}) (raised OR acquired OR expands OR "named" OR award)'
    try:
        results = brave_search(query, count=10)
    except Exception:
        return 0
    return score_press_results(results, name, domain)


def marketplace_presence(name: str, domain: str) -> list[str]:
    try:
        return score_marketplace_results(brave_search(f'"{name}" {domain} reviews', count=10))
    except Exception:
        return []


def _linkedin_company_url(domain: str) -> str:
    """Build the guessed LinkedIn company page URL from a domain. RULING
    C34: this slug guess is deliberately left as-is; there is no live
    session to validate a smarter guess against, and guessing harder
    without feedback is how this pipeline picked up earlier false-positive
    bugs."""
    slug = domain.split(".")[0]
    return f"https://www.linkedin.com/company/{slug}/about/"


def _looks_like_not_found(body: str, status: int | None) -> bool:
    """True if the response looks like a dead slug guess rather than a real
    company page: either a genuine HTTP 404, or LinkedIn's soft-404 (200
    status, "page not found" style copy in the body)."""
    if status == 404:
        return True
    low = (body or "").lower()
    return any(marker in low for marker in _NOT_FOUND_MARKERS)


def linkedin_headcount(page, domain: str) -> int | None:
    """Read the employee band off a LinkedIn company page using the saved
    session. RULING C34: "page not found" (wrong slug guess) and "page
    found but no headcount text" are both returned as None to match the
    int|None contract, but are recorded distinctly via a log line, so a
    run against a restored session can tell a wrong slug from a genuine
    miss by reading the log rather than guessing."""
    url = _linkedin_company_url(domain)
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(1500)
        body = page.inner_text("body")[:6000]
    except Exception:
        print(f"[linkedin_headcount] navigation failed for domain={domain}", flush=True)
        return None

    status = getattr(response, "status", None) if response is not None else None
    if _looks_like_not_found(body, status):
        print(f"[linkedin_headcount] page not found (slug guess likely wrong) "
              f"for domain={domain}", flush=True)
        return None

    headcount = parse_headcount(body)
    if headcount is None:
        print(f"[linkedin_headcount] page found but no headcount text "
              f"for domain={domain}", flush=True)
    return headcount


def _linkedin_cookies_path() -> pathlib.Path | None:
    """Resolve the saved LinkedIn session cookie file. Checks the
    LINKEDIN_COOKIES_FILE environment variable first, then the same key
    inside every ~/.claude/security/*.env file. The value itself is a path,
    never hardcoded here and never logged. A relative value is resolved
    against a few plausible working directories since it was authored for
    a different script's cwd."""
    raw = os.environ.get(_LINKEDIN_KEY)
    if not raw and _SECURITY_DIR.exists():
        for env_file in sorted(_SECURITY_DIR.glob("*.env")):
            try:
                text = env_file.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                if line.startswith(_LINKEDIN_KEY + "="):
                    raw = line.split("=", 1)[1].strip()
                    break
            if raw:
                break
    if not raw:
        return None

    candidate = pathlib.Path(raw)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    for base in (pathlib.Path.cwd(), pathlib.Path.home(), pathlib.Path(__file__).resolve().parent.parent):
        resolved = base / candidate
        if resolved.exists():
            return resolved
    return None


def _linkedin_authenticated(page) -> bool:
    """True if the saved session is actually logged in, not bounced to a
    login wall or checkpoint challenge. Reviewer-confirmed: this probe
    hits linkedin.com/feed/ directly and is independent of any per-row
    slug-guess logic."""
    try:
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1200)
        url = page.url.lower()
        return "login" not in url and "authwall" not in url and "checkpoint" not in url
    except Exception:
        return False


def _open_linkedin_page(pw):
    """Open ONE browser context using the saved LinkedIn session cookies and
    return (browser, page) if the session authenticates, else (browser or
    None, None). Caller is responsible for closing the browser."""
    cookie_path = _linkedin_cookies_path()
    if not cookie_path:
        print("LINKEDIN_COOKIES_FILE not found (env or ~/.claude/security/*.env); "
              "skipping LinkedIn headcount lookups for this run", flush=True)
        return None, None

    browser = pw.chromium.launch(headless=True)
    try:
        cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        if _linkedin_authenticated(page):
            return browser, page
        print("LinkedIn saved session did not authenticate (login wall or checkpoint "
              "detected); skipping LinkedIn headcount lookups for this run", flush=True)
        browser.close()
        return None, None
    except Exception as exc:
        print(f"LinkedIn browser setup failed ({type(exc).__name__}); "
              "skipping LinkedIn headcount lookups for this run", flush=True)
        browser.close()
        return None, None


def _row_key(row: dict) -> str:
    """Stable resume key for a row. RULING C35: falls back from company_id
    (which can be falsy or missing on an older/malformed row) to domain,
    then to normalized name plus state, using the same canonical identity
    function every other stage uses, so every row gets a stable key and
    none is silently reprocessed and duplicated on resume."""
    cid = row.get("company_id")
    if cid:
        return cid
    return company_id(row.get("name", ""), row.get("state", ""), row.get("domain"))


def process_row(row: dict, page) -> dict:
    """Enrich one row with headcount, marketplaces and press hits. A row
    with no domain is returned unchanged, no query spent. Never touches
    disk; the caller checkpoints."""
    domain = row.get("domain")
    if not domain:
        return row
    sig = row.setdefault("signals", {})
    sig["headcount"] = linkedin_headcount(page, domain) if page else None
    sig["marketplaces"] = marketplace_presence(row["name"], domain)
    sig["press_hits"] = press_hits(row["name"], row.get("city", ""), domain)
    return row


def main(limit: int | None = 20):
    # Resume: a row already checkpointed to signals.jsonl is skipped, so an
    # interrupted run (this is the slowest, most rate-limited stage) can
    # restart without duplicating rows or re-spending Brave/LinkedIn budget.
    done_keys = {_row_key(row) for row in read_jsonl(config.DATA / "signals.jsonl")}
    all_rows = list(read_jsonl(config.DATA / "sites.jsonl"))
    skipped = sum(1 for r in all_rows if _row_key(r) in done_keys)
    pending = [r for r in all_rows if _row_key(r) not in done_keys]
    if limit:
        pending = pending[:limit]
    with_domain = sum(1 for r in pending if r.get("domain"))
    print(f"{len(pending)} rows to process this run ({with_domain} with a domain), "
          f"{skipped} already done and skipped", flush=True)

    browser = page = pw = None
    if with_domain:
        pw = sync_playwright().start()
        browser, page = _open_linkedin_page(pw)

    n = hc_hits = mk_hits = press_total = 0
    try:
        for row in pending:
            had_domain = bool(row.get("domain"))
            result = process_row(row, page)

            if had_domain:
                sig = result.get("signals", {})
                if sig.get("headcount") is not None:
                    hc_hits += 1
                if sig.get("marketplaces"):
                    mk_hits += 1
                press_total += sig.get("press_hits", 0) or 0

            append_jsonl(config.DATA / "signals.jsonl", [result])
            n += 1

            if had_domain:
                if page:
                    time.sleep(2.0)  # LinkedIn pacing, separate from Brave's budget
                time.sleep(1.1)  # Brave free tier is rate limited to about 1 qps

            if n % 10 == 0:
                print(f"  {n}/{len(pending)} processed, {hc_hits} headcounts, "
                      f"{mk_hits} with marketplace hit, {press_total} press hits so far",
                      flush=True)
    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()

    print(f"DONE: {n} rows processed this run, {hc_hits} headcounts resolved, "
          f"{mk_hits} rows with a marketplace hit, {press_total} total press hits "
          f"-> data/signals.jsonl", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20,
                     help="max rows to process this run (each row with a domain "
                          "costs 2 Brave queries plus one LinkedIn page load)")
    args = ap.parse_args()
    main(limit=args.limit)
