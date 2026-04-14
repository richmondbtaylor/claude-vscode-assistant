"""
Decision-maker email finder for BrainCX leads.

Strategy (no paid API required):
1. Scrape company website — contact/about/team/leadership/management/doctors pages
2. Brave search "@domain.com" to find published emails anywhere online
3. Brave search site:domain.com to find email-bearing pages we missed
4. Brave search "[company] [ICP-specific DM title]" to find named decision makers
5. Guess common email patterns from name + domain, verify via Brave

Returns best available: name, title, email.
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests

_REQUEST_DELAY = 1.0

# ICP-specific DM titles, ordered by seniority
_DM_TITLES_BY_ICP = {
    "healthcare": [
        "practice manager", "office manager", "practice administrator",
        "clinic administrator", "clinic manager", "front office manager",
        "medical director", "operations manager", "administrator",
    ],
    "immigration": [
        "managing partner", "firm administrator", "office manager",
        "operations manager", "owner", "partner",
    ],
    "general_legal": [
        "managing partner", "firm administrator", "office manager",
        "operations manager", "owner", "partner",
    ],
    "home_services": [
        "owner", "general manager", "operations manager",
        "office manager", "president", "ceo",
    ],
}
_DM_TITLES_DEFAULT = [
    "practice manager", "office manager", "practice administrator",
    "clinic administrator", "medical director", "operations manager",
    "office director", "managing partner", "firm administrator",
    "hospital administrator", "clinic manager", "front office manager",
    "business manager", "owner", "administrator",
]

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

_SKIP_EMAIL_PATTERNS = [
    "noreply", "no-reply", "donotreply", "support@", "info@indeed",
    "jobs@", "careers@", "privacy@", "legal@", "abuse@", "unsubscribe",
    "example.com", "test@", "demo@",
]

# Image/media file extensions that can be falsely matched as email TLDs
_FAKE_TLD_RE = re.compile(
    r'\.(png|jpg|jpeg|gif|svg|webp|ico|pdf|mp4|mp3|zip|css|js|json|xml|txt|doc|docx)$',
    re.IGNORECASE,
)

_SKIP_DOMAINS = {
    "zoominfo.com", "leadiq.com", "contactout.com", "apollo.io",
    "rocketreach.com", "rocketreach.co", "hunter.io", "spokeo.com", "whitepages.com",
    "crunchbase.com", "dnb.com", "owler.com", "manta.com",
    "pissedconsumer.com", "indeed.com", "linkedin.com", "glassdoor.com",
    "ziprecruiter.com", "monster.com", "careerbuilder.com",
}


@dataclass
class DecisionMaker:
    name: str = ""
    title: str = ""
    email: str = ""
    source: str = ""  # 'website' | 'brave_email' | 'search' | 'guessed+verified'


def _clean_email(email: str) -> Optional[str]:
    email = email.lower().strip()
    if any(p in email for p in _SKIP_EMAIL_PATTERNS):
        return None
    if _FAKE_TLD_RE.search(email):
        return None
    if not re.search(r"\.[a-z]{2,}$", email):
        return None
    return email


def _scrape_page_for_emails(url: str, timeout: int = 8) -> list[str]:
    """Fetch a URL and extract email addresses from the HTML."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BrainCX-Enricher/1.0)"},
            timeout=timeout,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return []
        emails = []
        for m in _EMAIL_RE.finditer(resp.text):
            clean = _clean_email(m.group(0))
            if clean and clean not in emails:
                emails.append(clean)
        return emails[:15]
    except Exception:
        return []


def _scrape_contact_pages(website: str) -> list[str]:
    """Try many subpages of the company website for emails."""
    if not website:
        return []
    domain = urlparse(website).netloc.lower().replace("www.", "")
    if any(s in domain for s in _SKIP_DOMAINS):
        return []
    base = website.rstrip("/")
    subpages = [
        base,
        f"{base}/contact",
        f"{base}/contact-us",
        f"{base}/about",
        f"{base}/about-us",
        f"{base}/team",
        f"{base}/our-team",
        f"{base}/meet-the-team",
        f"{base}/staff",
        f"{base}/leadership",
        f"{base}/management",
        f"{base}/doctors",
        f"{base}/attorneys",
        f"{base}/partners",
    ]
    found = []
    for url in subpages:
        emails = _scrape_page_for_emails(url)
        # Only keep emails that belong to this company's domain
        for e in emails:
            if domain in e and e not in found:
                found.append(e)
        time.sleep(0.2)
    return found


def _brave_search(query: str, api_key: str, count: int = 5) -> list[dict]:
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
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


def _find_email_via_domain_search(domain: str, api_key: str) -> list[str]:
    """Search Brave for published emails at this domain."""
    results = _brave_search(f'"@{domain}"', api_key, count=5)
    time.sleep(_REQUEST_DELAY)
    found = []
    for r in results:
        text = r.get("title", "") + " " + r.get("description", "")
        for m in _EMAIL_RE.finditer(text):
            e = _clean_email(m.group(0))
            if e and domain in e and e not in found:
                found.append(e)
    return found


def _find_email_via_site_search(domain: str, api_key: str) -> list[str]:
    """Brave site: search to find contact pages we may have missed, then scrape them."""
    results = _brave_search(f'site:{domain} email OR contact', api_key, count=3)
    time.sleep(_REQUEST_DELAY)
    found = []
    for r in results:
        url = r.get("url", "")
        if not url:
            continue
        result_domain = urlparse(url).netloc.lower().replace("www.", "")
        if result_domain != domain:
            continue
        emails = _scrape_page_for_emails(url)
        for e in emails:
            # Only keep emails that actually belong to this domain
            if domain in e and e not in found:
                found.append(e)
        if found:
            break
        time.sleep(0.2)
    return found


def _find_dm_via_search(company: str, icp_category: str, api_key: str) -> DecisionMaker:
    """Search Brave for a named decision-maker at the company."""
    dm_titles = _DM_TITLES_BY_ICP.get(icp_category, _DM_TITLES_DEFAULT)
    # Build title query from top 4 titles for this ICP
    title_terms = " OR ".join(f'"{t}"' for t in dm_titles[:4])
    dm_query = f'"{company}" ({title_terms})'
    results = _brave_search(dm_query, api_key, count=5)
    time.sleep(_REQUEST_DELAY)

    for r in results:
        snippet = (r.get("title", "") + " " + r.get("description", "")).lower()
        for title in dm_titles:
            if title in snippet:
                text = r.get("description", "") or r.get("title", "")
                name = _extract_name_near_title(text, title)
                if name:
                    return DecisionMaker(name=name, title=title.title(), source="search")

    return DecisionMaker()


def _extract_name_near_title(text: str, title: str) -> str:
    """Try to pull a proper name near a job title mention in text."""
    title_pattern = re.compile(re.escape(title), re.IGNORECASE)
    match = title_pattern.search(text)
    if not match:
        return ""

    start = max(0, match.start() - 80)
    end = min(len(text), match.end() + 80)
    surrounding = text[start:end]

    name_re = re.compile(r"\b([A-Z][a-z]{1,15})\s+([A-Z][a-z]{1,20})\b")
    for nm in name_re.finditer(surrounding):
        candidate = nm.group(0)
        if any(w in candidate.lower() for w in [
            "manager", "director", "office", "medical", "dental",
            "center", "group", "practice", "clinic", "health",
        ]):
            continue
        return candidate

    return ""


def _guess_email_patterns(name: str, domain: str) -> list[str]:
    """Generate common email patterns from a name + domain."""
    if not name or not domain:
        return []
    parts = name.lower().split()
    if len(parts) < 2:
        return []
    first, last = parts[0], parts[-1]
    return [
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}@{domain}",
        f"{first[0]}.{last}@{domain}",
        f"{first}{last[0]}@{domain}",
    ]


def _pick_best_email(emails: list[str], prefer_dm: bool = False) -> str:
    """Pick the best email from a list — prefer role/contact, avoid generic catch-alls."""
    if not emails:
        return ""
    priority_prefixes = [
        "info", "contact", "office", "admin", "hello", "manager", "front",
        "reception", "appointments", "scheduling", "billing", "customerservice",
        "customer", "inquiries", "inquiry", "general",
    ]
    for e in emails:
        local = e.split("@")[0]
        if any(local.startswith(p) for p in priority_prefixes):
            return e
    return emails[0]


def _verify_email_via_search(email: str, api_key: str) -> bool:
    """Quick Brave search to see if this email appears anywhere online."""
    results = _brave_search(f'"{email}"', api_key, count=2)
    time.sleep(0.5)
    return len(results) > 0


def lookup(company_name: str, website: str = "", location: str = "", icp_category: str = "") -> DecisionMaker:
    """
    Find decision-maker contact info for a business.
    Priority: website scrape > domain email search > site: search > DM name search > email guess
    """
    api_key = os.environ.get("BRAVE_API_KEY", "").strip()
    if not company_name or company_name.lower() in ("unknown", ""):
        return DecisionMaker()

    skip_hints = ["apply today", "jobs employment", "job vacancies", "work from home", "indeed.com", "linkedin.com"]
    if any(h in company_name.lower() for h in skip_hints):
        return DecisionMaker()

    domain = urlparse(website).netloc.replace("www.", "") if website else ""

    # Step 1: Scrape website (many subpages)
    emails_from_site = _scrape_contact_pages(website) if website else []
    chosen = _pick_best_email(emails_from_site)
    if chosen:
        print(f"[email] {company_name}: found on website: {chosen}")
        return DecisionMaker(email=chosen, source="website")

    if not api_key:
        return DecisionMaker()

    # Step 2: Brave "@domain.com" search — finds emails published anywhere online
    if domain:
        emails_from_search = _find_email_via_domain_search(domain, api_key)
        chosen = _pick_best_email(emails_from_search)
        if chosen:
            print(f"[email] {company_name}: found via domain search: {chosen}")
            return DecisionMaker(email=chosen, source="brave_email")

    # Step 3: Brave site: search to find contact pages we missed, then scrape them
    if domain:
        emails_from_site_search = _find_email_via_site_search(domain, api_key)
        chosen = _pick_best_email(emails_from_site_search)
        if chosen:
            print(f"[email] {company_name}: found via site search: {chosen}")
            return DecisionMaker(email=chosen, source="brave_email")

    # Step 4: Find named DM via Brave search
    dm = _find_dm_via_search(company_name, icp_category, api_key)
    if dm.name:
        # Step 5: Guess + verify email from DM name + domain
        if domain:
            patterns = _guess_email_patterns(dm.name, domain)
            for pattern in patterns[:3]:
                if _verify_email_via_search(pattern, api_key):
                    dm.email = pattern
                    dm.source = "guessed+verified"
                    print(f"[email] {company_name}: {dm.name} ({dm.title}) — {dm.email}")
                    return dm
        print(f"[email] {company_name}: DM found: {dm.name} ({dm.title}), no email verified")
        return dm

    return DecisionMaker()
