"""
Facebook Groups monitor using DuckDuckGo search — no API key required.
"""

import time
from datetime import datetime, timezone
from typing import Generator, Optional

from ddgs import DDGS

from analyzer import RawPost
from config import FACEBOOK_KEYWORDS, FACEBOOK_RESULTS_PER_KEYWORD

_REQUEST_DELAY = 3


def _make_query(keyword: str) -> str:
    return f'site:facebook.com/groups "{keyword}"'


def _parse_date(result: dict) -> Optional[datetime]:
    raw = result.get("published", "") or ""
    if not raw:
        return None
    try:
        date_part = raw.strip().split("T")[0]
        return datetime.fromisoformat(date_part).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_result(result: dict, keyword: str) -> RawPost | None:
    try:
        url = result.get("href", "")
        title = result.get("title", "")
        body = result.get("body", "")

        if not url or not body:
            return None

        if "facebook.com/groups" not in url.lower():
            return None

        post_id = f"facebook_{abs(hash(url))}"

        return RawPost(
            id=post_id,
            platform="facebook",
            url=url,
            author="unknown",
            title=title[:120],
            body=body,
            subreddit=None,
            published_at=_parse_date(result),
        )
    except Exception as e:
        print(f"[facebook] Failed to parse result: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    print("[facebook] Starting poll cycle...")
    seen_in_this_cycle: set[str] = set()

    with DDGS() as ddgs:
        for keyword in FACEBOOK_KEYWORDS:
            query = _make_query(keyword)
            print(f"[facebook] Searching: {query}")
            try:
                results = ddgs.text(query, max_results=FACEBOOK_RESULTS_PER_KEYWORD, timelimit='d')
                for result in (results or []):
                    post = _parse_result(result, keyword)
                    if post and post.id not in seen_in_this_cycle:
                        seen_in_this_cycle.add(post.id)
                        yield post
            except Exception as e:
                print(f"[facebook] Search error for '{keyword}': {e}")

            time.sleep(_REQUEST_DELAY)

    print(f"[facebook] Poll complete — {len(seen_in_this_cycle)} candidate posts found")
