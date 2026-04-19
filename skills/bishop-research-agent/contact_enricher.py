"""
Contact enrichment for Bishop AI Research Agent.

For hot leads (score >= ENRICH_MIN_SCORE), attempts to find:
  - Verified email + confidence score
  - Direct / mobile phone
  - LinkedIn profile URL
  - Company name + website

Enrichment chain (tries in order, merges results):
  1. Identity extraction  — parse LinkedIn URL, company name, domain from post
  2. Apify LinkedIn Scraper — if a LinkedIn profile URL is identified
  3. Apollo.io People Search — if name + company are identified
  4. Hunter.io Email Finder — if a company domain is identified
  5. Apify Contact Info Scraper — fallback scrape of company website

Each step is skipped gracefully when required input is missing or API key not set.

Required env vars (set in .env):
  APIFY_API_TOKEN   — Apify platform token
  APOLLO_API_KEY    — Apollo.io API key
  HUNTER_API_KEY    — Hunter.io API key (optional, improves email coverage)
"""

import os
import re
import requests
from dataclasses import dataclass
from typing import Optional

from analyzer import RawPost, PostAnalysis

_APIFY_BASE  = "https://api.apify.com/v2"
_APOLLO_BASE = "https://api.apollo.io/v1"
_HUNTER_BASE = "https://api.hunter.io/v2"

# Apify sync run timeout — LinkedIn scraper can take up to 45s
_APIFY_TIMEOUT = 90

# Personal email domains to ignore when extracting domain from post text
_PERSONAL_DOMAINS = {
    "gmail", "yahoo", "hotmail", "outlook", "proton", "icloud",
    "aol", "zoho", "mail", "ymail", "msn", "live",
}

# Platforms where post.author is a real name (not a handle)
_REAL_NAME_PLATFORMS = {"linkedin", "upwork", "fiverr"}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class EnrichmentResult:
    email: str = ""
    email_confidence: int = 0   # 0-100, Hunter.io style
    phone: str = ""
    phone_type: str = ""        # "direct", "mobile", "company"
    linkedin_url: str = ""
    enriched_name: str = ""
    company: str = ""
    website: str = ""
    source: str = ""            # pipe-separated list of which enrichers contributed


# ── Helpers ───────────────────────────────────────────────────────────────────

def _apify_token() -> str:
    return os.environ.get("APIFY_API_TOKEN", "").strip()

def _apollo_key() -> str:
    return os.environ.get("APOLLO_API_KEY", "").strip()

def _hunter_key() -> str:
    return os.environ.get("HUNTER_API_KEY", "").strip()


def _merge(a: EnrichmentResult, b: EnrichmentResult) -> EnrichmentResult:
    """Fill gaps in `a` with data from `b`."""
    return EnrichmentResult(
        email=a.email or b.email,
        email_confidence=a.email_confidence or b.email_confidence,
        phone=a.phone or b.phone,
        phone_type=a.phone_type or b.phone_type,
        linkedin_url=a.linkedin_url or b.linkedin_url,
        enriched_name=a.enriched_name or b.enriched_name,
        company=a.company or b.company,
        website=a.website or b.website,
        source=", ".join(filter(None, [a.source, b.source])),
    )


# ── Step 1: Identity extraction ────────────────────────────────────────────────

def _extract_linkedin_url(post: RawPost) -> str:
    """Find a LinkedIn /in/ profile URL from the post URL or body."""
    # Post URL directly contains a profile path
    m = re.search(r"linkedin\.com/in/([\w%-]+)", post.url or "")
    if m:
        return f"https://www.linkedin.com/in/{m.group(1)}"

    # Scan body text
    m = re.search(r"linkedin\.com/in/([\w%-]+)", post.body or "")
    if m:
        return f"https://www.linkedin.com/in/{m.group(1)}"

    # LinkedIn platform posts: linkedin.com/posts/{slug}_...
    if post.platform == "linkedin":
        m = re.search(r"linkedin\.com/posts/([\w-]+)_", post.url or "")
        if m:
            return f"https://www.linkedin.com/in/{m.group(1)}"

    return ""


def _extract_company_and_domain(post: RawPost) -> tuple[str, str]:
    """
    Extract (company_name, domain) from post text.
    Looks for ownership language, email addresses, and website URLs.
    """
    text = f"{post.title} {post.body}"
    company = ""
    domain = ""

    # Email address visible in post -> pull domain
    email_m = re.search(r"[\w.+-]+@([\w.-]+\.[a-z]{2,})", text, re.IGNORECASE)
    if email_m:
        candidate = email_m.group(1).lower()
        root = candidate.split(".")[0]
        if root not in _PERSONAL_DOMAINS:
            domain = candidate
            if not company:
                company = root.title()

    # Company name from ownership / role language
    _COMPANY_PATTERNS = [
        r"(?:founder|CEO|owner|co-founder|director|head)\s+(?:of|at)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s*[,.]|$)",
        r"(?:my|our)\s+(?:company|business|agency|startup|firm)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s*[,.]|$)",
        r"(?:I\s+run|I\s+own|we\s+run|we\s+own)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s*[,.]|$)",
        r"([A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]+){0,3})\s+(?:Inc|LLC|Ltd|Corp|Co)\b",
    ]
    for pattern in _COMPANY_PATTERNS:
        m = re.search(pattern, text)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 2:
                company = candidate
                break

    # Website URL visible in post -> extract domain
    if not domain:
        url_m = re.search(r"https?://(?:www\.)?([\w.-]+\.[a-z]{2,})", text)
        if url_m:
            candidate = url_m.group(1).lower()
            _SKIP = {
                "reddit", "linkedin", "twitter", "x", "facebook", "youtube",
                "google", "amazon", "github", "instagram", "tiktok", "upwork",
                "fiverr", "quora", "medium", "substack",
            }
            if candidate.split(".")[0] not in _SKIP:
                domain = candidate

    return company, domain


def _split_name(full_name: str) -> tuple[str, str]:
    """Return (first_name, last_name) from a full name string."""
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    return parts[0], parts[-1] if len(parts) > 1 else ""


# ── Step 2: Apify LinkedIn Profile Scraper ────────────────────────────────────

def _enrich_via_linkedin(linkedin_url: str) -> EnrichmentResult:
    """
    Apify LinkedIn Profile Scraper (apify/linkedin-profile-scraper).
    Returns email, phone, name, company from a /in/ profile URL.
    """
    token = _apify_token()
    if not token or not linkedin_url:
        return EnrichmentResult()

    try:
        resp = requests.post(
            f"{_APIFY_BASE}/acts/apify~linkedin-profile-scraper/run-sync-get-dataset-items",
            params={"token": token},
            json={
                "profileUrls": [linkedin_url],
                "proxyConfiguration": {"useApifyProxy": True},
            },
            timeout=_APIFY_TIMEOUT,
        )
        if not resp.ok:
            print(f"[enricher/linkedin] Apify error {resp.status_code}: {resp.text[:150]}")
            return EnrichmentResult()

        items = resp.json()
        if not items:
            return EnrichmentResult()

        item = items[0]
        email    = item.get("email") or ""
        phone    = item.get("phone") or ""
        name     = item.get("fullName") or item.get("name") or ""
        company  = item.get("companyName") or item.get("currentCompany") or ""
        website  = item.get("websiteUrl") or ""

        if email or phone:
            print(f"[enricher/linkedin] {name} — {email or 'no email'} | {phone or 'no phone'}")
            return EnrichmentResult(
                email=email,
                email_confidence=90 if email else 0,
                phone=phone,
                phone_type="direct" if phone else "",
                linkedin_url=linkedin_url,
                enriched_name=name,
                company=company,
                website=website,
                source="apify_linkedin",
            )
    except Exception as e:
        print(f"[enricher/linkedin] Error: {e}")

    return EnrichmentResult()


# ── Step 3: Apollo.io People Search ───────────────────────────────────────────

def _enrich_via_apollo(name: str, company: str, domain: str = "") -> EnrichmentResult:
    """
    Apollo.io People Search API (same pattern as BrainCX apollo_enrichment.py).
    Looks up a person by name + company and returns email + phone.
    """
    api_key = _apollo_key()
    if not api_key or (not name and not company):
        return EnrichmentResult()

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }

    payload: dict = {"per_page": 5, "page": 1}
    if name:
        payload["q_keywords"] = name
    if company:
        payload["q_organization_name"] = company
    if domain:
        payload["q_organization_domains"] = [domain]

    try:
        resp = requests.post(
            f"{_APOLLO_BASE}/mixed_people/api_search",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if not resp.ok:
            print(f"[enricher/apollo] Error {resp.status_code}: {resp.text[:150]}")
            return EnrichmentResult()

        people = resp.json().get("people") or resp.json().get("contacts") or []

        for person in people:
            email = person.get("email") or ""
            if any(d in email for d in ["@apollo.io", "example.com", "test@"]):
                continue

            first  = (person.get("first_name") or "").strip()
            last   = (person.get("last_name") or "").strip()
            full   = person.get("name") or f"{first} {last}".strip()
            title  = person.get("title") or ""
            li_url = person.get("linkedin_url") or ""

            phone, phone_type = "", ""
            for p in (person.get("phone_numbers") or []):
                raw = p.get("sanitized_number") or p.get("raw_number") or ""
                if raw:
                    phone = raw
                    ptype = (p.get("type") or "").lower()
                    phone_type = "mobile" if "mobile" in ptype else "direct"
                    break

            # Try to reveal email via enrich endpoint if Apollo only gave a placeholder
            if not email and person.get("id") and person.get("has_email"):
                email = _apollo_enrich_email(api_key, headers, person["id"])

            org = person.get("organization") or {}
            company_name = org.get("name") or person.get("organization_name") or company
            website = org.get("website_url") or ""

            if full:
                print(f"[enricher/apollo] {full} ({title}) — {email or 'no email'} | {phone or 'no phone'}")
                return EnrichmentResult(
                    email=email,
                    email_confidence=85 if email else 0,
                    phone=phone,
                    phone_type=phone_type,
                    linkedin_url=li_url,
                    enriched_name=full,
                    company=company_name,
                    website=website,
                    source="apollo",
                )
    except Exception as e:
        print(f"[enricher/apollo] Error: {e}")

    return EnrichmentResult()


def _apollo_enrich_email(api_key: str, headers: dict, person_id: str) -> str:
    """Reveal email for a known Apollo person ID via the enrich endpoint."""
    try:
        resp = requests.post(
            f"{_APOLLO_BASE}/contacts/enrich",
            headers=headers,
            json={"id": person_id},
            timeout=10,
        )
        if resp.ok:
            contact = resp.json().get("contact") or resp.json().get("person") or {}
            return contact.get("email") or ""
    except Exception:
        pass
    return ""


# ── Step 4: Hunter.io Email Finder ────────────────────────────────────────────

def _enrich_via_hunter(domain: str, first_name: str = "", last_name: str = "") -> EnrichmentResult:
    """
    Hunter.io email finder.
    If first + last name known: tries email-finder for a specific person.
    Fallback: domain-search to get the highest-confidence email on the domain.
    """
    api_key = _hunter_key()
    if not api_key or not domain:
        return EnrichmentResult()

    try:
        if first_name and last_name:
            resp = requests.get(
                f"{_HUNTER_BASE}/email-finder",
                params={"domain": domain, "first_name": first_name,
                        "last_name": last_name, "api_key": api_key},
                timeout=10,
            )
            if resp.ok:
                data = resp.json().get("data") or {}
                email = data.get("email") or ""
                confidence = data.get("score") or 0
                if email:
                    print(f"[enricher/hunter] Email finder: {email} ({confidence}% confidence)")
                    return EnrichmentResult(
                        email=email,
                        email_confidence=confidence,
                        source="hunter_finder",
                    )

        # Domain-level fallback
        resp = requests.get(
            f"{_HUNTER_BASE}/domain-search",
            params={"domain": domain, "limit": 5, "api_key": api_key},
            timeout=10,
        )
        if resp.ok:
            emails = resp.json().get("data", {}).get("emails") or []
            best = max(emails, key=lambda e: e.get("confidence", 0), default=None)
            if best:
                email = best.get("value") or ""
                confidence = best.get("confidence") or 0
                fn = best.get("first_name") or ""
                ln = best.get("last_name") or ""
                full_name = f"{fn} {ln}".strip()
                print(f"[enricher/hunter] Domain search: {email} ({confidence}% confidence)")
                return EnrichmentResult(
                    email=email,
                    email_confidence=confidence,
                    enriched_name=full_name,
                    source="hunter_domain",
                )
    except Exception as e:
        print(f"[enricher/hunter] Error: {e}")

    return EnrichmentResult()


# ── Step 5: Apify Contact Info Scraper ────────────────────────────────────────

def _enrich_via_contact_scraper(website_url: str) -> EnrichmentResult:
    """
    Apify Contact Info Scraper (apify/contact-info-scraper).
    Crawls up to 5 pages of a company website for emails and phone numbers.
    Prefers personal/direct emails over generic ones (info@, support@, etc.).
    """
    token = _apify_token()
    if not token or not website_url:
        return EnrichmentResult()

    if not website_url.startswith("http"):
        website_url = f"https://{website_url}"

    _GENERIC_PREFIXES = {"noreply", "no-reply", "info", "support", "hello",
                         "contact", "sales", "admin", "help", "team"}

    try:
        resp = requests.post(
            f"{_APIFY_BASE}/acts/apify~contact-info-scraper/run-sync-get-dataset-items",
            params={"token": token},
            json={
                "startUrls": [{"url": website_url}],
                "maxDepth": 1,
                "maxPagesPerDomain": 5,
                "proxyConfiguration": {"useApifyProxy": True},
            },
            timeout=_APIFY_TIMEOUT,
        )
        if not resp.ok:
            print(f"[enricher/contact_scraper] Apify error {resp.status_code}")
            return EnrichmentResult()

        for item in resp.json():
            emails = item.get("emails") or []
            phones = item.get("phones") or []

            personal_emails = [
                e for e in emails
                if e.split("@")[0].lower() not in _GENERIC_PREFIXES
            ]
            best_email = personal_emails[0] if personal_emails else (emails[0] if emails else "")
            best_phone = phones[0] if phones else ""

            if best_email or best_phone:
                print(f"[enricher/contact_scraper] {best_email or '-'} | {best_phone or '-'}")
                return EnrichmentResult(
                    email=best_email,
                    email_confidence=60 if best_email else 0,
                    phone=best_phone,
                    phone_type="company" if best_phone else "",
                    website=website_url,
                    source="apify_contact_scraper",
                )
    except Exception as e:
        print(f"[enricher/contact_scraper] Error: {e}")

    return EnrichmentResult()


# ── Public API ────────────────────────────────────────────────────────────────

def enrich(post: RawPost, analysis: PostAnalysis) -> EnrichmentResult:
    """
    Run the full enrichment chain for a qualifying lead.

    Chain:
      1. Extract identity signals from the post (LinkedIn URL, company, domain)
      2. Apify LinkedIn Scraper     — if LinkedIn URL found
      3. Apollo.io People Search   — if name or company identified
      4. Hunter.io Email Finder    — if domain identified, no email yet
      5. Apify Contact Info Scraper — fallback website crawl

    Returns EnrichmentResult; all fields default to empty string if nothing found.
    """
    label = f"[{post.platform}] {post.author} — {post.title[:50]}"
    print(f"[enricher] Starting enrichment: {label}")

    result = EnrichmentResult()

    # ── Step 1: Identity extraction ───────────────────────────────────────────
    linkedin_url       = _extract_linkedin_url(post)
    company, domain    = _extract_company_and_domain(post)

    # Real name: only trust author field on platforms with real names
    real_name = ""
    if post.platform in _REAL_NAME_PLATFORMS:
        if post.author and " " in post.author and not post.author.startswith("u/"):
            real_name = post.author

    first_name, last_name = _split_name(real_name)

    print(
        f"[enricher] Signals — "
        f"LinkedIn: {linkedin_url or 'none'} | "
        f"Company: {company or 'none'} | "
        f"Domain: {domain or 'none'} | "
        f"Name: {real_name or 'none (handle)'}"
    )

    # ── Step 2: LinkedIn scraper ──────────────────────────────────────────────
    if linkedin_url:
        li_result = _enrich_via_linkedin(linkedin_url)
        result = _merge(result, li_result)
        if not result.linkedin_url:
            result.linkedin_url = linkedin_url

    # ── Step 3: Apollo ────────────────────────────────────────────────────────
    if (real_name or company) and (not result.email or not result.phone):
        apollo_result = _enrich_via_apollo(real_name, company, domain)
        result = _merge(result, apollo_result)

    # ── Step 4: Hunter.io ─────────────────────────────────────────────────────
    if domain and not result.email:
        hunter_result = _enrich_via_hunter(domain, first_name, last_name)
        result = _merge(result, hunter_result)

    # ── Step 5: Contact scraper fallback ─────────────────────────────────────
    website = result.website or (f"https://{domain}" if domain else "")
    if website and not result.email and not result.phone:
        scraper_result = _enrich_via_contact_scraper(website)
        result = _merge(result, scraper_result)
        if not result.website:
            result.website = website

    # ── Summary ───────────────────────────────────────────────────────────────
    if result.email or result.phone:
        print(
            f"[enricher] FOUND — "
            f"email={result.email or '-'} "
            f"({result.email_confidence}%) | "
            f"phone={result.phone or '-'} | "
            f"source={result.source}"
        )
    else:
        print(f"[enricher] No contact info found for this lead")

    return result
