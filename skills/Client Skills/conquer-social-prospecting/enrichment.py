"""
Decision maker enrichment for Conquer.io leads.
Tries Hunter.io if API key is set, otherwise generates a realistic demo-grade guess.
"""

import os
import re
import time

import requests

_HUNTER_KEY = os.environ.get("HUNTER_API_KEY", "").strip()


def _domain_from_company(company: str) -> str:
    """Best-effort: convert a company name to a likely .com domain."""
    if not company or company.lower() in ("unknown", ""):
        return ""
    slug = re.sub(r"[^a-z0-9]", "", company.lower().replace(" ", ""))
    # Strip common suffixes
    for suffix in ("inc", "llc", "corp", "ltd", "co"):
        if slug.endswith(suffix):
            slug = slug[: -len(suffix)]
    return f"{slug}.com" if slug else ""


def _hunter_lookup(domain: str) -> dict:
    """Call Hunter.io domain-search and return the best match."""
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": _HUNTER_KEY, "limit": 3, "type": "personal"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        emails = data.get("emails", [])
        # Prefer VP/Director/CRO
        priority_titles = ("vp", "director", "cro", "head of sales", "revenue", "chief")
        for e in emails:
            title = (e.get("position") or "").lower()
            if any(t in title for t in priority_titles):
                return {
                    "email": e.get("value", ""),
                    "first_name": e.get("first_name", ""),
                    "last_name": e.get("last_name", ""),
                    "title": e.get("position", ""),
                    "confidence": e.get("confidence", 0),
                    "source": "hunter.io",
                }
        # Fall back to first result
        if emails:
            e = emails[0]
            return {
                "email": e.get("value", ""),
                "first_name": e.get("first_name", ""),
                "last_name": e.get("last_name", ""),
                "title": e.get("position", ""),
                "confidence": e.get("confidence", 0),
                "source": "hunter.io",
            }
    except Exception as ex:
        print(f"[enrichment] Hunter.io error for {domain}: {ex}")
    return {}


def enrich(company_name: str, job_title: str = "unknown") -> dict:
    """
    Return enrichment dict with keys: email, first_name, last_name, title, confidence, source.
    Returns empty dict if no verified data is available — never fabricates contacts.

    To enable enrichment: set HUNTER_API_KEY in .env (https://hunter.io — free tier 25/mo).
    """
    if not company_name or company_name.lower() in ("unknown", ""):
        return {}

    if not _HUNTER_KEY:
        return {}  # No key = no enrichment. Better empty than wrong.

    domain = _domain_from_company(company_name)
    if not domain:
        return {}

    result = _hunter_lookup(domain)
    if result:
        time.sleep(0.5)  # Hunter free tier rate limit
    return result
