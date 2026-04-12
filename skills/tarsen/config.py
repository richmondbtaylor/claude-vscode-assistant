"""
TARSEN configuration. Constants, paths, and tunable knobs.

Reads ANTHROPIC_API_KEY from .env (copy from bishop-research-agent or set manually).
"""
import os
from datetime import time as dtime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# --- Anthropic ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-4-5"  # Sonnet 4.5 - the right tier for structured-tone reply generation

# --- Google Sheet ---
SHEET_ID = "1em3nkXBeQAEaAbVZbE-Aif6PmVtSV1QkPsurKnKPdWU"
GSPREAD_TOKEN_PATH = os.path.expanduser(r"~\AppData\Roaming\gspread\authorized_user.json")
GSPREAD_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# --- Playwright X session ---
X_SESSION_DIR = ROOT / "x_session"  # persistent browser context lives here

# --- Operational windows (Eastern Time) ---
ACTIVE_HOURS_START = dtime(7, 0)   # 7:00 AM ET
ACTIVE_HOURS_END = dtime(23, 0)    # 11:00 PM ET
TIMEZONE = "America/New_York"

# --- Warm-up schedule (day of operation -> daily reply cap) ---
def daily_cap_for_day(day_index: int) -> int:
    """day_index is 1-based: day 1 is first day of operation."""
    if day_index <= 7:
        return 8           # week 1: 5-10/day, default 8
    if day_index <= 14:
        return 15          # week 2
    if day_index <= 21:
        return 22          # week 3
    return 50              # week 4+: ramp toward 40-60

# --- Reply timing ---
LIKE_TO_POST_DELAY_SECONDS = (10, 45)         # random sleep between like and post
MIN_TWEET_AGE_MINUTES = (3, 20)               # min age of tweet before TARSEN replies (random per run)
MAX_REPLY_WORDS_DEFAULT = 40
MAX_REPLY_WORDS_DEEP = 80                     # only when tweet warrants depth

# --- Targeting ---
MAX_REPLIES_PER_ACCOUNT_PER_DAY = 2
MIN_AUTHOR_FOLLOWERS = 5_000
SEARCH_KEYWORDS = ["AI automation", "RevOps", "GTM strategy", "pipeline generation"]

# --- Banlists (loaded from sheet at runtime, but these are minimum hard-coded fallbacks) ---
HARDCODED_BANNED_OPENERS = [
    "great point", "love this", "100%", "this!", "so true", "absolutely",
    "couldn't agree more", "nailed it", "spot on", "well said",
    "hot take", "game changer", "mind blown",
]
EM_DASH = chr(0x2014)  # never write a literal em dash anywhere in the codebase

# --- Logging ---
LOG_FILE = ROOT / "tarsen.log"
