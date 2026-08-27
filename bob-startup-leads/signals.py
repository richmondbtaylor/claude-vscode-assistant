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

import config
from lib.records import append_jsonl, read_jsonl
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
    login wall or checkpoint challenge."""
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


def main(limit: int | None = 20):
    # Resume: a company_id already written to signals.jsonl is skipped, so
    # an interrupted run (this is the slowest, most rate-limited stage) can
    # restart without duplicating rows or re-spending Brave/LinkedIn budget.
    done_ids = {row.get("company_id") for row in read_jsonl(config.DATA / "signals.jsonl")
                if row.get("company_id")}
    all_rows = list(read_jsonl(config.DATA / "sites.jsonl"))
    skipped = sum(1 for r in all_rows if r.get("company_id") in done_ids)
    pending = [r for r in all_rows if r.get("company_id") not in done_ids]
    if limit:
        pending = pending[:limit]
    with_domain = sum(1 for r in pending if r.get("domain"))
    print(f"{len(pending)} rows to process this run ({with_domain} with a domain), "
          f"{skipped} already done and skipped", flush=True)

    browser = page = None
    if with_domain:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser, page = _open_linkedin_page(pw)
    else:
        pw = None

    n = hc_hits = mk_hits = press_total = 0
    try:
        for row in pending:
            domain = row.get("domain")
            if not domain:
                # No domain: nothing to look up, no query spent, pass through
                # unchanged.
                append_jsonl(config.DATA / "signals.jsonl", [row])
                n += 1
                continue

            sig = row.setdefault("signals", {})

            sig["headcount"] = linkedin_headcount(page, domain) if page else None
            if sig["headcount"] is not None:
                hc_hits += 1
            if page:
                time.sleep(2.0)  # LinkedIn pacing, separate from Brave's budget

            sig["marketplaces"] = marketplace_presence(row["name"], domain)
            if sig["marketplaces"]:
                mk_hits += 1
            hits = press_hits(row["name"], row.get("city", ""))
            sig["press_hits"] = hits
            press_total += hits

            append_jsonl(config.DATA / "signals.jsonl", [row])
            n += 1
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
