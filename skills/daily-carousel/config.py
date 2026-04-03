"""
Daily Carousel Pipeline -- Configuration.

CTA rotation, topic sources, style presets, brand colors.
"""

import json
import os
from datetime import datetime

# ── Brand Colors (Bishop AI) ─────────────────────────────────────────────────

BRAND = {
    "white": "#FAFBFA",
    "off_white": "#E6E2DE",
    "dark_navy": "#1D2333",
    "deep_navy": "#000813",
    "gold": "#E0B848",
    "blue": "#1894C9",
}

# ── Style Presets ─────────────────────────────────────────────────────────────

STYLE_PRESETS = {
    "clean_editorial": {
        "background": "#F5F0E8",
        "text_color": "#1A1A1A",
        "accent": "#D4A853",
        "best_for": "tips, frameworks, educational",
    },
    "dark_professional": {
        "background": "#0A0A0A",
        "text_color": "#FFFFFF",
        "accent": "#FF6B35",
        "best_for": "tech, tools, comparisons",
    },
    "bold_minimal": {
        "background": "#FFFFFF",
        "text_color": "#000000",
        "accent": "#E8453C",
        "best_for": "hooks, contrarian takes, CTAs",
    },
    "bishop_ai_brand": {
        "background": BRAND["white"],
        "text_color": BRAND["deep_navy"],
        "accent": BRAND["gold"],
        "best_for": "brand content, client-facing",
    },
    "notebook_sketch": {
        "background": "#F8F6F0",
        "text_color": "#2D2D2D",
        "accent": "watercolor brush highlights",
        "best_for": "story arcs, personal insights",
    },
}

# ── CTA Rotation ─────────────────────────────────────────────────────────────

CTA_POOL = [
    {
        "slide_text": "Follow @bishop_ai_ for daily AI tips",
        "caption_text": "Follow @bishop_ai_ for more",
        "type": "follow",
    },
    {
        "slide_text": "Save this for your next build",
        "caption_text": "Save this and try one today",
        "type": "save",
    },
    {
        "slide_text": "Share with a founder who needs this",
        "caption_text": "Tag a founder who needs to see this",
        "type": "share",
    },
    {
        "slide_text": "Drop your favorite tip in the comments",
        "caption_text": "Which tip are you trying first? Comment below",
        "type": "comment",
    },
    {
        "slide_text": "Tag someone still doing this manually",
        "caption_text": "Tag someone who needs to automate this",
        "type": "share",
    },
    {
        "slide_text": "Comment BUILDER for the full breakdown",
        "caption_text": "Comment BUILDER and I'll send you the full guide",
        "type": "dm",
    },
    {
        "slide_text": "Which one surprised you? Tell me below",
        "caption_text": "Which one surprised you most? Drop a comment",
        "type": "comment",
    },
]

CTA_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "cta_history.json")


def get_next_cta() -> dict:
    """Pick a CTA that hasn't been used in the last 5 days."""
    history = []
    if os.path.exists(CTA_HISTORY_FILE):
        with open(CTA_HISTORY_FILE, "r") as f:
            history = json.load(f)

    recent_texts = [h["slide_text"] for h in history[-5:]]
    available = [c for c in CTA_POOL if c["slide_text"] not in recent_texts]

    if not available:
        available = CTA_POOL

    # Prefer comment/share CTAs on weekdays (more engagement)
    day = datetime.now().weekday()
    if day < 5:  # Weekday
        engagement_ctas = [c for c in available if c["type"] in ("comment", "share")]
        if engagement_ctas:
            chosen = engagement_ctas[0]
        else:
            chosen = available[0]
    else:  # Weekend
        follow_ctas = [c for c in available if c["type"] == "follow"]
        if follow_ctas:
            chosen = follow_ctas[0]
        else:
            chosen = available[0]

    # Record usage
    history.append({"slide_text": chosen["slide_text"], "date": datetime.now().strftime("%Y-%m-%d")})
    with open(CTA_HISTORY_FILE, "w") as f:
        json.dump(history[-30:], f, indent=2)

    return chosen


# ── Topic Research Config ─────────────────────────────────────────────────────

BRAVE_SEARCH_QUERIES = [
    "AI tools trending this week 2026",
    "Claude Code tips developers",
    "AI automation for business",
    "best AI workflows solopreneurs",
    "ChatGPT vs Claude comparison",
    "AI agents business use cases",
    "prompt engineering tips 2026",
    "no-code AI automation tools",
    "AI for small business owners",
    "vibe coding AI development",
]

REDDIT_RSS_FEEDS = [
    "https://www.reddit.com/r/ClaudeAI/hot/.json?limit=10",
    "https://www.reddit.com/r/ChatGPT/hot/.json?limit=10",
    "https://www.reddit.com/r/artificial/hot/.json?limit=10",
    "https://www.reddit.com/r/LocalLLaMA/hot/.json?limit=10",
    "https://www.reddit.com/r/singularity/hot/.json?limit=10",
]

# ── Content Generation Config ─────────────────────────────────────────────────

HANDLE = "@bishop_ai_"
SLIDE_COUNT_RANGE = (6, 8)
ASPECT_RATIO = "4:5"
RESOLUTION = "2K"

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
KIE_SCRIPT = os.path.join(BASE_DIR, "..", "infographic-generator", "scripts", "generate_kie.py")
GDRIVE_SCRIPT = os.path.join(BASE_DIR, "..", "infographic-generator", "scripts", "upload_gdrive.py")
