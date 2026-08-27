"""Scrape company websites for contact data and payment-tech fingerprints.

Port of ~/.claude/bob-miami-150/site_scrape.py. Reuses its fetch, path-walk,
email regex, junk filter and ThreadPoolExecutor main loop, including the
resume-on-restart behaviour (skip company_ids already written to the
output file). Drops the loose NAME_RE owner-extraction block entirely
(that regex is what produced junk contact names like "Get Ah" in the
previous production run); name extraction is handled in a later task
using lib.normalize.is_valid_person_name.

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

# RULING C30: template placeholder addresses that ship as if contactable.
# Matched by exact equality, not substring, because a substring check on
# "company.com" would wrongly reject real domains like
# "precisionroofingcompany.com".
PLACEHOLDER_LOCALPARTS = {"email", "youremail", "name", "example", "yourname", "yourcompany"}
PLACEHOLDER_DOMAINS = {"company.com", "yourcompany.com", "yourdomain.com",
                        "example.com", "domain.com", "email.com"}

# RULING C26: phone extraction preference order is tel: href, then a digit
# run near a phone label, then a bare match as last resort. A candidate
# immediately preceded by a license/invoice/order/PO/EIN label is rejected
# outright, since those are commonly formatted as 3-3-4 digit groups too.
TEL_HREF_RE = re.compile(r'href=["\']tel:([^"\']+)["\']', re.I)
PHONE_CANDIDATE_RE = re.compile(r"(\+?1?[\s.\-]?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})")
PHONE_LABEL_RE = re.compile(r"\b(phone|call|tel|office|toll[\s-]?free)\b", re.I)
PHONE_REJECT_RE = re.compile(
    r"\b(licen[cs]e|lic|invoice|order|po|ein)\b\W{0,5}$", re.I)
# RULING C31: a tel: link is not automatically the company's own number. A
# web designer's credit link or a chamber-of-commerce badge can carry a
# tel: href too, and can appear earlier in document order than the real
# contact block. Deprioritize (do not reject outright, since it may be the
# only candidate) a tel: link whose surrounding text reads like a footer
# credit rather than a contact section.
FOOTER_CREDIT_RE = re.compile(
    r"designed by|powered by|site by|built by|web design by|developed by|"
    r"\bcredits?\b", re.I)

# Fingerprints for the money stack. Presence implies real transactions.
#
# RULING C29: expanded from the original ten (kept unchanged below) after
# a live probe found zero hits on 103 real businesses across two verticals
# while an identical-technique probe for untracked platforms found real
# signal (WordPress, HubSpot, etc.) on the same pages. The original ten
# were mistuned for the population this pipeline actually collects.
#
# Deliberately EXCLUDED: WordPress, Wix, Squarespace, GoDaddy, Webflow.
# A website builder is not evidence that money moves through a business;
# nearly every company would score a free hit.
#
# Short/ordinary-word platform names (clover, toast, drift, podium,
# acuity, rippling, xero) are anchored to their actual embed/widget
# domain, not the bare word, and several carry a leading \b boundary so
# a longer domain that merely ends in the same letters (e.g.
# "flexero.com") cannot match.
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
    # Payments
    "paypal": r"paypal\.com|paypalobjects\.com",
    "braintree": r"braintreegateway\.com|braintreepayments\.com",
    "authorizenet": r"authorize\.net|authorizenet",
    "clover": r"\bclover\.com\b|checkout\.clover\.com",
    "toast": r"toasttab\.com",
    "helcim": r"helcim\.com",
    # Ecommerce
    "bigcommerce": r"bigcommerce\.com",
    "woocommerce": r"woocommerce",
    # Paid marketing and CRM
    "hubspot": r"hubspot\.com|hs-scripts|hsforms",
    "salesforce": r"salesforce\.com",
    "pardot": r"pardot\.com",
    "marketo": r"marketo\.com|marketo\.net",
    "activecampaign": r"activecampaign\.com|activehosted\.com",
    "klaviyo": r"klaviyo\.com",
    "mailchimp": r"mailchimp\.com|list-manage\.com",
    "constantcontact": r"constantcontact\.com",
    # Support
    "zendesk": r"zendesk\.com|zdassets\.com",
    "intercom": r"intercom\.io|intercomcdn\.com",
    "freshdesk": r"freshdesk\.com",
    "drift": r"driftt\.com",
    # Booking
    "calendly": r"calendly\.com",
    "acuity": r"acuityscheduling\.com",
    "mindbody": r"mindbodyonline\.com",
    # Field service
    "workiz": r"workiz\.com",
    "fieldedge": r"fieldedge\.com",
    # Payroll and HR
    "paychex": r"paychex\.com",
    "bamboohr": r"bamboohr\.com",
    "rippling": r"\brippling\.com\b",
    # Accounting
    "xero": r"\bxero\.com\b",
    "freshbooks": r"freshbooks\.com",
    # Reviews and reputation
    "birdeye": r"birdeye\.com",
    "podium": r"\bpodium\.com\b",
    "nicejob": r"nicejob\.co\b",
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
    """Filter asset and vendor noise, prefer addresses on the company domain.
    RULING C30: also drops template placeholder addresses (email@,
    youremail@, name@, example@, yourname@, @company.com, @yourdomain.com
    style), URL-encoding artifacts (a stray "%" from an un-decoded mailto
    href), and local parts that are purely numeric or a single character
    -- none of these are a real, contactable address even though they
    parse as syntactically valid email strings."""
    keep = []
    for email in found:
        low = email.lower().strip(".")
        if any(j in low for j in JUNK):
            continue
        if low.count("@") != 1 or len(low) > 80:
            continue
        if "%" in low:
            continue
        local, _, rhs = low.partition("@")
        if not local or len(local) == 1 or local.isdigit():
            continue
        if local in PLACEHOLDER_LOCALPARTS or rhs in PLACEHOLDER_DOMAINS:
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


def extract_phone(html: str) -> str | None:
    """Extract a US phone number from page HTML or text. RULING C26: a
    tel: href wins outright; otherwise prefer a digit run near a phone
    label ("phone", "call", "tel", "office", "toll free") over a bare
    match; reject any candidate immediately preceded by a license,
    invoice, order, PO or EIN label. Every candidate passes through
    norm_phone, which already rejects impossible area/exchange codes.
    RULING C31: the license/invoice/order/PO/EIN reject list also applies
    to tel: hrefs, and a tel: link in a contact region is preferred over
    one that reads as a footer design credit, regardless of which one
    appears first in the document."""
    tel_spans = []
    tel_candidates = []
    for m in TEL_HREF_RE.finditer(html):
        tel_spans.append(m.span())
        # The reject label (e.g. "License:") sits before the opening tag
        # ("<a href=..."), not immediately before the href= attribute
        # itself, so the window is anchored to the tag's own start.
        tag_start = html.rfind("<", 0, m.start())
        if tag_start == -1:
            tag_start = m.start()
        window_before = html[max(0, tag_start - 20):tag_start]
        if PHONE_REJECT_RE.search(window_before):
            continue
        p = norm_phone(m.group(1))
        if not p:
            continue
        context = html[max(0, m.start() - 80):m.end() + 80]
        is_credit = bool(FOOTER_CREDIT_RE.search(context))
        tel_candidates.append((p, is_credit))
    if tel_candidates:
        non_credit = [p for p, is_credit in tel_candidates if not is_credit]
        if non_credit:
            return non_credit[0]
        return tel_candidates[0][0]

    labeled, bare = [], []
    for m in PHONE_CANDIDATE_RE.finditer(html):
        # A tel: href's own digits are governed entirely by the tel:
        # branch above (including its reject check); do not let a
        # rejected tel: number leak back in through the bare-digit path.
        if any(s <= m.start() < e for s, e in tel_spans):
            continue
        window_before = html[max(0, m.start() - 20):m.start()]
        if PHONE_REJECT_RE.search(window_before):
            continue
        p = norm_phone(m.group(1))
        if not p:
            continue
        context = html[max(0, m.start() - 40):m.end() + 10]
        if PHONE_LABEL_RE.search(context):
            labeled.append(p)
        else:
            bare.append(p)
    if labeled:
        return labeled[0]
    if bare:
        return bare[0]
    return None


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
            p = extract_phone(html)
            if p:
                phone = p
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
    # RULING C27: resume support. A domain already written to sites.jsonl
    # is skipped, so an interrupted run (up to eight fetches per domain
    # across thousands of companies) can restart without duplicating rows.
    done_ids = {row.get("company_id") for row in read_jsonl(config.DATA / "sites.jsonl")
                if row.get("company_id")}
    all_rows = list(read_jsonl(config.DATA / "resolved.jsonl"))
    skipped = sum(1 for r in all_rows if r.get("company_id") in done_ids)
    rows = [r for r in all_rows if r.get("company_id") not in done_ids]
    if limit:
        rows = rows[:limit]
    print(f"{len(rows)} rows to scrape ({workers} workers), "
          f"{skipped} already done and skipped", flush=True)

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
