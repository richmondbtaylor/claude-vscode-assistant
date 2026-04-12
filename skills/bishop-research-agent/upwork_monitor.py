"""
Upwork job monitor using Brave Search API.

Upwork blocks headless browsers (Cloudflare) and killed their RSS feeds (410).
This uses the Brave Search API to find Upwork job listing pages. While individual
job postings (/jobs/~ID) aren't well-indexed, Upwork's freelance-jobs category
pages contain real job titles and descriptions that Claude can score.

Uses the same BRAVE_API_KEY already configured for brave_monitor.py.
"""

import os
import re
import time
from typing import Generator, Optional

import requests

from analyzer import RawPost
from config import UPWORK_SEARCH_QUERIES

_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_REQUEST_DELAY = 1.2  # Brave free tier: 1 req/sec
_RESULTS_PER_QUERY = 10


def _get_api_key() -> Optional[str]:
    return os.environ.get("BRAVE_API_KEY", "").strip() or None


def _extract_post_id(url: str) -> str:
    """Extract a stable post ID from an Upwork URL."""
    match = re.search(r"/jobs/(~[a-zA-Z0-9]+)", url)
    if match:
        return f"upwork_{match.group(1)}"
    # For category pages, hash the full URL
    return f"upwork_{abs(hash(url))}"


def _search_brave(api_key: str, query: str) -> list[dict]:
    """Run a single Brave Search API query."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": f"site:upwork.com {query}",
        "count": _RESULTS_PER_QUERY,
    }
    try:
        resp = requests.get(_BASE_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("web", {}).get("results", [])
    except requests.RequestException as e:
        print(f"[upwork] Brave API error for '{query}': {e}")
        return []


def _parse_result(result: dict) -> RawPost | None:
    """Convert a Brave search result into a RawPost."""
    try:
        url = result.get("url", "")
        title = result.get("title", "")
        body = result.get("description", "")

        if not url or not title:
            return None

        # Accept job pages and freelance-jobs category pages
        url_lower = url.lower()
        if not any(seg in url_lower for seg in ["/jobs/", "/freelance-jobs/", "/hire/"]):
            return None

        # Skip generic non-job pages
        if any(skip in url_lower for skip in ["/resources/", "/blog/", "/press/", "/about/"]):
            return None

        url = url.split("?")[0]
        post_id = _extract_post_id(url)

        return RawPost(
            id=post_id,
            platform="upwork",
            url=url,
            author="upwork_client",
            title=title[:120],
            body=body[:800],
            subreddit=None,
            published_at=None,
        )
    except Exception as e:
        print(f"[upwork] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    """
    Main entry point called by the scheduler.
    Searches Brave for Upwork job listings and yields unique RawPosts.
    """
    api_key = _get_api_key()
    if not api_key:
        print("[upwork] BRAVE_API_KEY not set -- skipping Upwork monitor.")
        return

    print(f"[upwork] Starting Brave Search poll -- {len(UPWORK_SEARCH_QUERIES)} queries...")
    seen_in_this_cycle: set[str] = set()
    total = 0

    for query in UPWORK_SEARCH_QUERIES:
        print(f"[upwork] Searching: {query}")
        results = _search_brave(api_key, query)

        for result in results:
            post = _parse_result(result)
            if post and post.id not in seen_in_this_cycle:
                seen_in_this_cycle.add(post.id)
                total += 1
                yield post

        time.sleep(_REQUEST_DELAY)

    print(f"[upwork] Poll complete -- {total} candidate jobs found")
