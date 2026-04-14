"""
BrainCX Social Listening Lead Finder — Main orchestrator.

Run:  python main.py                # Run all sources continuously
      python main.py --once         # Single pass then exit (testing)
      python main.py --reddit-only  # Reddit only
      python main.py --web-only     # LinkedIn/Quora/Twitter/web only
      python setup_sheets.py        # Authorize Google Sheets (run once first)
"""

import argparse
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timedelta, timezone

import schedule
from dotenv import load_dotenv

load_dotenv()

import analyzer
import brave_monitor
import facebook_monitor
import job_board_monitor
import linkedin_monitor
import notifier
import reddit_monitor
import storage
import twitter_monitor
import web_monitor
from config import REDDIT_POLL_INTERVAL_MINUTES, WEB_POLL_INTERVAL_HOURS


_MAX_POST_AGE = timedelta(days=7)

# Job board / web posts get through regardless — they're already targeted.
# Reddit posts must contain at least one relevant keyword or they're skipped
# without spending a Claude call on them.
_REDDIT_SIGNAL_KEYWORDS = [
    "receptionist", "front desk", "answering service", "virtual receptionist",
    "ai receptionist", "voice ai", "ivr", "after hours", "after-hours",
    "call volume", "missing calls", "multilingual", "bilingual",
    "scheduling", "intake", "patient calls", "client calls",
    "overwhelmed", "can't keep up", "understaffed", "staffing",
    "hvac", "plumbing", "dental", "medical", "clinic", "law firm",
    "attorney", "immigration", "chiropractic", "veterinary", "vet ",
]


def _is_too_old(post: analyzer.RawPost) -> bool:
    if post.published_at is None:
        return False
    return (datetime.now(timezone.utc) - post.published_at) > _MAX_POST_AGE


def _reddit_has_signal(post: analyzer.RawPost) -> bool:
    """Quick keyword pre-filter for Reddit posts to avoid wasting Claude calls."""
    if post.platform != "reddit":
        return True  # non-Reddit posts always pass
    text = (post.title + " " + post.body).lower()
    return any(kw in text for kw in _REDDIT_SIGNAL_KEYWORDS)


def process_post(post: analyzer.RawPost) -> None:
    if storage.is_seen(post.id, post.platform):
        return

    if _is_too_old(post):
        age_days = (datetime.now(timezone.utc) - post.published_at).days
        print(f"  [SKIP] Too old ({age_days}d) — [{post.platform}] {post.title[:60]}...")
        storage.mark_seen(post.id, post.platform)
        return

    storage.mark_seen(post.id, post.platform)

    if not _reddit_has_signal(post):
        return  # skip silently — no relevant keywords

    other_platforms = storage.get_author_platforms(post.author, post.platform)
    cross_platform = ", ".join(other_platforms) if other_platforms else ""
    if cross_platform:
        print(f"  [CROSS] Author '{post.author}' also seen on: {cross_platform}")

    print(f"  >> Analyzing [{post.platform}] {post.title[:70]}...")

    analysis = analyzer.analyze(post)
    if analysis is None:
        print(f"  [FAIL] Analysis failed for {post.id}")
        return

    print(
        f"  [OK] Score: {analysis.relevance_score}/100 | "
        f"ICP: {analysis.icp_category} | "
        f"Lead: {analysis.lead_score} | "
        f"Contact: {'Yes' if analysis.should_contact else 'No'}"
    )

    notifier.log_to_sheets(post, analysis, cross_platform=cross_platform)
    notifier.send_slack_alert(post, analysis)

    storage.save_analysis(
        post.id,
        post.platform,
        post.author,
        analysis.relevance_score,
        analysis.icp_category,
        analysis.should_contact,
    )


def run_reddit_cycle() -> None:
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] REDDIT POLL CYCLE")
    print(f"{'='*60}")
    try:
        for post in reddit_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Reddit cycle error: {e}")
    _print_stats()


def run_web_cycle() -> None:
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WEB POLL CYCLE")
    print(f"{'='*60}")
    try:
        for post in brave_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Web cycle error: {e}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] LINKEDIN MONITOR")
    try:
        for post in linkedin_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] LinkedIn cycle error: {e}")

    # Facebook Groups — requires saved Playwright session in .browser_sessions/
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FACEBOOK GROUPS")
    try:
        for post in facebook_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Facebook cycle error: {e}")

    # Twitter permanently disabled — X bot detection blocks headless Playwright
    # Brave web queries with site:x.com catch Twitter posts anyway

    # Job boards — businesses actively HIRING receptionists = hottest leads
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] JOB BOARDS (Indeed + LinkedIn Jobs)")
    try:
        for post in job_board_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Job board cycle error: {e}")

    notifier.flush_slack_buffer()
    _print_stats()


def _print_stats() -> None:
    stats = storage.get_stats()
    print(f"\n[stats] Total seen: {stats['total_seen']} | "
          f"Analyzed: {stats['total_analyzed']} | "
          f"Should contact: {stats['should_contact']}")


def parse_args():
    parser = argparse.ArgumentParser(description="BrainCX Social Listening Lead Finder")
    parser.add_argument("--once", action="store_true", help="Run a single pass then exit")
    parser.add_argument("--reddit-only", action="store_true", help="Run Reddit only")
    parser.add_argument("--web-only", action="store_true", help="Run web search only")
    return parser.parse_args()


def main():
    args = parse_args()

    print("==========================================")
    print("   BrainCX Social Listening Lead Finder")
    print("==========================================")

    storage.init_db()
    print("[main] Database initialized")

    run_reddit = not args.web_only
    run_web    = not args.reddit_only

    if args.once:
        print("[main] Running single pass (--once mode)")
        if run_reddit:
            run_reddit_cycle()
        if run_web:
            run_web_cycle()
        notifier.flush_slack_buffer()
        print("\n[main] Single pass complete. Exiting.")
        sys.exit(0)

    sources = []
    if run_reddit:
        sources.append(f"Reddit every {REDDIT_POLL_INTERVAL_MINUTES} min")
    if run_web:
        sources.append(f"Web every {WEB_POLL_INTERVAL_HOURS}h")
    print(f"[main] Monitoring: {' | '.join(sources)}\n")

    if run_reddit:
        run_reddit_cycle()
    if run_web:
        run_web_cycle()

    if run_reddit:
        schedule.every(REDDIT_POLL_INTERVAL_MINUTES).minutes.do(run_reddit_cycle)
    if run_web:
        schedule.every(WEB_POLL_INTERVAL_HOURS).hours.do(run_web_cycle)

    print(f"\n[main] Scheduler running. Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[main] Shutting down.")
        _print_stats()
        sys.exit(0)


if __name__ == "__main__":
    main()
