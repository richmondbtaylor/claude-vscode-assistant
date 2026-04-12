"""
Review Site Monitor — finds competitor pain signals on G2 and TrustRadius via Brave Search.
Uses Brave's indexed snippets: no Playwright needed, no Cloudflare issues.
Returns real review page URLs — every link goes directly to the review.

Sources:
  - TrustRadius: individual review permalinks (/reviews/{product}-{date})
  - G2: product review pages and pros/cons aggregates
"""

import os
import re
import time
from datetime import datetime, timezone
from typing import Generator, Optional

import requests

from analyzer import RawPost

_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2   # Brave free tier: 1 req/sec

# Review site queries — G2 and TrustRadius only (Capterra URLs are 100% dead).
_COMPETITOR_QUERIES = [
    # ── Outreach ──────────────────────────────────────────────────────────────────
    ('site:g2.com "outreach" reviews "dislike" OR "cons" OR "problems"',                   "Outreach"),
    ('"outreach.io" "too expensive" OR "pricing" site:g2.com OR site:trustradius.com',     "Outreach"),
    ('site:g2.com "outreach" "alternative" OR "switching" OR "replace"',                   "Outreach"),
    ('site:g2.com/compare "outreach" salesforce',                                          "Outreach"),
    ('site:g2.com/reviews "outreach" "salesforce"',                                        "Outreach"),

    # ── Salesloft ─────────────────────────────────────────────────────────────────
    ('site:g2.com "salesloft" reviews "dislike" OR "cons" OR "problems"',                  "Salesloft"),
    ('"salesloft" "too expensive" OR "pricing" site:g2.com OR site:trustradius.com',       "Salesloft"),
    ('site:g2.com "salesloft" "alternative" OR "switching" OR "replace"',                  "Salesloft"),
    ('site:g2.com/compare "salesloft" salesforce',                                         "Salesloft"),
    ('site:g2.com/reviews "salesloft" "salesforce"',                                       "Salesloft"),

    # ── Gong ─────────────────────────────────────────────────────────────────────
    ('site:g2.com "gong" reviews "dislike" OR "cons" OR "problems"',                      "Gong"),
    ('"gong.io" "too expensive" OR "pricing" site:g2.com OR site:trustradius.com',        "Gong"),
    ('site:g2.com "gong" "alternative" OR "switching" OR "replace"',                      "Gong"),
    ('site:g2.com/reviews "gong" "salesforce"',                                           "Gong"),

    # ── RingDNA / Revenue.io ──────────────────────────────────────────────────────
    ('site:g2.com "ringdna" OR "revenue.io" reviews "dislike" OR "cons"',                 "RingDNA"),
    ('site:g2.com "revenue.io" "alternative" OR "switching"',                             "RingDNA"),
    ('site:g2.com/compare "revenue.io" salesforce',                                       "RingDNA"),

    # ── Dialpad ───────────────────────────────────────────────────────────────────
    ('site:g2.com "dialpad sell" reviews "dislike" OR "cons" OR "problems"',              "Dialpad"),
    ('"dialpad sell" "too expensive" OR "pricing" site:g2.com OR site:trustradius.com',   "Dialpad"),
    ('site:g2.com "dialpad" "alternative" OR "switching" OR "replace"',                   "Dialpad"),

    # ── Cross-competitor / evaluation signals ─────────────────────────────────────
    ('site:g2.com/compare "salesloft" "outreach" salesforce',                             "Comparison"),
    ('"sales engagement platform" "salesforce" "switching" OR "alternative" site:g2.com', "Comparison"),
    ('site:g2.com "salesforce native" "sales engagement" problems OR cons OR dislike',    "Comparison"),
    ('"sales dialer" "salesforce" "problems" OR "switching" site:g2.com',                 "Comparison"),

    # ── Trustpilot — publicly indexed, real user reviews ─────────────────────────
    ('site:trustpilot.com "outreach.io" OR "outreach" reviews',                           "Outreach"),
    ('site:trustpilot.com "salesloft" reviews',                                           "Salesloft"),
    ('site:trustpilot.com "gong.io" OR "gong" reviews',                                  "Gong"),
    ('site:trustpilot.com "ringdna" OR "revenue.io" reviews',                             "RingDNA"),
    ('site:trustpilot.com "dialpad" reviews',                                             "Dialpad"),
]

# Social chatter queries — forums and communities that Brave actually indexes.
# LinkedIn /pulse articles and /posts are partially indexed (not profiles).
# Facebook public group posts are occasionally indexed.
# Focus on open discussion platforms: LinkedIn, Quora, Reddit, Sales Hacker, Spiceworks, forums.
_SOCIAL_QUERIES: list[tuple[str, str, str]] = [
    # ── LinkedIn — pulse articles and public posts (not profiles) ─────────────────
    ('site:linkedin.com/pulse "outreach" "salesloft" OR "alternative" OR "switching" "salesforce"', "Comparison",  "linkedin"),
    ('site:linkedin.com/pulse "salesloft" "alternative" OR "switching" OR "too expensive"',          "Salesloft",   "linkedin"),
    ('site:linkedin.com/pulse "outreach.io" "problems" OR "switching" OR "alternative"',             "Outreach",    "linkedin"),
    ('site:linkedin.com/pulse "sales engagement platform" "salesforce" "native" 2025 OR 2026',       "Comparison",  "linkedin"),
    ('site:linkedin.com/pulse "gong" "alternative" OR "switching" OR "expensive" "sales"',           "Gong",        "linkedin"),
    ('"outreach" OR "salesloft" "switching" OR "alternative" site:linkedin.com 2025 OR 2026',        "Comparison",  "linkedin"),
    ('"sales dialer" "salesforce native" "switching" site:linkedin.com',                             "Comparison",  "linkedin"),

    # ── Facebook — public group posts (partially indexed) ────────────────────────
    ('site:facebook.com "outreach.io" OR "salesloft" "alternative" OR "switching" "salesforce"',    "Comparison",  "web"),
    ('site:facebook.com "sales engagement" "outreach" OR "salesloft" "problems" OR "switching"',    "Comparison",  "web"),
    ('"outreach" OR "salesloft" "alternative" site:facebook.com/groups',                            "Comparison",  "web"),

    # ── Quora — open, well-indexed, real practitioners ────────────────────────────
    ('site:quora.com "Outreach.io" OR "Outreach" "alternative" OR "better" "sales"',               "Outreach",    "quora"),
    ('site:quora.com "Salesloft" "alternative" OR "better" OR "problem"',                           "Salesloft",   "quora"),
    ('site:quora.com "best sales engagement platform" "Salesforce"',                                "Comparison",  "quora"),
    ('site:quora.com "Gong" "alternative" OR "too expensive" "sales"',                              "Gong",        "quora"),

    # ── Sales Hacker — practitioner forum, open content ──────────────────────────
    ('site:saleshacker.com "outreach" OR "salesloft" "problems" OR "switching" OR "alternative"',   "Comparison",  "saleshacker"),
    ('site:saleshacker.com "sales engagement" "Salesforce" "native" OR "alternative"',              "Comparison",  "saleshacker"),
    ('site:saleshacker.com "dialpad" OR "ringdna" OR "revenue.io" "problems" OR "alternative"',     "Comparison",  "saleshacker"),

    # ── Reddit via open web (not RSS) — broader than RSS feed ────────────────────
    ('site:reddit.com "outreach.io" "switching" OR "alternative" OR "too expensive" 2025 OR 2026',  "Outreach",    "reddit"),
    ('site:reddit.com "salesloft" "switching" OR "alternative" OR "too expensive" 2025 OR 2026',    "Salesloft",   "reddit"),
    ('site:reddit.com "sales engagement platform" "Salesforce" "problems" OR "switching"',          "Comparison",  "reddit"),
    ('site:reddit.com "gong" "alternative" OR "switching" OR "expensive" 2025 OR 2026',             "Gong",        "reddit"),
    ('site:reddit.com "revenue.io" OR "ringdna" "switching" OR "alternative"',                      "RingDNA",     "reddit"),

    # ── Spiceworks / TechTarget / industry forums ─────────────────────────────────
    ('site:community.spiceworks.com "outreach" OR "salesloft" "alternative" OR "problems"',         "Comparison",  "web"),
    ('"outreach.io" OR "salesloft" "salesforce native" "switching" OR "alternatives" 2025 OR 2026', "Comparison",  "web"),
    ('"sales engagement" "salesforce" "outreach" OR "salesloft" "too expensive" OR "switching"',    "Comparison",  "web"),

    # ── Additional forums: HubSpot community, Salesforce Trailblazer, RevOps Co-op ─
    ('site:community.hubspot.com "outreach" OR "salesloft" "alternative" OR "switching"',           "Comparison",  "web"),
    ('site:trailhead.salesforce.com "outreach" OR "salesloft" "problems" OR "switching"',           "Comparison",  "web"),
    ('site:revopscoop.com "outreach" OR "salesloft" OR "gong" "alternative" OR "switching"',        "Comparison",  "web"),
    ('"sales engagement" "salesforce" "dialpad" OR "ringdna" "switching" OR "problems" 2025',       "Comparison",  "web"),
]

_RESULTS_PER_QUERY = 10


def _get_api_key() -> Optional[str]:
    return os.environ.get("BRAVE_API_KEY", "").strip() or None


def _detect_platform(url: str, forced: str = "") -> str:
    if forced:
        return forced
    url_lower = url.lower()
    if "trustradius.com" in url_lower:
        return "trustradius"
    if "g2.com" in url_lower:
        return "g2"
    if "capterra.com" in url_lower:
        return "capterra"
    if "linkedin.com" in url_lower:
        return "linkedin"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    if "trustpilot.com" in url_lower:
        return "trustpilot"
    if "facebook.com" in url_lower:
        return "facebook"
    if "quora.com" in url_lower:
        return "quora"
    if "trailhead.salesforce.com" in url_lower or "success.salesforce.com" in url_lower:
        return "trailblazer"
    if "saleshacker.com" in url_lower:
        return "saleshacker"
    return "web"


def _is_individual_review(url: str) -> bool:
    """True for direct review permalinks (higher signal than listing pages)."""
    # TrustRadius individual: /reviews/product-YYYY-MM-DD-...
    if re.search(r"trustradius\.com/reviews/[a-z0-9-]+-\d{4}-\d{2}-\d{2}", url):
        return True
    # G2 individual: /reviews/12345678
    if re.search(r"g2\.com/reviews/\d+", url):
        return True
    return False


def _search(query: str, api_key: str, freshness: str = "pm") -> list[dict]:
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": _RESULTS_PER_QUERY,
        "text_decorations": "false",
        "search_lang": "en",
        "freshness": freshness,  # pm = past month — hard cap on all results
    }
    try:
        resp = requests.get(_BASE_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            print("[g2] Brave rate limit — backing off 5s")
            time.sleep(5)
        else:
            print(f"[g2] Brave HTTP error: {e}")
        return []
    except Exception as e:
        print(f"[g2] Brave error: {e}")
        return []


def _ddg_search(query: str) -> list[dict]:
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=_RESULTS_PER_QUERY):
                results.append({
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "description": r.get("body", ""),
                })
        return results
    except Exception as e:
        print(f"[g2] DDG fallback error: {e}")
        return []


def _validate_url(url: str) -> bool:
    """HEAD-check the URL. Returns False if 4xx/5xx or unreachable."""
    try:
        resp = requests.head(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"},
            timeout=8,
            allow_redirects=True,
        )
        return resp.status_code < 400
    except Exception:
        return False


def _parse_result(result: dict, competitor: str, forced_platform: str = "") -> Optional[RawPost]:
    url   = result.get("url", "").strip()
    title = result.get("title", "").strip()
    body  = result.get("description", "").strip()

    if not url or not body:
        return None

    platform = _detect_platform(url, forced_platform)

    # Skip generic listing pages with no review content in snippet
    if len(body) < 40:
        return None

    # Validate URL — skip dead links (saves demo from 500 errors in the sheet)
    if not _validate_url(url):
        print(f"  [SKIP] Dead URL ({platform}) — {url[:80]}")
        return None

    # Build a post_id — use URL hash for listing pages, URL itself for individual reviews
    post_id = f"{platform}_{abs(hash(url))}"

    # Enrich title with competitor context for the analyzer
    full_title = f"[{platform.upper()} review] {title}"

    # Note if this is an individual permalink (higher credibility for Claude)
    if _is_individual_review(url):
        body = f"[Verified individual review] {body}"

    return RawPost(
        id=post_id,
        platform=platform,
        url=url,
        author="reviewer",           # Brave doesn't expose reviewer name in snippet
        title=full_title[:200],
        body=body[:2000],
        subreddit=competitor,        # competitor label for context
        published_at=_parse_date(result),
    )


def _parse_date(result: dict) -> Optional[datetime]:
    # Use Brave's page_age field if present (reflects when Brave last indexed/saw the page)
    raw = result.get("page_age", "") or result.get("age", "") or ""
    if raw:
        try:
            return datetime.fromisoformat(raw.split("T")[0]).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    # Do NOT extract date from TrustRadius URL slugs — those are review submission
    # dates (often 2018-2022) and would cause the age filter to drop valid leads.
    # Return None so the age filter is skipped for these posts.
    return None


def poll() -> Generator[RawPost, None, None]:
    """
    Search G2/TrustRadius/Capterra for competitor pain reviews AND social chatter
    (LinkedIn, Twitter/X, Quora, forums) via Brave. freshness=pm ensures past-month only.
    Yields RawPost objects with validated URLs only.
    """
    api_key = _get_api_key()
    use_brave = bool(api_key)

    if not use_brave:
        print("[g2] BRAVE_API_KEY not set — using DuckDuckGo fallback")

    total_queries = len(_COMPETITOR_QUERIES) + len(_SOCIAL_QUERIES)
    print(f"[g2] Starting search — {total_queries} queries ({len(_COMPETITOR_QUERIES)} review + {len(_SOCIAL_QUERIES)} social) via {'Brave' if use_brave else 'DDG'}...")
    seen: set[str] = set()
    total = 0
    individual_count = 0

    # Phase 1: Review sites (G2, TrustRadius, Capterra)
    print("[g2] Phase 1: Review sites...")
    for query, competitor in _COMPETITOR_QUERIES:
        if use_brave:
            results = _search(query, api_key)
        else:
            results = _ddg_search(query)

        for result in results:
            post = _parse_result(result, competitor)
            if post and post.id not in seen:
                seen.add(post.id)
                total += 1
                if _is_individual_review(post.url):
                    individual_count += 1
                yield post

        time.sleep(_REQUEST_DELAY)

    # Phase 2: Social chatter (LinkedIn, Twitter/X, Quora, forums)
    print("[g2] Phase 2: Social chatter...")
    for query, competitor, forced_platform in _SOCIAL_QUERIES:
        if use_brave:
            results = _search(query, api_key)
        else:
            results = _ddg_search(query)

        for result in results:
            post = _parse_result(result, competitor, forced_platform)
            if post and post.id not in seen:
                seen.add(post.id)
                total += 1
                yield post

        time.sleep(_REQUEST_DELAY)

    print(
        f"[g2] Search complete — {total} posts found "
        f"({individual_count} individual review permalinks)"
    )
