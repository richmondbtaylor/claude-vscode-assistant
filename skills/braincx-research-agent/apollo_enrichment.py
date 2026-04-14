"""
Apollo.io People Search enrichment for BrainCX leads.
Targets SMB decision-makers: practice managers, office managers, owners, etc.
Set APOLLO_API_KEY in .env to enable. Falls back gracefully if not set.
"""

import os
import re
import time

import requests

_APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "").strip()
_APOLLO_URL = "https://api.apollo.io/v1/mixed_people/api_search"

# ICP-specific titles per BrainCX target verticals
_TITLES_BY_ICP = {
    "healthcare": [
        "Practice Manager", "Office Manager", "Practice Administrator",
        "Clinic Administrator", "Clinic Manager", "Front Office Manager",
        "Medical Director", "Operations Manager", "Hospital Administrator",
    ],
    "immigration": [
        "Managing Partner", "Firm Administrator", "Office Manager",
        "Operations Manager", "Owner", "Partner",
    ],
    "general_legal": [
        "Managing Partner", "Firm Administrator", "Office Manager",
        "Operations Manager", "Owner", "Partner",
    ],
    "home_services": [
        "Owner", "General Manager", "Operations Manager",
        "Office Manager", "President", "CEO",
    ],
}

_TITLES_DEFAULT = [
    "Practice Manager", "Office Manager", "Practice Administrator",
    "Clinic Administrator", "Operations Manager", "Managing Partner",
    "Firm Administrator", "Office Director", "Owner", "President",
    "CEO", "General Manager", "Business Owner", "Administrator",
]

_SENIORITY_FILTER = ["owner", "c_suite", "director", "manager", "partner"]


def _clean_last_name(obfuscated: str) -> str:
    if not obfuscated:
        return ""
    return re.sub(r"\*+\w*$", ".", obfuscated).strip()


def enrich(company_name: str, icp_category: str = "") -> dict:
    """
    Return enrichment dict: first_name, last_name, title, email, source.
    Returns empty dict if no key set or no match found.
    """
    if not _APOLLO_KEY or not company_name or company_name.lower() in ("unknown", ""):
        return {}

    headers = {"Content-Type": "application/json", "X-Api-Key": _APOLLO_KEY}
    titles = _TITLES_BY_ICP.get(icp_category, _TITLES_DEFAULT)

    def _search(extra: dict) -> list:
        try:
            resp = requests.post(
                _APOLLO_URL,
                headers=headers,
                json={"q_organization_name": company_name, "per_page": 5, **extra},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("people", [])
        except Exception as ex:
            print(f"[apollo] Error for '{company_name}': {ex}")
            return []

    # Pass 1: title-filtered
    people = _search({"person_titles": titles, "person_seniorities": _SENIORITY_FILTER})

    # Pass 2: seniority-only fallback
    if not people:
        people = _search({"person_seniorities": _SENIORITY_FILTER})

    if not people:
        return {}

    # Prefer management/operations titles
    best = None
    for p in people:
        t = (p.get("title") or "").lower()
        if any(w in t for w in ("manager", "administrator", "owner", "partner", "director", "ceo")):
            best = p
            break
    if not best:
        best = people[0]

    first = best.get("first_name", "")
    last = _clean_last_name(best.get("last_name_obfuscated", ""))
    title = best.get("title", "")
    has_email = best.get("has_email", False)

    time.sleep(0.3)
    return {
        "first_name": first,
        "last_name": last,
        "title": title,
        "email": "Reveal in Apollo" if has_email else "",
        "source": "apollo.io",
    }
