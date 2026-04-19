"""
Radley Lead Finder Agent — Main orchestrator.

Run:  python main.py                # Run all sources continuously
      python main.py --once         # Single pass then exit
      python main.py --reddit-only  # Reddit only
      python main.py --web-only     # Web search only
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

load_dotenv("C:/Users/docch/.claude/security/.env")

import analyzer
import brave_monitor
import facebook_monitor
import linkedin_monitor
import notifier
import reddit_monitor
import storage
import twitter_monitor
import web_monitor
from config import REDDIT_POLL_INTERVAL_MINUTES, WEB_POLL_INTERVAL_HOURS, MAX_LEADS_PER_RUN


_MAX_POST_AGE = timedelta(days=1)
_leads_logged = 0


class LeadCapReached(Exception):
    """Raised when MAX_LEADS_PER_RUN qualified leads have been logged."""
    pass


def _is_too_old(post: analyzer.RawPost) -> bool:
    if post.published_at is None:
        return False
    return (datetime.now(timezone.utc) - post.published_at) > _MAX_POST_AGE


def process_post(post: analyzer.RawPost) -> None:
    """Dedup -> Age check -> Analyze -> Notify -> Store."""

    if storage.is_seen(post.id, post.platform):
        return

    if _is_too_old(post):
        age_days = (datetime.now(timezone.utc) - post.published_at).days
        print(f"  [SKIP] Too old ({age_days}d) — [{post.platform}] {post.title[:60]}...")
        storage.mark_seen(post.id, post.platform)
        return

    storage.mark_seen(post.id, post.platform)

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
        f"Intent Score: {analysis.intent_score}/100 | "
        f"Intent: {analysis.intent_type} | "
        f"Contact: {'Yes' if analysis.should_contact else 'No'}"
    )

    global _leads_logged
    logged = notifier.log_to_sheets(post, analysis, cross_platform=cross_platform)
    notifier.send_slack_alert(post, analysis)

    if logged:
        _leads_logged += 1
        print(f"  [LEAD {_leads_logged}/{MAX_LEADS_PER_RUN}] Logged to Google Sheets")
        if _leads_logged >= MAX_LEADS_PER_RUN:
            raise LeadCapReached(f"Reached {MAX_LEADS_PER_RUN} qualified leads")

    storage.save_analysis(
        post.id,
        post.platform,
        post.author,
        analysis.relevance_score,
        analysis.intent_type,
        analysis.should_contact,
    )


def _reset_lead_counter() -> None:
    global _leads_logged
    _leads_logged = 0


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

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FACEBOOK GROUPS MONITOR")
    try:
        for post in facebook_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Facebook cycle error: {e}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TWITTER / X MONITOR")
    try:
        for post in twitter_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Twitter cycle error: {e}")

    notifier.flush_slack_buffer()
    _print_stats()


def _print_stats() -> None:
    stats = storage.get_stats()
    print(f"\n[stats] Total seen: {stats['total_seen']} | "
          f"Analyzed: {stats['total_analyzed']} | "
          f"Should contact: {stats['should_contact']}")


def parse_args():
    parser = argparse.ArgumentParser(description="Radley Lead Finder Agent")
    parser.add_argument("--once", action="store_true",
                        help="Run a single pass then exit")
    parser.add_argument("--reddit-only", action="store_true",
                        help="Run Reddit only")
    parser.add_argument("--web-only", action="store_true",
                        help="Run web search only")
    return parser.parse_args()


def main():
    args = parse_args()

    print("==========================================")
    print("     Radley Lead Finder Agent v1.0")
    print("     radley.tax — R&D Tax Credits")
    print("==========================================")

    storage.init_db()
    print("[main] Database initialized")

    run_reddit = not args.web_only
    run_web    = not args.reddit_only

    if args.once:
        print(f"[main] Running single pass (--once mode) — max {MAX_LEADS_PER_RUN} leads at 70+ score")
        try:
            if run_reddit:
                run_reddit_cycle()
            if run_web:
                run_web_cycle()
        except LeadCapReached:
            print(f"\n[main] Lead cap reached — {_leads_logged} qualified leads logged to Google Sheets.")
        notifier.flush_slack_buffer()
        _print_stats()
        print(f"\n[main] Single pass complete. {_leads_logged} leads logged. Exiting.")
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
