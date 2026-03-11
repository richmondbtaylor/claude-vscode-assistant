import os
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import Generator, Optional
from analyzer import RawPost

_API_BASE = "https://api.apify.com/v2"
_ACTOR_ID = "apify~facebook-posts-scraper"
_MAX_AGE_DAYS = 7
_POLL_INTERVAL = 30
_MAX_WAIT = 300

# High-value Facebook Groups for Bishop AI leads
# Add/remove group URLs here as needed
FACEBOOK_GROUPS = [
    "https://www.facebook.com/groups/AIAutomationNation",
    "https://www.facebook.com/groups/chatgptusers",
    "https://www.facebook.com/groups/aiforsmallbusiness",
    "https://www.facebook.com/groups/artificialintelligenceentrepreneurs",
    "https://www.facebook.com/groups/n8ncommunity",
    "https://www.facebook.com/groups/zapierusers",
    "https://www.facebook.com/groups/automationandai",
    "https://www.facebook.com/groups/aibusinessowners",
    "https://www.facebook.com/groups/promptengineering",
    "https://www.facebook.com/groups/chatgptformarketers",
]


def _get_api_key() -> Optional[str]:
    return os.environ.get("APIFY_API_KEY", "").strip() or None


def _start_run(api_key: str, group_urls: list) -> Optional[str]:
    url = f"{_API_BASE}/acts/{_ACTOR_ID}/runs"
    payload = {
        "startUrls": [{"url": u} for u in group_urls],
        "resultsLimit": 50,
    }
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            params={"token": api_key},
            timeout=30,
        )
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]
        print(f"[facebook] Actor run started: {run_id}")
        return run_id
    except Exception as e:
        print(f"[facebook] Failed to start actor run: {e}")
        return None


def _wait_for_run(api_key: str, run_id: str) -> bool:
    url = f"{_API_BASE}/actor-runs/{run_id}"
    elapsed = 0
    while elapsed < _MAX_WAIT:
        try:
            resp = requests.get(url, params={"token": api_key}, timeout=15)
            resp.raise_for_status()
            status = resp.json()["data"]["status"]
            if status == "SUCCEEDED":
                return True
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                print(f"[facebook] Run {run_id} ended with status: {status}")
                return False
            print(f"[facebook] Run status: {status} ({elapsed}s elapsed)")
        except Exception as e:
            print(f"[facebook] Error checking run status: {e}")
        time.sleep(_POLL_INTERVAL)
        elapsed += _POLL_INTERVAL
    print(f"[facebook] Run timed out after {_MAX_WAIT}s")
    return False


def _fetch_results(api_key: str, run_id: str) -> list:
    url = f"{_API_BASE}/actor-runs/{run_id}/dataset/items"
    try:
        resp = requests.get(
            url,
            params={"token": api_key, "format": "json", "limit": 200},
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json()
        print(f"[facebook] Fetched {len(items)} posts from run")
        return items
    except Exception as e:
        print(f"[facebook] Failed to fetch results: {e}")
        return []


def _parse_post(item: dict) -> Optional[RawPost]:
    try:
        post_id = item.get("postId") or item.get("id") or ""
        url = item.get("url") or item.get("postUrl") or ""
        text = item.get("text") or item.get("message") or ""
        author = item.get("authorName") or (item.get("user") or {}).get("name", "unknown")
        group_name = item.get("groupName") or item.get("pageName") or "Facebook Group"

        if not text or not post_id:
            return None

        published_at = None
        raw_date = item.get("time") or item.get("timestamp") or item.get("date") or ""
        if raw_date:
            try:
                if isinstance(raw_date, (int, float)):
                    published_at = datetime.fromtimestamp(raw_date, tz=timezone.utc)
                else:
                    published_at = datetime.fromisoformat(
                        str(raw_date).replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
            except Exception:
                pass

        if published_at:
            age = datetime.now(timezone.utc) - published_at
            if age > timedelta(days=_MAX_AGE_DAYS):
                return None

        title = text[:120].replace("\n", " ")
        body = text[:1000]

        return RawPost(
            id=f"facebook_{abs(hash(post_id))}",
            platform="facebook",
            url=url or f"https://facebook.com/groups/post/{post_id}",
            author=author,
            title=title,
            body=body,
            subreddit=group_name,
            published_at=published_at,
        )
    except Exception as e:
        print(f"[facebook] Failed to parse post: {e}")
        return None


def poll() -> Generator[RawPost, None, None]:
    api_key = _get_api_key()
    if not api_key:
        print("[facebook] APIFY_API_KEY not set -- skipping")
        return

    print(f"[facebook] Starting scrape of {len(FACEBOOK_GROUPS)} groups...")

    run_id = _start_run(api_key, FACEBOOK_GROUPS)
    if not run_id:
        return

    if not _wait_for_run(api_key, run_id):
        return

    items = _fetch_results(api_key, run_id)
    seen: set = set()
    count = 0

    for item in items:
        post = _parse_post(item)
        if post and post.id not in seen:
            seen.add(post.id)
            count += 1
            yield post

    print(f"[facebook] Poll complete -- {count} posts yielded")
