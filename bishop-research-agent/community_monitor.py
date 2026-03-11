"""
Generic Discourse community monitor.

Covers Make Community and OpenAI Community (both Discourse-based).
Zapier Community is not publicly accessible via Discourse API.
"""

import re
import time
from datetime import datetime, timezone
from typing import Generator, Optional

import requests

from analyzer import RawPost

_HEADERS = {
    "User-Agent": "BishopAI-ResearchAgent/1.0 (non-commercial research)",
    "Accept": "application/json",
}

_REQUEST_DELAY = 1.5

# (base_url, platform_id, display_name, [category_slugs])
COMMUNITIES = [
    (
        "https://community.make.com",
        "make_community",
        "Make Community",
        ["questions", "beginner-questions", "hire-a-pro"],
    ),
    (
        "https://community.openai.com",
        "openai_community",
        "OpenAI Community",
        ["api", "prompting", "chatgpt", "gpts-builders"],
    ),
]


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _fetch_category_topics(base_url: str, category_slug: str) -> list[dict]:
    url = f"{base_url}/c/{category_slug}.json"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json().get("topic_list", {}).get("topics", [])
    except Exception as e:
        print(f"[community] Failed to fetch {url}: {e}")
        return []


def poll() -> Generator[RawPost, None, None]:
    """Yield RawPost objects from Make Community and OpenAI Community."""
    for base_url, platform_id, display_name, categories in COMMUNITIES:
        print(f"[community] Scanning {display_name}...")
        seen_ids: set[int] = set()

        for category_slug in categories:
            topics = _fetch_category_topics(base_url, category_slug)
            time.sleep(_REQUEST_DELAY)

            for topic in topics:
                try:
                    topic_id = topic.get("id")
                    if topic_id in seen_ids:
                        continue
                    seen_ids.add(topic_id)

                    if topic.get("pinned") or topic.get("pinned_globally"):
                        continue

                    slug = topic.get("slug", "")
                    title = topic.get("title", "").strip()
                    excerpt = topic.get("excerpt", "").strip()
                    author = topic.get("last_poster_username", "unknown")
                    created_at = _parse_date(topic.get("created_at"))
                    url = f"{base_url}/t/{slug}/{topic_id}"
                    post_id = f"{platform_id}_{topic_id}"

                    if not title:
                        continue

                    yield RawPost(
                        id=post_id,
                        platform=platform_id,
                        url=url,
                        author=author,
                        title=title,
                        body=excerpt or title,
                        subreddit=None,
                        published_at=created_at,
                    )

                except Exception as e:
                    print(f"[community] Failed to parse topic from {display_name}: {e}")
                    continue

                time.sleep(0.3)
