"""
Topic Researcher -- Finds trending AI topics for carousel content.

Uses Brave Search API + Reddit JSON feeds to discover viral topics,
then scores them for carousel potential.
"""

import os
import random
import time
from datetime import datetime

import requests

from config import BRAVE_SEARCH_QUERIES, REDDIT_RSS_FEEDS


def _brave_search(query: str, count: int = 5) -> list[dict]:
    """Search Brave for recent articles on a topic."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        print("[topic] BRAVE_API_KEY not set -- skipping Brave search")
        return []

    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": query, "count": count, "freshness": "pd"},  # past day
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "source": "brave",
                "query": query,
            })
        return results
    except Exception as e:
        print(f"[topic] Brave search failed for '{query}': {e}")
        return []


def _reddit_hot(feed_url: str) -> list[dict]:
    """Pull hot posts from a Reddit subreddit JSON feed."""
    try:
        resp = requests.get(
            feed_url,
            headers={"User-Agent": "DailyCarouselBot/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            score = post.get("score", 0)
            if score < 50:  # Skip low-engagement posts
                continue
            subreddit = post.get("subreddit", "")
            results.append({
                "title": post.get("title", ""),
                "description": post.get("selftext", "")[:300],
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "source": f"reddit/r/{subreddit}",
                "score": score,
                "num_comments": post.get("num_comments", 0),
                "upvote_ratio": post.get("upvote_ratio", 0),
            })
        return results
    except Exception as e:
        print(f"[topic] Reddit feed failed for {feed_url}: {e}")
        return []


def research_topics() -> list[dict]:
    """
    Research trending AI topics from multiple sources.
    Returns top 3 candidates scored for carousel potential.
    """
    print("[topic] Researching trending AI topics...")
    all_results = []

    # Brave search -- pick 3 random queries to avoid hitting rate limits
    selected_queries = random.sample(BRAVE_SEARCH_QUERIES, min(3, len(BRAVE_SEARCH_QUERIES)))
    for query in selected_queries:
        results = _brave_search(query, count=5)
        all_results.extend(results)
        time.sleep(0.5)  # Rate limit courtesy

    # Reddit hot posts
    for feed_url in REDDIT_RSS_FEEDS:
        results = _reddit_hot(feed_url)
        all_results.extend(results)
        time.sleep(0.5)

    print(f"[topic] Found {len(all_results)} raw results across all sources")

    # Deduplicate by title similarity (simple check)
    seen_titles = set()
    unique_results = []
    for r in all_results:
        title_key = r["title"].lower().strip()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_results.append(r)

    # Score each result for carousel potential
    for r in unique_results:
        score = 0
        title_lower = r["title"].lower()

        # Carousel-friendly signals (listicles, how-tos, tips)
        list_signals = ["tips", "ways", "tools", "steps", "mistakes", "reasons", "things", "rules", "secrets", "hacks"]
        if any(s in title_lower for s in list_signals):
            score += 30

        how_to_signals = ["how to", "how i", "guide", "tutorial", "beginner", "101"]
        if any(s in title_lower for s in how_to_signals):
            score += 25

        comparison_signals = ["vs", "versus", "compared", "better than", "best"]
        if any(s in title_lower for s in comparison_signals):
            score += 20

        # Relevance to Bishop AI audience
        audience_signals = ["claude", "chatgpt", "ai agent", "automation", "prompt", "no-code", "solopreneur", "business", "workflow", "n8n", "make.com", "zapier"]
        matches = sum(1 for s in audience_signals if s in title_lower)
        score += matches * 10

        # Engagement signals (Reddit)
        reddit_score = r.get("score", 0)
        if reddit_score > 500:
            score += 20
        elif reddit_score > 200:
            score += 10
        elif reddit_score > 100:
            score += 5

        r["carousel_score"] = score

    # Sort by score and return top 3
    unique_results.sort(key=lambda x: x.get("carousel_score", 0), reverse=True)
    top_3 = unique_results[:3]

    for i, t in enumerate(top_3, 1):
        print(f"[topic] #{i}: [{t.get('carousel_score', 0)}] {t['title'][:80]}")

    return top_3


if __name__ == "__main__":
    from pathlib import Path
from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "daily-carousel.env")
    topics = research_topics()
    for t in topics:
        print(f"\n--- {t['title']} ---")
        print(f"  Source: {t['source']}")
        print(f"  Score: {t.get('carousel_score', 0)}")
        print(f"  URL: {t['url']}")
