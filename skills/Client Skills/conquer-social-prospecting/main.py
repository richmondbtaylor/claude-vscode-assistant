"""
Conquer.io Social Prospecting Agent — Main orchestrator.

Run:  python main.py                # Run all sources continuously
      python main.py --once         # Single pass then exit
      python main.py --reddit-only  # Reddit only (r/sales, r/salesforce, r/salesops — competitor keywords)
      python main.py --g2-only      # G2 competitor reviews only (best lead quality)
      python setup_sheets.py        # Authorize Google Sheets (run once first)

Lead sources:
  - G2 reviews: 1–3 star reviews of Outreach, Salesloft, Gong, RingDNA, Dialpad
    → Direct review URLs, verified enterprise users, explicit pain signal
  - Reddit: competitor-specific keyword search in sales/salesforce/salesops/RevOps
    → Real discussions, but noisier than G2
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
import g2_monitor
import notifier
import reddit_monitor
import storage
from config import G2_POLL_INTERVAL_HOURS, REDDIT_POLL_INTERVAL_MINUTES


_MAX_POST_AGE_REDDIT  = timedelta(days=30)    # Hard cap: past month only
_MAX_POST_AGE_REVIEWS = timedelta(days=30)    # Hard cap: past month only


def _is_too_old(post: analyzer.RawPost) -> bool:
    # Posts with no date from social/web platforms cannot be verified as fresh — reject them.
    # G2/TrustRadius listing pages are stable URLs with no date; allow them through (Brave freshness=pm handles it).
    if post.published_at is None:
        return post.platform not in ("g2", "trustradius")
    max_age = _MAX_POST_AGE_REVIEWS if post.platform in ("g2", "trustradius") else _MAX_POST_AGE_REDDIT
    return (datetime.now(timezone.utc) - post.published_at) > max_age


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

    print(f"  >> Analyzing [{post.platform}] {post.title[:70]}...")

    analysis = analyzer.analyze(post)
    if analysis is None:
        print(f"  [FAIL] Analysis failed for {post.id}")
        return

    # Hard age gate: reject posts Claude determined are older than 30 days
    if analysis.post_age_days > 30:
        print(f"  [SKIP] Too old per content ({analysis.post_age_days}d) — [{post.platform}] {post.title[:60]}...")
        return

    tier_icon = {"High": "🔥", "Medium": "⭐", "Low": "📌"}.get(analysis.score_tier, "")
    print(
        f"  [OK] Score: {analysis.intent_score}/100 | "
        f"Tier: {tier_icon} {analysis.score_tier} | "
        f"Category: {analysis.pain_category} | "
        f"Contact: {'Yes' if analysis.should_contact else 'No'} | "
        f"GDPR: {'⚠️ YES' if analysis.gdpr_flag else 'No'}"
    )

    notifier.log_to_sheets(post, analysis)
    notifier.send_slack_alert(post, analysis)

    storage.save_analysis(
        post.id,
        post.platform,
        post.author,
        analysis.intent_score,
        analysis.pain_category,
        analysis.should_contact,
        analysis.company_name,
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
    notifier.flush_slack_buffer()
    _print_stats()


def run_g2_cycle() -> None:
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] G2 REVIEW CYCLE (Outreach / Salesloft / Gong / RingDNA / Dialpad)")
    print(f"{'='*60}")
    try:
        for post in g2_monitor.poll():
            process_post(post)
    except Exception as e:
        print(f"[main] G2 cycle error: {e}")
    notifier.flush_slack_buffer()
    _print_stats()


def _print_stats() -> None:
    stats = storage.get_stats()
    print(
        f"\n[stats] Total seen: {stats['total_seen']} | "
        f"Analyzed: {stats['total_analyzed']} | "
        f"Should contact: {stats['should_contact']}"
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Conquer.io Social Prospecting Agent")
    parser.add_argument("--once", action="store_true",
                        help="Run a single pass then exit")
    parser.add_argument("--reddit-only", action="store_true",
                        help="Reddit only (competitor keywords in sales/salesforce/salesops/RevOps)")
    parser.add_argument("--g2-only", action="store_true",
                        help="G2 reviews only (best lead quality — direct review URLs)")
    return parser.parse_args()


def main():
    args = parse_args()

    print("==========================================")
    print("  Conquer.io Social Prospecting Agent")
    print("==========================================")

    storage.init_db()
    print("[main] Database initialized")

    run_reddit = not args.g2_only
    run_g2     = not args.reddit_only

    if args.once:
        print("[main] Running single pass (--once mode)")
        if run_g2:
            run_g2_cycle()
        if run_reddit:
            run_reddit_cycle()
        notifier.flush_slack_buffer()
        print("\n[main] Single pass complete. Exiting.")
        sys.exit(0)

    # Continuous mode
    sources = []
    if run_g2:
        sources.append(f"G2 reviews every {G2_POLL_INTERVAL_HOURS}h")
    if run_reddit:
        sources.append(f"Reddit every {REDDIT_POLL_INTERVAL_MINUTES} min")
    print(f"[main] Monitoring: {' | '.join(sources)}\n")

    if run_g2:
        run_g2_cycle()
    if run_reddit:
        run_reddit_cycle()

    if run_g2:
        schedule.every(G2_POLL_INTERVAL_HOURS).hours.do(run_g2_cycle)
    if run_reddit:
        schedule.every(REDDIT_POLL_INTERVAL_MINUTES).minutes.do(run_reddit_cycle)

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
