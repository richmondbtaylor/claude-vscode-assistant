"""
Web monitor using Brave Search API (with DuckDuckGo fallback).
Searches LinkedIn, G2, Quora, Reddit, Trustpilot, Sales Hacker, and general web
for Conquer.io-relevant sales engagement pain points.
"""

import os
import time
from datetime import datetime, timezone
from typing import Generator, Optional

import requests

from analyzer import RawPost
from config import WEB_RESULTS_PER_QUERY, WEB_SEARCH_QUERIES

_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2   # Brave free tier: 1 req/sec + buffer


def _get_api_key() -> Optional[str]:
    return os.environ.get("BRAVE_API_KEY", "").strip() or None


def _detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return "linkedin"
    elif "g2.com" in url_lower:
        return "g2"
    elif "trustpilot.com" in url_lower:
        return "trustpilot"
    elif "quora.com" in url_lower:
        return "quora"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "facebook.com" in url_lower:
        return "facebook"
    elif "saleshacker.com" in url_lower:
        return "saleshacker"
    elif "trailhead.salesforce.com" in url_lower or "trailblazer.salesforce.com" in url_lower:
        return "trailblazer"
    elif "reddit.com" in url_lower:
        return "reddit"
    else:
        return "web"


def _extract_author(title: str, url: str, platform: str) -> str:
    if platform == "linkedin" and " on LinkedIn" in title:
        return title.split(" on LinkedIn")[0].strip()
    if platform == "quora" and "'s answer to" in title:
        return title.split("'s answer")[0].strip()
    if platform == "twitter" and " on X:" in title:
        return title.split(" on X:")[0].strip()
    return "unknown"


def _parse_date(result: dict) -> Optional[datetime]:
    raw = result.get("page_age", "") or result.get("age", "") or ""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.split("T")[0]).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _search(query: str, api_key: str, count: int = 10) -> list[dict]:
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": min(count, 20),
        "freshness": "pw",   # past week
        "text_decorations": "false",
        "search_lang": "en",
    }
    try:
        resp = requests.get(_BASE_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("web", {}).get("results", [])
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            print(f"[brave] Rate limit hit — backing off 5s")
            time.sleep(5)
        else:
            print(f"[brave] HTTP error for query '{query[:50]}': {e}")
        return []
    except Exception as e:
        print(f"[brave] Error for query '{query[:50]}': {e}")
        return []


def _parse_result(result: dict) -> Optional[RawPost]:
    try:
        url = result.get("url", "")
        title = result.get("title", "")
        body = result.get("description", "") or result.get("extra_snippets", [""])[0]

        if not url or not body:
            return None

        platform = _detect_platform(url)

        # Reddit is handled by reddit_monitor — skip duplicates
        if platform == "reddit":
            return None

        author = _extract_author(title, url, platform)
        post_id = f"{platform}_{abs(hash(url))}"

        return RawPost(
            id=post_id,
            platform=platform,
            url=url,
            author=author,
            title=title[:120],
            body=body[:1500],
            subreddit=None,
            published_at=_parse_date(result),
        )
    except Exception as e:
        print(f"[brave] Failed to parse result: {e}")
        return None


# ── DuckDuckGo fallback ────────────────────────────────────────────────────────

def _ddg_search(query: str, count: int = 5) -> list[dict]:
    """DuckDuckGo fallback when Brave API key is not set."""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=count, timelimit="w"):
                results.append({
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "description": r.get("body", ""),
                })
        return results
    except ImportError:
        print("[brave] ddgs not installed — run: pip install ddgs")
        return []
    except Exception as e:
        print(f"[brave/ddg] Error for query '{query[:50]}': {e}")
        return []


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point. Runs all WEB_SEARCH_QUERIES and yields unique RawPosts.
    Falls back to DuckDuckGo if BRAVE_API_KEY is not set.
    """
    api_key = _get_api_key()
    use_brave = bool(api_key)

    if not use_brave:
        print("[brave] BRAVE_API_KEY not set — using DuckDuckGo fallback")

    print(f"[brave] Starting poll — {len(WEB_SEARCH_QUERIES)} queries via {'Brave' if use_brave else 'DuckDuckGo'}...")
    seen_in_this_cycle: set[str] = set()
    counts: dict[str, int] = {}
    no_result_count = 0

    for query in WEB_SEARCH_QUERIES:
        if use_brave:
            results = _search(query, api_key, count=WEB_RESULTS_PER_QUERY)
        else:
            results = _ddg_search(query, count=WEB_RESULTS_PER_QUERY)

        if not results:
            no_result_count += 1
        else:
            for result in results:
                post = _parse_result(result)
                if post and post.id not in seen_in_this_cycle:
                    seen_in_this_cycle.add(post.id)
                    counts[post.platform] = counts.get(post.platform, 0) + 1
                    yield post

        time.sleep(_REQUEST_DELAY)

    summary = ", ".join(f"{p}: {n}" for p, n in sorted(counts.items()))
    print(
        f"[brave] Poll complete — {len(seen_in_this_cycle)} posts found "
        f"({summary}) | {no_result_count} queries returned 0 results"
    )
