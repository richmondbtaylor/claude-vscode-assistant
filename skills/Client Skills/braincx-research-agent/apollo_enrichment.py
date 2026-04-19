"""
Apollo.io enrichment for BrainCX leads.

Uses Apollo's People Search API to find decision-makers at a company
by title, then returns their name, title, and email.

Docs: https://apolloio.github.io/apollo-api-docs/
"""

import os
import time
from dataclasses import dataclass

import requests

_BASE = "https://api.apollo.io/v1"

# ICP-specific decision-maker titles to search for
_DM_TITLES_BY_ICP = {
    "healthcare": [
        "Practice Manager", "Office Manager", "Practice Administrator",
        "Clinic Administrator", "Clinic Manager", "Front Office Manager",
        "Medical Director", "Operations Manager", "Administrator",
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
_DM_TITLES_DEFAULT = [
    "Practice Manager", "Office Manager", "Practice Administrator",
    "Clinic Administrator", "Medical Director", "Operations Manager",
    "Managing Partner", "Firm Administrator", "Owner", "Administrator",
]


@dataclass
class ApolloResult:
    name: str = ""
    title: str = ""
    email: str = ""
    linkedin_url: str = ""
    phone: str = ""


def _headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }


def _enrich_person_email(api_key: str, person_id: str) -> str:
    """
    Try Apollo's contact enrich endpoint to reveal email for a known person ID.
    Returns email string or empty string if unavailable/plan-limited.
    """
    try:
        resp = requests.post(
            f"{_BASE}/contacts/enrich",
            headers=_headers(api_key),
            json={"id": person_id},
            timeout=10,
        )
        if not resp.ok:
            return ""
        data = resp.json()
        contact = data.get("contact") or data.get("person") or {}
        return contact.get("email") or ""
    except Exception:
        return ""


def lookup_person(
    company_name: str,
    domain: str = "",
    icp_category: str = "",
) -> ApolloResult:
    """
    Search Apollo for a decision-maker at the given company.
    Returns the best match: name, title, email.
    """
    api_key = os.environ.get("APOLLO_API_KEY", "").strip()
    if not api_key or not company_name:
        return ApolloResult()

    titles = _DM_TITLES_BY_ICP.get(icp_category.lower(), _DM_TITLES_DEFAULT)

    payload = {
        "q_organization_name": company_name,
        "person_titles": titles[:6],
        "per_page": 5,
        "page": 1,
    }
    if domain:
        payload["q_organization_domains"] = [domain]

    try:
        resp = requests.post(
            f"{_BASE}/mixed_people/api_search",
            headers=_headers(api_key),
            json=payload,
            timeout=15,
        )
        if not resp.ok:
            # Log response body for debugging
            print(f"[apollo] Search failed for {company_name}: {resp.status_code} — {resp.text[:200]}")
            return ApolloResult()
        data = resp.json()
    except Exception as e:
        print(f"[apollo] Search error for {company_name}: {e}")
        return ApolloResult()

    people = data.get("people") or data.get("contacts") or []
    if not people:
        # Log response keys to diagnose empty results (plan limits, etc.)
        keys = list(data.keys())
        total = data.get("pagination", {}).get("total_entries", "?")
        print(f"[apollo] No people for {company_name} — resp keys: {keys}, total_entries: {total}")
        return ApolloResult()

    # Pick the best person — prefer verified email, then seniority order
    for person in people:
        email = person.get("email") or ""
        # Skip clearly bad emails
        if any(p in email for p in ["@apollo.io", "example.com", "test@", "demo@"]):
            continue

        # Apollo free plan returns first_name + last_name_obfuscated instead of full name
        first = (person.get("first_name") or "").strip()
        last = (person.get("last_name") or "").strip()
        name_full = (person.get("name") or "").strip()
        # Prefer full name, fall back to first+last, fall back to first only
        if name_full:
            name = name_full
        elif first and last:
            name = f"{first} {last}"
        elif first:
            name = first
        else:
            name = ""

        title = (person.get("title") or "").strip()
        linkedin = person.get("linkedin_url") or ""
        phone = ""
        phones = person.get("phone_numbers") or []
        if phones:
            phone = phones[0].get("sanitized_number") or phones[0].get("raw_number") or ""

        # If email not revealed (free plan), try to enrich by person ID
        if not email and person.get("id") and person.get("has_email"):
            email = _enrich_person_email(api_key, person["id"])

        if name:
            result = ApolloResult(
                name=name,
                title=title,
                email=email,
                linkedin_url=linkedin,
                phone=phone,
            )
            print(f"[apollo] {company_name}: {name} ({title}) — {email or 'no email'}")
            return result

    return ApolloResult()


def enrich_domain(domain: str) -> dict:
    """
    Use Apollo's organization enrich endpoint to get company phone + website.
    Returns dict with 'phone' and 'website' keys.
    """
    api_key = os.environ.get("APOLLO_API_KEY", "").strip()
    if not api_key or not domain:
        return {}

    try:
        resp = requests.get(
            f"{_BASE}/organizations/enrich",
            headers=_headers(api_key),
            params={"domain": domain},
            timeout=15,
        )
        resp.raise_for_status()
        org = resp.json().get("organization") or {}
    except Exception as e:
        print(f"[apollo] Org enrich failed for {domain}: {e}")
        return {}

    phone = org.get("primary_phone", {}).get("number") or ""
    website = org.get("website_url") or ""
    return {"phone": phone, "website": website}
