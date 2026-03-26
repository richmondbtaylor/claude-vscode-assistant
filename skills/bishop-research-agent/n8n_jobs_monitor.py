"""
Scraper for the n8n Community Jobs board.
https://community.n8n.io/c/jobs/

Uses the Discourse JSON API — no auth needed, no scraping required.
Returns posts as RawPost objects for the standard analysis pipeline.
"""

import time
from datetime import datetime, timezone
from typing import Generator, Optional

import requests

from analyzer import RawPost

_BASE_URL = "https://community.n8n.io"
_JOBS_URL = f"{_BASE_URL}/c/jobs.json"
_TOPIC_URL = f"{_BASE_URL}/t/{{slug}}/{{topic_id}}.json"

_HEADERS = {
    "User-Agent": "BishopAI-ResearchAgent/1.0 (non-commercial research)",
    "Accept": "application/json",
}

_REQUEST_DELAY = 2  # seconds between requests


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        # Discourse format: "2024-01-15T12:00:00.000Z"
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _fetch_topic_body(slug: str, topic_id: int) -> str:
    """Fetch the first post body for a topic to get full description."""
    try:
        url = _TOPIC_URL.format(slug=slug, topic_id=topic_id)
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = data.get("post_stream", {}).get("posts", [])
        if posts:
            # Strip HTML tags from cooked content
            import re
            cooked = posts[0].get("cooked", "")
            plain = re.sub(r"<[^>]+>", " ", cooked)
            plain = re.sub(r"\s+", " ", plain).strip()
            return plain[:2000]
    except Exception:
        pass
    return ""


def poll(fetch_bodies: bool = False) -> Generator[RawPost, None, None]:
    """
    Fetch job posts from n8n community jobs board.

    Args:
        fetch_bodies: If True, fetches full post body for each topic (2x API calls).
                      Set False to use just the excerpt (faster, fewer requests).
    """
    print("[n8n_jobs] Fetching jobs from community.n8n.io/c/jobs/...")

    try:
        resp = requests.get(_JOBS_URL, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[n8n_jobs] Failed to fetch job list: {e}")
        return

    topics = data.get("topic_list", {}).get("topics", [])
    print(f"[n8n_jobs] Found {len(topics)} job postings")

    for topic in topics:
        try:
            topic_id = topic.get("id")
            slug = topic.get("slug", "")
            title = topic.get("title", "").strip()
            excerpt = topic.get("excerpt", "").strip()
            author = topic.get("last_poster_username", "unknown")
            created_at = _parse_date(topic.get("created_at"))
            url = f"{_BASE_URL}/t/{slug}/{topic_id}"
            post_id = f"n8n_jobs_{topic_id}"

            if not title:
                continue

            # Use excerpt as body, or fetch full body if requested
            if fetch_bodies and not excerpt:
                body = _fetch_topic_body(slug, topic_id)
                time.sleep(_REQUEST_DELAY)
            else:
                body = excerpt or title

            yield RawPost(
                id=post_id,
                platform="n8n_community",
                url=url,
                author=author,
                title=title,
                body=body,
                subreddit=None,
                published_at=created_at,
            )

        except Exception as e:
            print(f"[n8n_jobs] Failed to parse topic: {e}")
            continue

        time.sleep(0.5)  # polite delay between topics
