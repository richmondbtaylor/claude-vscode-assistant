# main.py — HubSpot SMB Lead Research Agent

"""
HubSpot SMB Lead Research Agent — Main orchestrator.

Run:  python main.py --once         # Single pass then exit
      python main.py --once --reddit-only
      python main.py --once --web-only
"""

import argparse
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timedelta, timezone
from pathlib import Path

import schedule
from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude" / "security" / "hubspot-smb-agent.env")

import analyzer
import brave_monitor
import linkedin_monitor
import notifier
import reddit_monitor
import storage
import twitter_monitor
import web_monitor
from config import REDDIT_POLL_INTERVAL_MINUTES, WEB_POLL_INTERVAL_HOURS


_MAX_POST_AGE = timedelta(days=7)

_REDDIT_CRM_SIGNAL_TERMS = [
    "crm", "switching crm", "replacing crm", "crm recommendation", "crm alternative",
    "salesforce", "zoho", "pipedrive", "monday crm", "copper crm", "keap",
    "activecampaign", "freshsales", "insightly", "streak crm", "close crm",
    "crm too expensive", "crm too complex", "leaving salesforce", "salesforce alternative",
    "outgrown crm", "crm adoption", "team not using crm", "what crm", "best crm",
    "crm for small business", "crm for startup", "crm migration", "switching from salesforce",
]

_REDDIT_HUBSPOT_TERMS = ["hubspot", "hub spot", "marketing hub", "sales hub", "service hub"]


def _is_too_old(post: analyzer.RawPost) -> bool:
    if post.published_at is None:
        return False
    return (datetime.now(timezone.utc) - post.published_at) > _MAX_POST_AGE


def _reddit_has_signal(post: analyzer.RawPost) -> bool:
    if post.platform != "reddit":
        return True
    text = (post.title + " " + post.body).lower()
    # Skip posts that are primarily about using HubSpot (already a customer)
    hubspot_count = sum(1 for term in _REDDIT_HUBSPOT_TERMS if term in text)
    crm_signal_count = sum(1 for term in _REDDIT_CRM_SIGNAL_TERMS if term in text)
    if hubspot_count > 0 and crm_signal_count == 0:
        return False  # HubSpot user asking a HubSpot question, not a prospect
    return crm_signal_count > 0


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
        return

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
        analysis.intent_type,
        analysis.should_contact,
    )


def run_reddit_cycle():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] REDDIT CYCLE")
    storage.init_db()
    try:
        for post in reddit_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Reddit cycle error: {e}")
    notifier.flush_slack_buffer()


def run_web_cycle():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WEB CYCLE")
    storage.init_db()

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] BRAVE/WEB MONITOR")
    try:
        for post in brave_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Brave/web cycle error: {e}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] LINKEDIN MONITOR")
    try:
        for post in linkedin_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] LinkedIn cycle error: {e}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TWITTER/X MONITOR")
    try:
        for post in twitter_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] Twitter cycle error: {e}")

    notifier.flush_slack_buffer()


def main():
    parser = argparse.ArgumentParser(description="HubSpot SMB Lead Research Agent")
    parser.add_argument("--once", action="store_true", help="Run one full pass then exit")
    parser.add_argument("--reddit-only", action="store_true", help="Reddit only")
    parser.add_argument("--web-only", action="store_true", help="Web/LinkedIn/social only")
    args = parser.parse_args()

    storage.init_db()

    if args.once:
        if args.reddit_only:
            run_reddit_cycle()
        elif args.web_only:
            run_web_cycle()
        else:
            run_reddit_cycle()
            run_web_cycle()
        return

    schedule.every(REDDIT_POLL_INTERVAL_MINUTES).minutes.do(run_reddit_cycle)
    schedule.every(WEB_POLL_INTERVAL_HOURS).hours.do(run_web_cycle)

    run_reddit_cycle()
    run_web_cycle()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
