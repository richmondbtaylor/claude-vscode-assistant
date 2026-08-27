"""Scrape company websites for contact data and payment-tech fingerprints.

Port of ~/.claude/bob-miami-150/site_scrape.py. Reuses its fetch, path-walk,
email regex, junk filter and ThreadPoolExecutor main loop. Drops the loose
NAME_RE owner-extraction block entirely (that regex is what produced junk
contact names like "Get Ah" in the previous production run); name extraction
is handled in a later task using lib.normalize.is_valid_person_name.

Usage: uv run site_scrape.py [--limit N]
Input: data/resolved.jsonl
Output: data/sites.jsonl
"""
import argparse
import json
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

import config
from lib.normalize import norm_phone
from lib.records import append_jsonl, read_jsonl

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
           "Accept-Language": "en-US,en;q=0.9"}
PATHS = ["", "contact", "contact-us", "about", "about-us", "team", "our-team", "staff"]
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
JUNK = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", ".gif", ".webp",
        ".svg", "sentry.io", "schema.org", "godaddy", "@sentry", "no-reply",
        "noreply", "yourdomain", "domain.com", "email.com", "@email", "u003e",
        "squarespace")

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


def fetch(url):
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12, follow_redirects=True)
        if r.status_code == 200 and "text/html" in r.headers.get("content-type", "html"):
            return r.text
    except Exception:
        pass
    return None


def clean_emails(found: set[str], domain: str) -> list[str]:
    """Filter asset and vendor noise, prefer addresses on the company domain."""
    keep = []
    for email in found:
        low = email.lower().strip(".")
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


def scrape_domain(root_url: str, domain: str) -> dict:
    """Walk the standard path set for one site, returning everything the
    money-scoring stage needs: emails, phone, tech fingerprint and the
    pricing/careers page booleans."""
    found_emails = set()
    phone = None
    sources = []
    pages_ok = 0
    has_pricing_page = False
    has_careers_page = False

    for path in PATHS:
        url = urljoin(root_url if root_url.endswith("/") else root_url + "/", path)
        html = fetch(url)
        if not html:
            continue
        pages_ok += 1
        sources.append(html)
        found_emails |= set(EMAIL_RE.findall(html))
        try:
            text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        except Exception:
            text = ""
        found_emails |= set(EMAIL_RE.findall(text))
        if phone is None:
            jsonld = extract_jsonld_org(html)
            if jsonld.get("phone"):
                phone = jsonld["phone"]
        time.sleep(random.uniform(0.3, 0.9))
        if pages_ok >= 5 and found_emails:
            break

    for extra_path in ("pricing", "careers"):
        url = urljoin(root_url if root_url.endswith("/") else root_url + "/", extra_path)
        ok = fetch(url) is not None
        if extra_path == "pricing":
            has_pricing_page = ok
        else:
            has_careers_page = ok
        time.sleep(random.uniform(0.3, 0.9))

    if phone is None:
        for html in sources:
            m = re.search(r"(\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", html)
            if m:
                phone = norm_phone(m.group(1))
                if phone:
                    break

    emails = clean_emails(found_emails, domain)
    tech = fingerprint_tech(" ".join(sources))

    return {
        "emails": emails,
        "phone": phone,
        "tech": tech,
        "has_pricing_page": has_pricing_page,
        "has_careers_page": has_careers_page,
        "pages_fetched": pages_ok,
    }


def scrape_row(row: dict) -> dict:
    """Enrich one canonical record with site-scrape results. RULING C5: tech,
    has_pricing_page and has_careers_page nest under row['signals']; email,
    email_status and phone stay top-level. A row with no domain cannot be
    scraped and passes through unchanged."""
    domain = row.get("domain")
    website = row.get("website")
    if not domain or not website:
        return row

    result = scrape_domain(website, domain)

    if result["emails"]:
        row["email"] = result["emails"][0]
        row["email_status"] = classify_email(result["emails"][0], domain)
    if result["phone"] and not row.get("phone"):
        row["phone"] = result["phone"]

    signals = dict(row.get("signals") or {})
    signals["tech"] = result["tech"]
    signals["has_pricing_page"] = result["has_pricing_page"]
    signals["has_careers_page"] = result["has_careers_page"]
    row["signals"] = signals
    return row


def main(limit: int | None = None, workers: int = 12):
    rows = list(read_jsonl(config.DATA / "resolved.jsonl"))
    if limit:
        rows = rows[:limit]
    print(f"{len(rows)} rows to scrape ({workers} workers)", flush=True)

    lock = threading.Lock()
    counter = {"n": 0, "hits": 0, "tech": 0}

    def work(row):
        try:
            res = scrape_row(row)
        except Exception:
            res = row
        with lock:
            append_jsonl(config.DATA / "sites.jsonl", [res])
            counter["n"] += 1
            if res.get("email"):
                counter["hits"] += 1
            if res.get("signals", {}).get("tech"):
                counter["tech"] += 1
            if counter["n"] % 50 == 0:
                print(f"  {counter['n']}/{len(rows)} done, "
                      f"{counter['hits']} with email, {counter['tech']} with tech",
                      flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(work, rows))
    print(f"DONE: {counter['n']} rows scraped, {counter['hits']} with email, "
          f"{counter['tech']} with tech -> data/sites.jsonl", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    main(limit=a.limit)
