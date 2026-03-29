"""
Instagram Engagement Automation — Configuration
All tunable settings live here. Edit this file to change behavior without touching the logic.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Rate limits (strictly enforced per account per window)
# These are the MAXIMUM limits (graduated accounts, day 22+).
# During ramp-up, get_ramp_up_limits() overrides these.
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
# RISEN: 21-Day Ramp-Up Matrix (safety protocol for new/existing accounts)
# Day 1 = first day the account was used by this bot.
# ---------------------------------------------------------------------------

RAMP_UP_MATRIX = [
    {"days": (1,  3),    "follows": 2,   "comments": 0,   "likes": 12,  "sessions": 2},
    {"days": (4,  7),    "follows": 8,   "comments": 5,   "likes": 35,  "sessions": 3},
    {"days": (8,  14),   "follows": 15,  "comments": 15,  "likes": 85,  "sessions": 4},
    {"days": (15, 21),   "follows": 30,  "comments": 45,  "likes": 180, "sessions": 5},
    {"days": (22, 9999), "follows": 100, "comments": 120, "likes": 200, "sessions": 5},
]


def get_ramp_up_limits(day_number: int) -> dict:
    """Return daily action limits for the given ramp-up day (1-based)."""
    for tier in RAMP_UP_MATRIX:
        start, end = tier["days"]
        if start <= day_number <= end:
            return {
                "follows": tier["follows"],
                "comments": tier["comments"],
                "likes": tier["likes"],
                "sessions": tier["sessions"],
            }
    return {"follows": 100, "comments": 120, "likes": 200, "sessions": 5}


# ---------------------------------------------------------------------------
# Timing / human-like behavior (RISEN inter-action delay: 45–210s)
# ---------------------------------------------------------------------------

# Random delay range (seconds) between every action
ACTION_DELAY_RANGE = (45, 210)

# Break taken between sessions (inter-session delay)
INTER_SESSION_DELAY_RANGE = (30 * 60, 90 * 60)  # 30–90 minutes in seconds

# How long each active session block runs (minutes)
SESSION_ACTIVE_DURATION_RANGE = (20, 25)

# Break taken every ~60 minutes within a session (seconds) — kept as fallback
HOURLY_BREAK_RANGE = (300, 600)  # 5–10 minutes

# Delay between scrolling through a profile (seconds)
SCROLL_DELAY_RANGE = (2, 5)

# ---------------------------------------------------------------------------
# RISEN: Blackout window — no operations during this local time range
# ---------------------------------------------------------------------------

BLACKOUT_START = (22, 10)  # 10:10 PM
BLACKOUT_END = (7, 35)     # 7:35 AM

# ---------------------------------------------------------------------------
# Humanization — randomized action probabilities per target
# ---------------------------------------------------------------------------

# Chance of liking posts for a standard target
LIKE_PROBABILITY = 0.92

# Authority targets: only like 60% of their posts (simulates human taste)
AUTHORITY_LIKE_PROBABILITY = 0.60

# Chance of commenting (less frequent — more weight, more human)
COMMENT_PROBABILITY = 0.55

# Chance of following (selective — quality over quantity)
FOLLOW_PROBABILITY = 0.65

# Chance any given comment includes a single emoji (~1 in 3)
EMOJI_PROBABILITY = 0.30

# Randomly vary how many posts to like per target
LIKES_PER_TARGET_RANGE = (1, 3)

# ---------------------------------------------------------------------------
# Target account filtering criteria
# ---------------------------------------------------------------------------

MIN_FOLLOWERS = 300
MAX_POST_AGE_DAYS = 14         # Account must have posted within this window to engage
MIN_FOLLOW_RATIO = 0.3         # followers / following must be >= this value
BIO_KEYWORDS = [
    # Core AI/automation terms
    "AI", "artificial intelligence", "automation", "machine learning", "ML",
    "LLM", "ChatGPT", "GPT", "Claude", "prompt engineering",
    # Tools/platforms
    "n8n", "make.com", "zapier", "airtable", "notion",
    # Business/creator identity
    "consulting", "agency", "founder", "entrepreneur", "coach",
    "solopreneur", "business owner", "online business",
    # Broader creator/tech terms
    "no-code", "low-code", "workflow", "productivity", "digital marketing",
    "content creator", "tech", "saas", "builder",
]
POSTS_TO_LIKE = (2, 3)

# Post recency for comment + follow gating (days)
COMMENT_FOLLOW_MAX_POST_AGE_DAYS = 14

# ---------------------------------------------------------------------------
# Engagement history / cooldowns
# ---------------------------------------------------------------------------

COMMENT_COOLDOWN_DAYS = 30
FOLLOW_BACK_WAIT_DAYS = 7
REENGAGE_CADENCE_DAYS = 3      # Re-engage followed accounts every N days

# ---------------------------------------------------------------------------
# RISEN: Content abort keywords
# If a post caption contains any of these, abort ALL engagement immediately.
# ---------------------------------------------------------------------------

CONTENT_ABORT_KEYWORDS = [
    "sad", "rip", "rest in peace", "loss", "passed away", "in memoriam",
    "grief", "heartbroken", "devastating", "our thoughts", "condolences",
    "frustrated", "this hurts", "i'm done",
    "wedding", "vacation", "honeymoon", "birthday party", "baby shower",
    "we're hiring", "job opening", "open position", "now hiring",
    "we are hiring", "join our team", "open role", "apply now",
    "politics", "election", "vote for",
]

# ---------------------------------------------------------------------------
# RISEN: Authority accounts (Category A) — fixed list of top leaders to monitor
# Set in .env: AUTHORITY_ACCOUNTS=user1,user2,user3
# ---------------------------------------------------------------------------

AUTHORITY_ACCOUNTS = [
    a.strip() for a in os.getenv("AUTHORITY_ACCOUNTS", "").split(",") if a.strip()
]

# ---------------------------------------------------------------------------
# Credentials (loaded from .env per account)
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
# Competitor accounts to scrape followers from (optional, Category B source)
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
# Default hashtag targets
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
