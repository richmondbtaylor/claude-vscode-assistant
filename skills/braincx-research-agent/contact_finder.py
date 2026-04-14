"""
Contact enrichment — finds phone number and website for a business.

Uses Brave Search to look up "{company} {city} phone number" and extracts
contact info from the top result snippets. Only called for Hot/Warm leads
to avoid burning Brave quota on low-quality hits.
"""

import os
import re
import time
from typing import Optional
from dataclasses import dataclass

_BRAVE_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2


@dataclass
class ContactInfo:
    phone: str = ""
    website: str = ""
    address: str = ""


# Regex patterns for US phone numbers
_PHONE_RE = re.compile(
    r"""(?:
        \(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}   # (555) 555-5555 / 555-555-5555
    )""",
    re.VERBOSE,
)

# Patterns that indicate a number is NOT a phone (zip codes, ID numbers, etc.)
_NOT_PHONE_RE = re.compile(r"^\d{5}$|^\d{9,}$")


def _extract_phone(text: str) -> str:
    """Extract the first plausible US phone number from text."""
    for match in _PHONE_RE.finditer(text):
        raw = match.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 10 and not _NOT_PHONE_RE.match(digits):
            # Format as (555) 555-5555
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return ""


def _extract_website(results: list[dict], company_hint: str) -> str:
    """Find the most likely official website URL from search results."""
    skip_domains = {
        "indeed.com", "linkedin.com", "glassdoor.com", "ziprecruiter.com",
        "monster.com", "careerbuilder.com", "simplyhired.com", "facebook.com",
        "yelp.com", "yellowpages.com", "bbb.org", "healthgrades.com",
        "vitals.com", "zocdoc.com", "wikipedia.org", "google.com",
        # Data brokers / aggregators — never the actual company website
        "zoominfo.com", "leadiq.com", "contactout.com", "apollo.io",
        "rocketreach.com", "hunter.io", "spokeo.com", "whitepages.com",
        "crunchbase.com", "dnb.com", "owler.com", "manta.com",
        "pissedconsumer.com", "complaintsboard.com", "ripoffreport.com",
    }
    for r in results:
        url = r.get("url", "")
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
        except Exception:
            continue
        if domain and not any(s in domain for s in skip_domains):
            return url
    return ""


def lookup(company_name: str, location: str = "", platform: str = "") -> ContactInfo:
    """
    Look up contact info for a business.
    Returns ContactInfo with whatever was found (empty strings if not found).
    """
    api_key = os.environ.get("BRAVE_API_KEY", "").strip()
    if not api_key or not company_name or company_name.lower() in ("unknown", ""):
        return ContactInfo()

    # Skip aggregate job board pages — they're not a single company
    aggregate_hints = ["apply today", "jobs employment", "job vacancies", "work from home jobs"]
    if any(h in company_name.lower() for h in aggregate_hints):
        return ContactInfo()

    query = f'"{company_name}" {location} phone number contact'.strip()

    import requests
    try:
        resp = requests.get(
            _BRAVE_BASE_URL,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            params={
                "q": query,
                "count": 5,
                "text_decorations": "false",
                "search_lang": "en",
            },
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
    except Exception as e:
        print(f"[contact] Lookup failed for '{company_name}': {e}")
        return ContactInfo()

    time.sleep(_REQUEST_DELAY)

    phone = ""
    for r in results:
        text = (r.get("title", "") + " " + r.get("description", ""))
        phone = _extract_phone(text)
        if phone:
            break

    website = _extract_website(results, company_name)

    if phone or website:
        print(f"[contact] {company_name}: phone={phone or 'n/a'} | site={website[:50] if website else 'n/a'}")

    return ContactInfo(phone=phone, website=website)
