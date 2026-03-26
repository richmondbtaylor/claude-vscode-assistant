"""
Instagram Session — Playwright headless browser for all Instagram interactions.

Handles:
  - Login and session persistence
  - Login challenge detection (captcha, 2FA, suspicious activity)
  - Hashtag search and post author collection
  - Profile scraping (followers, following, post count, bio, recent post date)
  - Account filtering
  - Liking, commenting, following, unfollowing
"""

import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PWTimeout

from config import (
    ACTION_DELAY_RANGE,
    SCROLL_DELAY_RANGE,
    MIN_FOLLOWERS,
    MAX_POST_AGE_DAYS,
    MIN_FOLLOW_RATIO,
    BIO_KEYWORDS,
    POSTS_TO_LIKE,
    COMMENT_FOLLOW_MAX_POST_AGE_DAYS,
    COMPETITOR_ACCOUNTS,
)

logger = logging.getLogger(__name__)

SESSION_DIR = Path(__file__).parent / ".browser_sessions"
SESSION_DIR.mkdir(exist_ok=True)

IG_BASE = "https://www.instagram.com"


class LoginChallengeError(Exception):
    """Raised when Instagram presents a login challenge (captcha, 2FA, etc.)."""
    pass


class RateLimitError(Exception):
    """Raised when Instagram signals a rate limit / action block."""
    pass


def _human_delay(low: float = None, high: float = None):
    lo, hi = (low, high) if low is not None else ACTION_DELAY_RANGE
    time.sleep(random.uniform(lo, hi))


def _scroll_delay():
    time.sleep(random.uniform(*SCROLL_DELAY_RANGE))


class InstagramSession:
    def __init__(self, account_name: str, username: str, password: str, dry_run: bool = False):
        self.account_name = account_name
        self.username = username
        self.password = password
        self.dry_run = dry_run
        self._pw = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self.page: Page = None
        self._session_file = SESSION_DIR / f"{account_name}_session.json"

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        if self._session_file.exists():
            self._context = self._browser.new_context(storage_state=str(self._session_file))
            logger.info(f"[{self.account_name}] Loaded saved session from {self._session_file}")
        else:
            self._context = self._browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )
        self.page = self._context.new_page()
        self._login()

    def stop(self):
        if self._context:
            self._context.storage_state(path=str(self._session_file))
            logger.info(f"[{self.account_name}] Session saved to {self._session_file}")
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def _login(self):
        self.page.goto(f"{IG_BASE}/accounts/login/", wait_until="networkidle", timeout=30000)
        _scroll_delay()

        # Already logged in (redirected away from login page)
        if "/accounts/login/" not in self.page.url:
            logger.info(f"[{self.account_name}] Already logged in via saved session")
            return

        try:
            self.page.fill('input[name="username"]', self.username, timeout=10000)
            _scroll_delay()
            self.page.fill('input[name="password"]', self.password, timeout=10000)
            _scroll_delay()
            self.page.click('button[type="submit"]', timeout=10000)
            self.page.wait_for_load_state("networkidle", timeout=20000)
        except PWTimeout:
            raise LoginChallengeError(f"[{self.account_name}] Login form timed out — possible challenge or page change")

        self._check_login_challenges()

        # Dismiss "Save login info" and "Turn on notifications" dialogs
        for dismiss_text in ["Not Now", "Not now"]:
            try:
                btn = self.page.get_by_role("button", name=dismiss_text)
                if btn.is_visible(timeout=3000):
                    btn.click()
                    _scroll_delay()
            except Exception:
                pass

        logger.info(f"[{self.account_name}] Login successful")

    def _check_login_challenges(self):
        url = self.page.url
        challenge_patterns = [
            "/challenge/",
            "/two_factor",
            "/checkpoint/",
            "accounts/suspended",
            "unusual login",
        ]
        for pattern in challenge_patterns:
            if pattern in url:
                raise LoginChallengeError(
                    f"[{self.account_name}] Login challenge detected at {url}. "
                    "Please complete it manually in a regular browser, then retry."
                )

        # Also check page text
        content = self.page.content().lower()
        suspicious_phrases = ["suspicious login", "verify your identity", "enter the code", "we detected"]
        for phrase in suspicious_phrases:
            if phrase in content:
                raise LoginChallengeError(
                    f"[{self.account_name}] Suspicious activity prompt detected. "
                    "Complete verification manually in a browser, then retry."
                )

    # ------------------------------------------------------------------
    # Target Discovery
    # ------------------------------------------------------------------

    def get_hashtag_targets(self, hashtag: str, max_accounts: int = 60) -> list[str]:
        """Collect unique usernames from recent posts under a hashtag."""
        tag = hashtag.lstrip("#")
        url = f"{IG_BASE}/explore/tags/{tag}/"
        logger.info(f"[{self.account_name}] Searching hashtag #{tag}")
        self.page.goto(url, wait_until="networkidle", timeout=30000)
        _scroll_delay()

        usernames = set()
        # Collect post links from the grid
        post_links = self.page.query_selector_all('a[href*="/p/"]')
        for link in post_links[:max_accounts * 2]:
            try:
                href = link.get_attribute("href")
                if href:
                    self.page.goto(f"{IG_BASE}{href}", wait_until="networkidle", timeout=20000)
                    _scroll_delay()
                    username = self._get_post_author()
                    if username:
                        usernames.add(username)
                    self.page.go_back(wait_until="networkidle", timeout=15000)
                    _scroll_delay()
                    if len(usernames) >= max_accounts:
                        break
            except Exception as e:
                logger.warning(f"Error collecting hashtag target: {e}")
                continue

        logger.info(f"[{self.account_name}] Found {len(usernames)} targets from #{tag}")
        return list(usernames)

    def get_competitor_followers(self, competitor_username: str, max_accounts: int = 40) -> list[str]:
        """Collect follower usernames from a competitor account."""
        url = f"{IG_BASE}/{competitor_username}/followers/"
        logger.info(f"[{self.account_name}] Scraping followers of @{competitor_username}")
        try:
            self.page.goto(f"{IG_BASE}/{competitor_username}/", wait_until="networkidle", timeout=20000)
            _scroll_delay()
            # Click followers link
            followers_link = self.page.query_selector('a[href$="/followers/"]')
            if not followers_link:
                return []
            followers_link.click()
            self.page.wait_for_timeout(3000)

            usernames = set()
            rows = self.page.query_selector_all('span[class*="x1lliihq"]')  # username spans in followers modal
            for row in rows[:max_accounts]:
                try:
                    text = row.inner_text().strip()
                    if text and "/" not in text and " " not in text:
                        usernames.add(text)
                except Exception:
                    continue

            # Close modal
            self.page.keyboard.press("Escape")
            return list(usernames)[:max_accounts]
        except Exception as e:
            logger.warning(f"Could not scrape followers of @{competitor_username}: {e}")
            return []

    # ------------------------------------------------------------------
    # Profile Scraping
    # ------------------------------------------------------------------

    def get_profile_info(self, username: str) -> dict | None:
        """
        Scrape profile info. Returns dict with keys:
          followers, following, post_count, bio, recent_post_date, is_private
        Returns None if profile is unavailable or private.
        """
        try:
            self.page.goto(f"{IG_BASE}/{username}/", wait_until="networkidle", timeout=20000)
            _scroll_delay()

            # Check for private account or "Page not found"
            content = self.page.content()
            if "Sorry, this page" in content or "isn't available" in content:
                return None

            is_private = "This account is private" in content or "private" in content.lower()

            # Parse follower/following counts from meta description or visible spans
            counts = self._parse_counts()
            bio = self._parse_bio()
            recent_post_date = self._get_most_recent_post_date() if not is_private else None

            return {
                "username": username,
                "followers": counts.get("followers", 0),
                "following": counts.get("following", 0),
                "post_count": counts.get("posts", 0),
                "bio": bio,
                "recent_post_date": recent_post_date,
                "is_private": is_private,
            }
        except Exception as e:
            logger.warning(f"Could not scrape profile @{username}: {e}")
            return None

    def _parse_counts(self) -> dict:
        """Extract follower/following counts from profile page."""
        counts = {}
        try:
            # Instagram renders counts in <span> elements within the stats section
            meta = self.page.query_selector('meta[name="description"]')
            if meta:
                desc = meta.get_attribute("content") or ""
                # Format: "X Followers, Y Following, Z Posts"
                import re
                m = re.findall(r"([\d,]+\.?\d*[KMkm]?)\s+(Followers?|Following|Posts?)", desc, re.IGNORECASE)
                for val_str, label in m:
                    val = _parse_count_value(val_str)
                    key = label.lower().rstrip("s")
                    counts[key] = val
        except Exception:
            pass
        return counts

    def _parse_bio(self) -> str:
        try:
            # Bio lives in a <span> inside the profile header
            bio_el = self.page.query_selector('span[class*="x1lliihq"]:not([class*="xlyipyv"])')
            return bio_el.inner_text().strip() if bio_el else ""
        except Exception:
            return ""

    def _get_most_recent_post_date(self) -> datetime | None:
        """Navigate into the most recent post and extract its timestamp."""
        try:
            first_post = self.page.query_selector('a[href*="/p/"]')
            if not first_post:
                return None
            href = first_post.get_attribute("href")
            self.page.goto(f"{IG_BASE}{href}", wait_until="networkidle", timeout=20000)
            _scroll_delay()
            time_el = self.page.query_selector("time[datetime]")
            if time_el:
                dt_str = time_el.get_attribute("datetime")
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
            self.page.go_back(wait_until="networkidle", timeout=15000)
        except Exception as e:
            logger.debug(f"Could not get post date: {e}")
        return None

    def _get_post_author(self) -> str | None:
        try:
            # Author link appears as /username/ in post header
            author_link = self.page.query_selector('header a[href^="/"]')
            if author_link:
                href = author_link.get_attribute("href") or ""
                username = href.strip("/")
                if username and "/" not in username:
                    return username
        except Exception:
            pass
        return None

    def _get_post_caption(self) -> str:
        try:
            cap_el = self.page.query_selector('div[class*="x5yr21d"] span')
            return cap_el.inner_text().strip() if cap_el else ""
        except Exception:
            return ""

    def _get_recent_post_links(self, profile_url: str, count: int = 3) -> list[str]:
        """Return up to `count` recent post hrefs from a profile."""
        links = []
        try:
            self.page.goto(profile_url, wait_until="networkidle", timeout=20000)
            _scroll_delay()
            post_els = self.page.query_selector_all('a[href*="/p/"]')
            for el in post_els[:count]:
                href = el.get_attribute("href")
                if href:
                    links.append(f"{IG_BASE}{href}")
        except Exception as e:
            logger.warning(f"Could not get post links: {e}")
        return links

    # ------------------------------------------------------------------
    # Account Filtering
    # ------------------------------------------------------------------

    def passes_filter(self, profile: dict) -> bool:
        """Return True if the profile meets all engagement criteria."""
        if profile is None:
            return False

        username = profile.get("username", "")
        followers = profile.get("followers", 0)
        following = profile.get("following", 1)
        bio = profile.get("bio", "").lower()
        recent_post_date = profile.get("recent_post_date")
        is_private = profile.get("is_private", False)

        if is_private:
            logger.debug(f"@{username}: filtered — private account")
            return False

        if followers < MIN_FOLLOWERS:
            logger.debug(f"@{username}: filtered — only {followers} followers")
            return False

        ratio = followers / max(following, 1)
        if ratio < MIN_FOLLOW_RATIO:
            logger.debug(f"@{username}: filtered — ratio {ratio:.2f} < {MIN_FOLLOW_RATIO}")
            return False

        if not any(kw.lower() in bio for kw in BIO_KEYWORDS):
            logger.debug(f"@{username}: filtered — bio keywords not found")
            return False

        if recent_post_date:
            age_days = (datetime.utcnow() - recent_post_date).days
            if age_days > MAX_POST_AGE_DAYS:
                logger.debug(f"@{username}: filtered — last post {age_days} days ago")
                return False

        # Aggregator heuristic: very high following relative to followers = likely aggregator
        if following > followers * 5 and following > 5000:
            logger.debug(f"@{username}: filtered — likely aggregator (following {following})")
            return False

        return True

    def is_recent_enough_for_comment(self, profile: dict) -> bool:
        """Post must be <= COMMENT_FOLLOW_MAX_POST_AGE_DAYS old to comment + follow."""
        recent_post_date = profile.get("recent_post_date")
        if not recent_post_date:
            return False
        age_days = (datetime.utcnow() - recent_post_date).days
        return age_days <= COMMENT_FOLLOW_MAX_POST_AGE_DAYS

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def like_post(self, post_url: str) -> bool:
        """Navigate to a post and like it. Returns True on success."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would like: {post_url}")
            return True
        try:
            self.page.goto(post_url, wait_until="networkidle", timeout=20000)
            _scroll_delay()
            # Like button: aria-label contains "Like"
            like_btn = self.page.get_by_role("button", name="Like")
            if like_btn.is_visible(timeout=5000):
                like_btn.click()
                logger.info(f"Liked: {post_url}")
                return True
            # Already liked check
            unlike_btn = self.page.get_by_role("button", name="Unlike")
            if unlike_btn.is_visible(timeout=2000):
                logger.debug(f"Already liked: {post_url}")
                return True
        except Exception as e:
            logger.warning(f"Like failed ({post_url}): {e}")
            self._check_action_block()
        return False

    def comment_on_post(self, post_url: str, comment_text: str) -> bool:
        """Navigate to a post and leave a comment. Returns True on success."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would comment on {post_url}: {comment_text}")
            return True
        try:
            self.page.goto(post_url, wait_until="networkidle", timeout=20000)
            _scroll_delay()
            comment_box = self.page.get_by_placeholder("Add a comment…")
            comment_box.click(timeout=5000)
            _scroll_delay()
            comment_box.type(comment_text, delay=random.uniform(30, 80))  # human-like typing
            _scroll_delay()
            # Submit with Enter
            comment_box.press("Enter")
            self.page.wait_for_timeout(2000)
            logger.info(f"Commented on {post_url}: {comment_text[:60]}...")
            return True
        except Exception as e:
            logger.warning(f"Comment failed ({post_url}): {e}")
            self._check_action_block()
        return False

    def follow_user(self, username: str) -> bool:
        """Navigate to profile and follow. Returns True on success."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would follow: @{username}")
            return True
        try:
            self.page.goto(f"{IG_BASE}/{username}/", wait_until="networkidle", timeout=20000)
            _scroll_delay()
            follow_btn = self.page.get_by_role("button", name="Follow")
            if follow_btn.is_visible(timeout=5000):
                follow_btn.click()
                logger.info(f"Followed: @{username}")
                return True
            # Already following
            following_btn = self.page.get_by_role("button", name="Following")
            if following_btn.is_visible(timeout=2000):
                logger.debug(f"Already following: @{username}")
                return True
        except Exception as e:
            logger.warning(f"Follow failed (@{username}): {e}")
            self._check_action_block()
        return False

    def unfollow_user(self, username: str) -> bool:
        """Navigate to profile and unfollow. Returns True on success."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would unfollow: @{username}")
            return True
        try:
            self.page.goto(f"{IG_BASE}/{username}/", wait_until="networkidle", timeout=20000)
            _scroll_delay()
            following_btn = self.page.get_by_role("button", name="Following")
            if following_btn.is_visible(timeout=5000):
                following_btn.click()
                _scroll_delay()
                # Confirm unfollow in dialog
                unfollow_confirm = self.page.get_by_role("button", name="Unfollow")
                if unfollow_confirm.is_visible(timeout=3000):
                    unfollow_confirm.click()
                logger.info(f"Unfollowed: @{username}")
                return True
        except Exception as e:
            logger.warning(f"Unfollow failed (@{username}): {e}")
        return False

    def check_follows_back(self, username: str) -> bool:
        """Check if a user follows us back by looking at their follower list."""
        try:
            self.page.goto(f"{IG_BASE}/{username}/followers/", wait_until="networkidle", timeout=20000)
            _scroll_delay()
            # Search for our username in the followers list (limited heuristic)
            content = self.page.content()
            return self.username.lower() in content.lower()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Error / block detection
    # ------------------------------------------------------------------

    def _check_action_block(self):
        """Check if Instagram has issued an action block."""
        content = self.page.content().lower()
        block_phrases = [
            "action blocked",
            "we restrict certain activity",
            "try again later",
            "you've been blocked",
        ]
        for phrase in block_phrases:
            if phrase in content:
                raise RateLimitError(
                    f"[{self.account_name}] Instagram action block detected: '{phrase}'"
                )

    def get_recent_post_with_caption(self, username: str) -> tuple[str, str]:
        """
        Return (post_url, caption) for the most recent post of a user.
        Returns ("", "") if unavailable.
        """
        try:
            self.page.goto(f"{IG_BASE}/{username}/", wait_until="networkidle", timeout=20000)
            _scroll_delay()
            first_post = self.page.query_selector('a[href*="/p/"]')
            if not first_post:
                return "", ""
            href = first_post.get_attribute("href")
            post_url = f"{IG_BASE}{href}"
            self.page.goto(post_url, wait_until="networkidle", timeout=20000)
            _scroll_delay()
            caption = self._get_post_caption()
            return post_url, caption
        except Exception as e:
            logger.warning(f"Could not get recent post for @{username}: {e}")
            return "", ""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_count_value(val_str: str) -> int:
    """Convert '12.3K' or '1,234' to int."""
    import re
    val_str = val_str.replace(",", "").strip()
    multipliers = {"K": 1_000, "M": 1_000_000, "k": 1_000, "m": 1_000_000}
    for suffix, mult in multipliers.items():
        if val_str.endswith(suffix):
            try:
                return int(float(val_str[:-1]) * mult)
            except ValueError:
                return 0
    try:
        return int(float(val_str))
    except ValueError:
        return 0
