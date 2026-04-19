"""
Daily Carousel Pipeline -- Main orchestrator.

Run:  python main.py          # Full pipeline (research -> generate -> images -> slack)
      python main.py --dry    # Research + content only, no images or Slack
      python main.py --test   # Use test topics, skip research
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime

# Windows terminals default to cp1252 which can't handle Unicode.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "daily-carousel.env")

from content_generator import generate_content
from image_generator import generate_images
from slack_notifier import send_slack_approval, send_slack_error
from topic_researcher import research_topics


def _save_run_log(carousel: dict, image_paths: list, drive_links: list, duration_s: float):
    """Save a JSON log of each pipeline run for history."""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.json")

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration_s, 1),
        "topic": carousel.get("chosen_topic", {}),
        "style": carousel.get("style_preset", ""),
        "slide_count": len(carousel.get("slides", [])),
        "cta": carousel.get("cta_used", {}),
        "images_generated": len(image_paths),
        "drive_links": drive_links,
        "instagram_caption": carousel.get("instagram_caption", ""),
        "linkedin_caption": carousel.get("linkedin_caption", ""),
        "instagram_hashtags": carousel.get("instagram_hashtags", []),
        "linkedin_hashtags": carousel.get("linkedin_hashtags", []),
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    print(f"[main] Run log saved: {log_file}")


def run(dry_run: bool = False, use_test_topics: bool = False):
    """Execute the full daily carousel pipeline."""
    start = datetime.now()
    print(f"\n{'='*60}")
    print(f"Daily Carousel Pipeline -- {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # ── Step 1: Research topics ──────────────────────────────────────────
    if use_test_topics:
        print("[main] Using test topics (--test flag)")
        topics = [
            {"title": "5 AI tools every solopreneur needs in 2026", "source": "test", "description": "Top AI tools for solo founders", "carousel_score": 80},
            {"title": "Claude Code just changed how I build websites", "source": "test", "description": "Developer workflow tips", "carousel_score": 70},
            {"title": "AI agents vs AI chatbots: the real difference", "source": "test", "description": "Comparison post", "carousel_score": 60},
        ]
    else:
        topics = research_topics()

    if not topics:
        msg = "No topics found. Check Brave API key and internet connection."
        print(f"[main] ERROR: {msg}")
        send_slack_error(msg)
        return

    # ── Step 2: Generate content via Claude API ──────────────────────────
    carousel = generate_content(topics)

    if dry_run:
        print("\n[main] DRY RUN -- skipping image generation and Slack")
        print(json.dumps(carousel, indent=2, ensure_ascii=False))
        return

    # ── Step 3: Generate slide images via KIE AI ─────────────────────────
    image_paths, drive_links = generate_images(carousel)

    if not image_paths:
        msg = "All slide image generations failed. Check KIE API key."
        print(f"[main] ERROR: {msg}")
        send_slack_error(msg)
        return

    # ── Step 4: Send to Slack for approval ───────────────────────────────
    send_slack_approval(carousel, image_paths, drive_links)

    # ── Step 5: Log the run ──────────────────────────────────────────────
    duration = (datetime.now() - start).total_seconds()
    _save_run_log(carousel, image_paths, drive_links, duration)

    print(f"\n{'='*60}")
    print(f"Pipeline complete in {duration:.0f}s")
    print(f"  Topic: {carousel.get('chosen_topic', {}).get('title', 'unknown')}")
    print(f"  Slides: {len(image_paths)} images generated")
    print(f"  Slack: notification sent to #marketing-updates")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Carousel Pipeline")
    parser.add_argument("--dry", action="store_true", help="Dry run: research + content only, no images/Slack")
    parser.add_argument("--test", action="store_true", help="Use test topics instead of live research")
    args = parser.parse_args()

    try:
        run(dry_run=args.dry, use_test_topics=args.test)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        print(f"[main] FATAL ERROR:\n{error_msg}")
        try:
            send_slack_error(error_msg)
        except Exception:
            pass
        sys.exit(1)
