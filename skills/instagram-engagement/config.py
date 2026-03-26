"""
Instagram Engagement Automation — Configuration
All tunable settings live here. Edit this file to change behavior without touching the logic.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Rate limits (strictly enforced per account per window)
# ---------------------------------------------------------------------------

RATE_LIMITS_HOURLY = {
    "follows": 20,
    "comments": 30,
    "likes": 50,
}

RATE_LIMITS_DAILY = {
    "follows": 100,
    "comments": 120,
    "likes": 200,
}

# ---------------------------------------------------------------------------
# Timing / human-like behavior
# ---------------------------------------------------------------------------

# Random delay range (seconds) between every action
ACTION_DELAY_RANGE = (45, 120)

# Break taken every ~60 minutes of activity (seconds)
HOURLY_BREAK_RANGE = (300, 600)  # 5–10 minutes

# Delay between scrolling through a profile (seconds)
SCROLL_DELAY_RANGE = (2, 5)

# ---------------------------------------------------------------------------
# Humanization — randomized action probabilities per target
#
# Not every target gets every action. These probabilities control how often
# each action fires, so the pattern looks organic rather than robotic.
# ---------------------------------------------------------------------------

# Chance of liking posts for any given target (almost always — likes are low-risk)
LIKE_PROBABILITY = 0.92

# Chance of commenting (less frequent — more weight, more human)
COMMENT_PROBABILITY = 0.55

# Chance of following (selective — quality over quantity)
FOLLOW_PROBABILITY = 0.65

# Chance any given comment includes a single emoji (~1 in 3)
EMOJI_PROBABILITY = 0.30

# Randomly vary how many posts to like per target (overrides POSTS_TO_LIKE bounds)
# The actual count is sampled from this range each time
LIKES_PER_TARGET_RANGE = (1, 3)

# ---------------------------------------------------------------------------
# Target account filtering criteria
# ---------------------------------------------------------------------------

MIN_FOLLOWERS = 500
MAX_POST_AGE_DAYS = 7          # Account must have posted within this window to engage
MIN_FOLLOW_RATIO = 0.5         # followers / following must be >= this value
BIO_KEYWORDS = ["AI", "automation", "consulting", "artificial intelligence"]
POSTS_TO_LIKE = (2, 3)         # Like this many recent posts per target (min, max)

# Post recency for comment + follow gating (days)
# If most recent post is older than this, only like — no comment or follow
COMMENT_FOLLOW_MAX_POST_AGE_DAYS = 14

# ---------------------------------------------------------------------------
# Engagement history / cooldowns
# ---------------------------------------------------------------------------

# Don't comment on the same account's posts within this window
COMMENT_COOLDOWN_DAYS = 30

# Days to wait for a follow-back before unfollowing
FOLLOW_BACK_WAIT_DAYS = 7

# ---------------------------------------------------------------------------
# Credentials (loaded from .env per account)
# Account credentials are accessed via get_credentials(account_name)
# ---------------------------------------------------------------------------

def get_credentials(account_name: str) -> dict:
    """Load Instagram credentials for the given account from environment variables."""
    username = os.getenv(f"IG_{account_name}_USERNAME")
    password = os.getenv(f"IG_{account_name}_PASSWORD")
    if not username or not password:
        raise ValueError(
            f"Credentials for account '{account_name}' not found in .env. "
            f"Expected IG_{account_name}_USERNAME and IG_{account_name}_PASSWORD."
        )
    return {"username": username, "password": password}


# ---------------------------------------------------------------------------
# Competitor accounts to scrape followers from (optional)
# ---------------------------------------------------------------------------

COMPETITOR_ACCOUNTS = [
    a.strip()
    for a in os.getenv("COMPETITOR_ACCOUNTS", "").split(",")
    if a.strip()
]

# ---------------------------------------------------------------------------
# Unfollow whitelist — these accounts are never unfollowed
# ---------------------------------------------------------------------------

UNFOLLOW_WHITELIST = set(
    a.strip().lower()
    for a in os.getenv("UNFOLLOW_WHITELIST", "").split(",")
    if a.strip()
)

# ---------------------------------------------------------------------------
# Default hashtag targets (used if no --focus is specified)
# ---------------------------------------------------------------------------

DEFAULT_HASHTAGS = [
    "#AIautomation",
    "#ProcessAutomation",
    "#ClaudeAI",
    "#AIeducation",
    "#PromptEngineering",
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "engagement.db")

# ---------------------------------------------------------------------------
# Claude model for comment generation
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-6"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
