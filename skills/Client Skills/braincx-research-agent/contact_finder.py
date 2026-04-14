"""
Contact enrichment — finds phone number and website for a business.

Strategy:
1. Search for company homepage directly (just company name, no "phone number" bias)
2. Scrape homepage + contact page for phone number
3. Fall back to snippet extraction if scraping fails

This avoids data broker sites dominating "phone number contact" queries.
"""

import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

_BRAVE_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2

_SKIP_DOMAINS = {
    "indeed.com", "linkedin.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com", "simplyhired.com", "facebook.com",
    "yelp.com", "yellowpages.com", "bbb.org", "healthgrades.com",
    "vitals.com", "zocdoc.com", "wikipedia.org", "google.com",
    "maps.google.com", "bing.com", "mapquest.com",
    # Data brokers — always skip
    "zoominfo.com", "leadiq.com", "contactout.com", "apollo.io",
    "rocketreach.com", "rocketreach.co", "hunter.io", "spokeo.com",
    "whitepages.com", "crunchbase.com", "dnb.com", "owler.com", "manta.com",
    "pissedconsumer.com", "complaintsboard.com", "ripoffreport.com",
    "signalhire.com", "lusha.com", "clearbit.com", "uplead.com",
    "reddit.com", "quora.com", "trustpilot.com", "similarweb.com", "semrush.com",
}


@dataclass
class ContactInfo:
    phone: str = ""
    website: str = ""
    address: str = ""


_PHONE_RE = re.compile(
    r"""(?:\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})""",
    re.VERBOSE,
)
_NOT_PHONE_RE = re.compile(r"^\d{5}$|^\d{9,}$")


def _extract_phone(text: str) -> str:
    for match in _PHONE_RE.finditer(text):
        raw = match.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 10 and not _NOT_PHONE_RE.match(digits):
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return ""


def _is_skip_domain(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return any(s in domain for s in _SKIP_DOMAINS)
    except Exception:
        return True


def _brave_search(query: str, api_key: str, count: int = 5) -> list[dict]:
    try:
        resp = requests.get(
            _BRAVE_BASE_URL,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            params={"q": query, "count": count, "text_decorations": "false", "search_lang": "en"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])
    except Exception:
        return []


def _scrape_for_phone(url: str) -> str:
    """Fetch a page and extract the first US phone number."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BrainCX-Enricher/1.0)"},
            timeout=8,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return ""
        # Strip HTML tags for cleaner text
        text = re.sub(r"<[^>]+>", " ", resp.text)
        return _extract_phone(text)
    except Exception:
        return ""


def _find_homepage(company_name: str, api_key: str) -> str:
    """Find the company's official homepage via Brave search."""
    # First try: just the company name — tends to return their homepage first
    results = _brave_search(f'"{company_name}" official site', api_key, count=7)
    time.sleep(_REQUEST_DELAY)

    for r in results:
        url = r.get("url", "")
        if not url or _is_skip_domain(url):
            continue
        # Prefer URLs that look like homepages (no deep paths)
        path = urlparse(url).path.rstrip("/")
        if path.count("/") <= 1:
            return url

    # Second try: any non-broker result
    for r in results:
        url = r.get("url", "")
        if url and not _is_skip_domain(url):
            return url

    return ""


def lookup(company_name: str, location: str = "", platform: str = "") -> ContactInfo:
    """
    Look up contact info for a business.
    Returns ContactInfo with whatever was found.
    """
    api_key = os.environ.get("BRAVE_API_KEY", "").strip()
    if not api_key or not company_name or company_name.lower() in ("unknown", ""):
        return ContactInfo()

    aggregate_hints = ["apply today", "jobs employment", "job vacancies", "work from home jobs"]
    if any(h in company_name.lower() for h in aggregate_hints):
        return ContactInfo()

    # Step 1: Find the company's actual homepage
    homepage = _find_homepage(company_name, api_key)

    # Step 2: Scrape homepage + /contact for phone
    phone = ""
    if homepage:
        phone = _scrape_for_phone(homepage)
        if not phone:
            base = homepage.rstrip("/")
            for suffix in ["/contact", "/contact-us", "/about"]:
                phone = _scrape_for_phone(base + suffix)
                if phone:
                    break
                time.sleep(0.2)

    # Step 3: If no phone from scraping, try snippet extraction
    if not phone:
        results = _brave_search(f'"{company_name}" {location} phone'.strip(), api_key, count=5)
        time.sleep(_REQUEST_DELAY)
        for r in results:
            text = r.get("title", "") + " " + r.get("description", "")
            phone = _extract_phone(text)
            if phone:
                break

    if phone or homepage:
        print(f"[contact] {company_name}: phone={phone or 'n/a'} | site={homepage[:60] if homepage else 'n/a'}")

    return ContactInfo(phone=phone, website=homepage)
