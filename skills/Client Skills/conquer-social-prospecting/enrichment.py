"""
Decision-maker enrichment for Conquer.io leads.
Uses Brave Search (already paid for) + website scraping — no extra API needed.

Strategy:
1. Brave search for company website
2. Scrape contact/team/leadership pages for emails
3. Brave "@domain.com" search to find published emails
4. Brave search "[company] VP Sales / CRO / Head of Sales" to find named DMs
5. Guess + verify email patterns from name + domain
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests

_BRAVE_KEY = os.environ.get("BRAVE_API_KEY", "").strip()
_BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2

# ICP-specific DM titles for Conquer's enterprise sales ICP
_DM_TITLES = [
    "VP of Sales", "VP Sales", "Vice President of Sales",
    "CRO", "Chief Revenue Officer",
    "Head of Sales", "Head of Revenue",
    "Director of Sales", "Sales Director",
    "VP Revenue Operations", "Head of Revenue Operations",
    "Head of Sales Operations", "VP Sales Operations",
    "Chief Sales Officer", "SVP Sales",
]

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

_SKIP_EMAIL_PATTERNS = [
    "noreply", "no-reply", "donotreply", "support@", "info@",
    "jobs@", "careers@", "privacy@", "legal@", "abuse@",
    "unsubscribe", "example.com", "test@", "demo@", "hello@",
]

_SKIP_DOMAINS = {
    "zoominfo.com", "leadiq.com", "contactout.com", "apollo.io",
    "rocketreach.com", "hunter.io", "linkedin.com", "glassdoor.com",
    "indeed.com", "crunchbase.com", "dnb.com", "owler.com",
    "g2.com", "trustradius.com", "salesforce.com", "wikipedia.org",
}


@dataclass
class Contact:
    name: str = ""
    title: str = ""
    email: str = ""
    source: str = ""


def _clean_email(email: str) -> Optional[str]:
    email = email.lower().strip()
    if any(p in email for p in _SKIP_EMAIL_PATTERNS):
        return None
    if not re.search(r"\.[a-z]{2,}$", email):
        return None
    return email


def _brave_search(query: str, count: int = 5) -> list[dict]:
    if not _BRAVE_KEY:
        return []
    try:
        resp = requests.get(
            _BRAVE_URL,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": _BRAVE_KEY,
            },
            params={"q": query, "count": count, "text_decorations": "false", "search_lang": "en"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])
    except Exception:
        return []


def _scrape_page(url: str) -> list[str]:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ConquerEnricher/1.0)"},
            timeout=8,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return []
        emails = []
        for m in _EMAIL_RE.finditer(resp.text):
            e = _clean_email(m.group(0))
            if e and e not in emails:
                emails.append(e)
        return emails[:15]
    except Exception:
        return []


def _find_website(company_name: str) -> str:
    results = _brave_search(f'"{company_name}" official site', count=5)
    time.sleep(_REQUEST_DELAY)
    for r in results:
        url = r.get("url", "")
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
        except Exception:
            continue
        if domain and not any(s in domain for s in _SKIP_DOMAINS):
            return url
    return ""


def _scrape_contact_pages(website: str, domain: str) -> list[str]:
    base = website.rstrip("/")
    subpages = [
        base,
        f"{base}/contact",
        f"{base}/about",
        f"{base}/team",
        f"{base}/leadership",
        f"{base}/management",
        f"{base}/executives",
    ]
    found = []
    for url in subpages:
        emails = _scrape_page(url)
        for e in emails:
            if e not in found:
                found.append(e)
        if found:
            break
        time.sleep(0.2)
    return found


def _find_emails_via_domain_search(domain: str) -> list[str]:
    results = _brave_search(f'"@{domain}"', count=5)
    time.sleep(_REQUEST_DELAY)
    found = []
    for r in results:
        text = r.get("title", "") + " " + r.get("description", "")
        for m in _EMAIL_RE.finditer(text):
            e = _clean_email(m.group(0))
            if e and domain in e and e not in found:
                found.append(e)
    return found


def _find_dm_via_search(company_name: str) -> Contact:
    title_terms = " OR ".join(f'"{t}"' for t in _DM_TITLES[:5])
    results = _brave_search(f'"{company_name}" ({title_terms})', count=5)
    time.sleep(_REQUEST_DELAY)
    for r in results:
        snippet = (r.get("title", "") + " " + r.get("description", "")).lower()
        for title in _DM_TITLES:
            if title.lower() in snippet:
                text = r.get("description", "") or r.get("title", "")
                name = _extract_name_near_title(text, title)
                if name:
                    return Contact(name=name, title=title, source="search")
    return Contact()


def _extract_name_near_title(text: str, title: str) -> str:
    match = re.search(re.escape(title), text, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - 80)
    end = min(len(text), match.end() + 80)
    surrounding = text[start:end]
    name_re = re.compile(r"\b([A-Z][a-z]{1,15})\s+([A-Z][a-z]{1,20})\b")
    skip_words = ["sales", "revenue", "operations", "director", "manager", "head", "chief"]
    for nm in name_re.finditer(surrounding):
        candidate = nm.group(0)
        if any(w in candidate.lower() for w in skip_words):
            continue
        return candidate
    return ""


def _guess_email_patterns(name: str, domain: str) -> list[str]:
    parts = name.lower().split()
    if len(parts) < 2:
        return []
    first, last = parts[0], parts[-1]
    return [
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}@{domain}",
        f"{first[0]}.{last}@{domain}",
    ]


def _verify_email(email: str) -> bool:
    results = _brave_search(f'"{email}"', count=2)
    time.sleep(0.5)
    return len(results) > 0


def enrich(company_name: str, job_title: str = "unknown") -> dict:
    """
    Return enrichment dict: email, first_name, last_name, title, source.
    Uses Brave search + website scraping — no paid API required.
    Returns empty dict if nothing found.
    """
    if not company_name or company_name.lower() in ("unknown", ""):
        return {}
    if not _BRAVE_KEY:
        return {}

    # Step 1: Find company website
    website = _find_website(company_name)
    domain = urlparse(website).netloc.replace("www.", "") if website else ""

    # Step 2: Scrape contact/team pages
    if website and domain:
        emails = _scrape_contact_pages(website, domain)
        if emails:
            e = emails[0]
            print(f"[enrichment] {company_name}: email from website: {e}")
            return {"email": e, "first_name": "", "last_name": "", "title": "", "source": "website"}

    # Step 3: Brave "@domain" search
    if domain:
        emails = _find_emails_via_domain_search(domain)
        if emails:
            e = emails[0]
            print(f"[enrichment] {company_name}: email from domain search: {e}")
            return {"email": e, "first_name": "", "last_name": "", "title": "", "source": "brave_search"}

    # Step 4: Find named DM via Brave search
    contact = _find_dm_via_search(company_name)
    if contact.name:
        # Step 5: Guess + verify email
        if domain:
            for pattern in _guess_email_patterns(contact.name, domain):
                if _verify_email(pattern):
                    contact.email = pattern
                    contact.source = "guessed+verified"
                    break
        parts = contact.name.split()
        print(f"[enrichment] {company_name}: DM found: {contact.name} ({contact.title})")
        return {
            "email": contact.email,
            "first_name": parts[0] if parts else "",
            "last_name": parts[-1] if len(parts) > 1 else "",
            "title": contact.title,
            "source": contact.source,
        }

    return {}
