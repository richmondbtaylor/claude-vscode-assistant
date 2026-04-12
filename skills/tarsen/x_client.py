"""
X (Twitter) Playwright client for TARSEN.

Two modes:
  - LIVE: opens a persistent Chromium context with Rich's stored X session, scrapes
          target accounts' recent tweets, and posts replies. Requires running
          setup_x_session.py once first.
  - DRY-RUN: returns fixture tweets, never opens a browser, never posts. Use this for
             development, testing, and the first end-to-end run before Rich approves
             going live.

The fixture tweets in DRY-RUN are realistic in shape but synthetic in content. They
exist so we can prove the full pipeline (target -> generate -> validate -> log) works
end to end without depending on x.com being scrapable, which may break for many
reasons (rate limits, login walls, layout changes).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from config import X_SESSION_DIR


@dataclass
class Tweet:
    handle: str
    follower_count: int
    tier: str
    text: str
    url: str
    posted_at: datetime
    thread_context: Optional[str] = None


# Fixture tweets for dry-run mode. Synthetic but realistic - drawn from the kinds of
# things the seed accounts actually post about. Used to prove the pipeline end-to-end.
FIXTURE_TWEETS = [
    Tweet(
        handle="kazanjy",
        follower_count=30_000,
        tier="mid",
        text=(
            "Half the 'AI SDR' demos I see are just GPT writing 50 cold emails an hour. "
            "That's not the unlock. The unlock is having an agent that knows which 12 "
            "accounts to call this morning based on signal data your reps would never "
            "have time to read."
        ),
        url="https://x.com/kazanjy/status/fixture-001",
        posted_at=datetime.now(timezone.utc) - timedelta(minutes=8),
    ),
    Tweet(
        handle="kareemamin",
        follower_count=20_000,
        tier="mid",
        text=(
            "The Clay thesis in one line: most go-to-market problems are actually data "
            "problems wearing a strategy costume. Once you can enrich and route on "
            "anything, the 'right play' becomes obvious."
        ),
        url="https://x.com/kareemamin/status/fixture-002",
        posted_at=datetime.now(timezone.utc) - timedelta(minutes=12),
    ),
    Tweet(
        handle="ChrisWalker171",
        follower_count=120_000,
        tier="high",
        text=(
            "Every B2B marketing team I audit in 2026 is over-invested in MQL volume "
            "and under-invested in actually understanding which 200 accounts will close "
            "this quarter. The math hasn't changed. The tooling has."
        ),
        url="https://x.com/ChrisWalker171/status/fixture-003",
        posted_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    ),
]


class XClient:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._pw = None
        self._context = None
        self._page = None

    def __enter__(self):
        if not self.dry_run:
            self._open_browser()
        return self

    def __exit__(self, *args):
        if self._context is not None:
            self._context.close()
        if self._pw is not None:
            self._pw.stop()

    def _open_browser(self):
        from playwright.sync_api import sync_playwright
        X_SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._context = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(X_SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        self._page = self._context.new_page()

    # --- Public API ---

    def fetch_recent_tweets(self, handle: str, max_tweets: int = 5) -> list[Tweet]:
        """Returns a list of recent Tweet objects for the given handle."""
        if self.dry_run:
            return [t for t in FIXTURE_TWEETS if t.handle == handle][:max_tweets]
        return self._scrape_profile(handle, max_tweets)

    def fetch_recent_from_seeds(self, seeds: list[dict], max_per: int = 3) -> list[Tweet]:
        """Returns a flat list of tweets across all seed accounts."""
        if self.dry_run:
            return list(FIXTURE_TWEETS)
        out = []
        for seed in seeds:
            try:
                out.extend(self.fetch_recent_tweets(seed["handle"], max_per))
            except Exception as e:
                print(f"  ! failed to scrape @{seed['handle']}: {e}")
        return out

    def like_tweet(self, tweet_url: str) -> bool:
        if self.dry_run:
            print(f"  [DRY] would like {tweet_url}")
            return True
        return self._click_like(tweet_url)

    def post_reply(self, tweet_url: str, reply_text: str) -> bool:
        if self.dry_run:
            print(f"  [DRY] would post reply to {tweet_url}:")
            print(f"        {reply_text}")
            return True
        return self._post_reply(tweet_url, reply_text)

    # --- Live Playwright implementations (used only when dry_run=False) ---
    # These are intentionally minimal scaffolding. They will work for a logged-in
    # session but Rich should test in headed mode first and tune selectors if X
    # changes their DOM, which they do constantly.

    def _scrape_profile(self, handle: str, max_tweets: int) -> list[Tweet]:
        page = self._page
        page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        tweets = []
        articles = page.locator("article[data-testid='tweet']").all()[:max_tweets]
        for art in articles:
            try:
                text = art.locator("div[data-testid='tweetText']").first.inner_text(timeout=2000)
                time_el = art.locator("time").first
                ts = time_el.get_attribute("datetime")
                link_el = art.locator("a[href*='/status/']").first
                href = link_el.get_attribute("href")
                if not href or not text:
                    continue
                tweets.append(Tweet(
                    handle=handle,
                    follower_count=0,  # Filled in by orchestrator from seed_accounts tier mapping
                    tier="mid",
                    text=text,
                    url=f"https://x.com{href}",
                    posted_at=datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.now(timezone.utc),
                ))
            except Exception:
                continue
        return tweets

    def _click_like(self, tweet_url: str) -> bool:
        page = self._page
        page.goto(tweet_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        try:
            page.locator("button[data-testid='like']").first.click(timeout=5000)
            return True
        except Exception as e:
            print(f"  ! like failed: {e}")
            return False

    def _post_reply(self, tweet_url: str, reply_text: str) -> bool:
        page = self._page
        page.goto(tweet_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        try:
            # click the reply icon, type, and submit
            page.locator("button[data-testid='reply']").first.click(timeout=5000)
            page.wait_for_timeout(1500)
            page.locator("div[data-testid='tweetTextarea_0']").first.fill(reply_text)
            page.wait_for_timeout(800)
            page.locator("button[data-testid='tweetButton']").first.click(timeout=5000)
            page.wait_for_timeout(2500)
            return True
        except Exception as e:
            print(f"  ! reply post failed: {e}")
            return False
