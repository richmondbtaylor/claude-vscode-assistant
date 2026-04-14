"""
Job board monitor — searches Indeed and LinkedIn Jobs via Brave/DDG.

Businesses actively hiring for "receptionist" or "front desk" are the hottest
possible BrainCX leads: they're spending money right now to solve the exact
problem BrainCX solves.
"""

import time
from typing import Generator

from analyzer import RawPost
from config import JOB_BOARD_QUERIES, JOB_BOARD_RESULTS_PER_QUERY

_REQUEST_DELAY = 1.5


def _detect_platform(url: str) -> str:
    u = url.lower()
    if "indeed.com" in u:
        return "indeed"
    elif "linkedin.com" in u:
        return "linkedin_jobs"
    elif "ziprecruiter.com" in u:
        return "ziprecruiter"
    elif "glassdoor.com" in u:
        return "glassdoor"
    else:
        return "job_board"


def _search_brave(query: str, api_key: str, count: int = 5) -> list[dict]:
    import requests
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": min(count, 20),
        "freshness": "pw",    # past week — recent job postings
        "text_decorations": "false",
        "search_lang": "en",
    }
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers, params=params, timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("web", {}).get("results", [])
    except Exception as e:
        print(f"[job_board] Brave error for '{query[:50]}': {e}")
        return []


def _search_ddg(query: str, count: int = 5) -> list[dict]:
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
    except Exception as e:
        print(f"[job_board] DDG error for '{query[:50]}': {e}")
        return []


def poll() -> Generator[RawPost, None, None]:
    """Search job boards and yield RawPosts for each job listing found."""
    import os
    api_key = os.environ.get("BRAVE_API_KEY", "").strip()

    print(f"[job_board] Starting poll — {len(JOB_BOARD_QUERIES)} queries...")
    seen: set[str] = set()
    count = 0

    for query in JOB_BOARD_QUERIES:
        if api_key:
            raw = _search_brave(query, api_key, count=JOB_BOARD_RESULTS_PER_QUERY)
        else:
            raw = _search_ddg(query, count=JOB_BOARD_RESULTS_PER_QUERY)

        for r in raw:
            url = r.get("url", "")
            title = r.get("title", "") or r.get("href", "")
            body = r.get("description", "") or r.get("body", "")

            if not url or not body:
                continue

            platform = _detect_platform(url)
            post_id = f"{platform}_{abs(hash(url))}"

            if post_id in seen:
                continue
            seen.add(post_id)

            # Extract company name hint from title if present
            author = "unknown"
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) >= 2:
                    author = parts[-1].strip()  # Usually "Company Name - Indeed"

            post = RawPost(
                id=post_id,
                platform=platform,
                url=url,
                author=author,
                title=title[:120],
                body=f"JOB POSTING: {body[:1500]}",
                subreddit=None,
                published_at=None,
            )
            count += 1
            yield post

        time.sleep(_REQUEST_DELAY)

    print(f"[job_board] Poll complete — {count} job listings found")
