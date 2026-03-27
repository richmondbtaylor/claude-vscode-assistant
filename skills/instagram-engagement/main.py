"""
Instagram Engagement Automation — Main Orchestrator

Usage:
  python main.py --account main_account --focus "#AIautomation" --duration 60
  python main.py --account main_account --unfollow-only
  python main.py --account main_account --stats
  python main.py --account main_account --focus "#AIeducation" --duration 30 --dry-run
"""

import argparse
import logging
import random
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

import engagement_tracker as tracker
from comment_generator import generate_comment
from config import (
    get_credentials,
    ACTION_DELAY_RANGE,
    HOURLY_BREAK_RANGE,
    COMMENT_COOLDOWN_DAYS,
    POSTS_TO_LIKE,
    RATE_LIMITS_DAILY,
    RATE_LIMITS_HOURLY,
    COMPETITOR_ACCOUNTS,
    LIKE_PROBABILITY,
    COMMENT_PROBABILITY,
    FOLLOW_PROBABILITY,
    LIKES_PER_TARGET_RANGE,
)
from instagram_session import InstagramSession, LoginChallengeError, RateLimitError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session counters
# ---------------------------------------------------------------------------

class SessionStats:
    def __init__(self):
        self.followed = 0
        self.commented = 0
        self.liked = 0
        self.unfollowed = 0
        self.skipped = 0
        self.errors = 0
        self.start_time = datetime.utcnow()

    def elapsed_minutes(self) -> float:
        return (datetime.utcnow() - self.start_time).total_seconds() / 60


# ---------------------------------------------------------------------------
# Rate limit check wrapper
# ---------------------------------------------------------------------------

def can_act(account: str, action: str) -> bool:
    return tracker.check_rate_limit(account, action)


def do_action(account: str, action: str):
    tracker.record_action(account, action)


# ---------------------------------------------------------------------------
# Unfollow pass
# ---------------------------------------------------------------------------

def run_unfollow_pass(session: InstagramSession, account: str, stats: SessionStats, dry_run: bool):
    candidates = tracker.get_unfollow_candidates(account)
    logger.info(f"[{account}] Unfollow candidates: {len(candidates)}")
    for username in candidates:
        if not can_act(account, "follows"):
            logger.info(f"[{account}] Daily unfollow limit reached — stopping")
            break
        try:
            success = session.unfollow_user(username)
            if success:
                if not dry_run:
                    tracker.record_unfollow(account, username)
                    do_action(account, "unfollows")
                stats.unfollowed += 1
            _human_delay()
        except Exception as e:
            logger.error(f"Unfollow error for @{username}: {e}")
            stats.errors += 1


def _human_delay():
    time.sleep(random.uniform(*ACTION_DELAY_RANGE))


# ---------------------------------------------------------------------------
# Engagement loop
# ---------------------------------------------------------------------------

def engage_with_target(
    session: InstagramSession,
    account: str,
    username: str,
    stats: SessionStats,
    dry_run: bool,
):
    """Run the full engagement sequence for a single target account."""
    logger.info(f"[{account}] Engaging with @{username}")

    profile = session.get_profile_info(username)
    if not session.passes_filter(profile):
        stats.skipped += 1
        return

    # Already following → skip follow (but still process likes/comments normally)
    already_following = tracker.already_following(account, username)
    recently_commented = tracker.commented_recently(account, username, COMMENT_COOLDOWN_DAYS)
    recent_enough = session.is_recent_enough_for_comment(profile)

    # Decide what actions to take — randomized so the pattern isn't robotic
    should_like = random.random() < LIKE_PROBABILITY
    should_comment = (
        not recently_commented
        and recent_enough
        and random.random() < COMMENT_PROBABILITY
    )
    should_follow = (
        not already_following
        and recent_enough
        and random.random() < FOLLOW_PROBABILITY
    )

    # --- Like 1–3 recent posts (count randomized per target) ---
    num_to_like = random.randint(*LIKES_PER_TARGET_RANGE)
    post_links = session._get_recent_post_links(f"https://www.instagram.com/{username}/", count=num_to_like + 1)

    liked_any = False
    most_recent_post_url = post_links[0] if post_links else ""
    most_recent_caption = ""

    if should_like:
        for post_url in post_links[:num_to_like]:
            if not can_act(account, "likes"):
                logger.info(f"[{account}] Like limit reached")
                break
            success = session.like_post(post_url)
            if success:
                if not dry_run:
                    tracker.record_like(account, username, post_url)
                    do_action(account, "likes")
                stats.liked += 1
                liked_any = True
            _human_delay()

    # --- Comment on most recent post ---
    if should_comment and most_recent_post_url and can_act(account, "comments"):
        # Get caption for the most recent post
        _, most_recent_caption = session.get_recent_post_with_caption(username)
        comment_text = generate_comment(username, most_recent_caption)
        success = session.comment_on_post(most_recent_post_url, comment_text)
        if success:
            if not dry_run:
                tracker.record_comment(account, username, most_recent_post_url, comment_text)
                do_action(account, "comments")
            stats.commented += 1
        _human_delay()

    # --- Follow ---
    if should_follow and can_act(account, "follows"):
        success = session.follow_user(username)
        if success:
            if not dry_run:
                tracker.record_follow(account, username)
                do_action(account, "follows")
            stats.followed += 1
        _human_delay()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_session(account: str, focus: str, duration_minutes: int, dry_run: bool):
    creds = get_credentials(account)
    stats = SessionStats()
    session = InstagramSession(account, creds["username"], creds["password"], dry_run=dry_run)

    logger.info(f"Starting session — account: {account}, focus: {focus}, duration: {duration_minutes}min")
    if dry_run:
        logger.info("DRY RUN — no actions will be taken")

    try:
        session.start()
    except LoginChallengeError as e:
        logger.error(str(e))
        print(f"\n⚠️  LOGIN CHALLENGE DETECTED for @{creds['username']}")
        print("Please open Instagram in your browser and complete the verification,")
        print("then run the session again.")
        return

    last_break_time = time.time()

    try:
        # Collect targets
        targets = []
        try:
            targets = session.get_hashtag_targets(focus, max_accounts=80)
        except Exception as e:
            logger.error(f"Hashtag search failed: {e}")
            stats.errors += 1

        # Optionally add competitor followers
        for competitor in COMPETITOR_ACCOUNTS:
            try:
                extra = session.get_competitor_followers(competitor, max_accounts=30)
                targets.extend(extra)
            except Exception as e:
                logger.warning(f"Competitor follower scrape failed (@{competitor}): {e}")

        # Deduplicate
        seen = set()
        unique_targets = []
        for t in targets:
            if t and t.lower() not in seen:
                seen.add(t.lower())
                unique_targets.append(t)

        random.shuffle(unique_targets)
        logger.info(f"[{account}] Total unique targets: {len(unique_targets)}")

        for username in unique_targets:
            # Check session time limit
            if stats.elapsed_minutes() >= duration_minutes:
                logger.info(f"[{account}] Duration limit reached ({duration_minutes}min)")
                break

            # Check daily limits — stop if all daily limits are maxed out
            daily = tracker.get_daily_stats(account)
            if (daily["follows"] >= RATE_LIMITS_DAILY["follows"] and
                    daily["comments"] >= RATE_LIMITS_DAILY["comments"] and
                    daily["likes"] >= RATE_LIMITS_DAILY["likes"]):
                logger.info(f"[{account}] All daily limits reached — stopping")
                break

            # Hourly break
            if time.time() - last_break_time >= 3600:
                break_secs = random.randint(*HOURLY_BREAK_RANGE)
                logger.info(f"[{account}] Taking hourly break ({break_secs // 60}min)")
                time.sleep(break_secs)
                last_break_time = time.time()

            try:
                engage_with_target(session, account, username, stats, dry_run)
            except RateLimitError as e:
                logger.warning(str(e))
                stats.errors += 1
                logger.info("Pausing 10 minutes after rate limit signal...")
                time.sleep(600)
            except Exception as e:
                logger.error(f"Unexpected error for @{username}: {e}")
                stats.errors += 1

        # Unfollow pass at end of session
        run_unfollow_pass(session, account, stats, dry_run)

    except LoginChallengeError as e:
        logger.error(str(e))
        print(f"\n⚠️  LOGIN CHALLENGE mid-session for @{creds['username']}. Stopping.")
    finally:
        session.stop()

    _print_report(account, focus, duration_minutes, stats)


def run_unfollow_only(account: str, dry_run: bool):
    creds = get_credentials(account)
    stats = SessionStats()
    session = InstagramSession(account, creds["username"], creds["password"], dry_run=dry_run)
    try:
        session.start()
        run_unfollow_pass(session, account, stats, dry_run)
    except LoginChallengeError as e:
        logger.error(str(e))
    finally:
        session.stop()
    logger.info(f"Unfollow pass complete. Unfollowed: {stats.unfollowed}")


def show_stats(account: str):
    daily = tracker.get_daily_stats(account)
    print(f"\nToday's stats for {account}:")
    print(f"  Follows   : {daily['follows']}/{RATE_LIMITS_DAILY['follows']}")
    print(f"  Comments  : {daily['comments']}/{RATE_LIMITS_DAILY['comments']}")
    print(f"  Likes     : {daily['liked']}/{RATE_LIMITS_DAILY['likes']}")


def _print_report(account: str, focus: str, duration_minutes: int, stats: SessionStats):
    daily = tracker.get_daily_stats(account)
    elapsed = int(stats.elapsed_minutes())
    print("\n" + "=" * 40)
    print("  Instagram Engagement Session Report")
    print("=" * 40)
    print(f"Account      : {account}")
    print(f"Focus        : {focus}")
    print(f"Duration     : {elapsed} minutes")
    print("-" * 40)
    print(f"Followed     : {stats.followed} accounts")
    print(f"Commented    : {stats.commented} posts")
    print(f"Liked        : {stats.liked} posts")
    print(f"Unfollowed   : {stats.unfollowed} accounts")
    print(f"Skipped      : {stats.skipped} accounts (filtered out)")
    print(f"Errors       : {stats.errors}")
    print("-" * 40)
    print(f"Daily totals : {daily['follows']}/{RATE_LIMITS_DAILY['follows']} follows | "
          f"{daily['comments']}/{RATE_LIMITS_DAILY['comments']} comments | "
          f"{daily['likes']}/{RATE_LIMITS_DAILY['likes']} likes")
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram Engagement Automation")
    parser.add_argument("--account", required=True, help="Account key from .env (e.g. main_account)")
    parser.add_argument("--focus", default=None, help="Hashtag to target (e.g. '#AIautomation')")
    parser.add_argument("--duration", type=int, default=60, help="Session duration in minutes")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no actions taken")
    parser.add_argument("--unfollow-only", action="store_true", help="Only run unfollow pass")
    parser.add_argument("--stats", action="store_true", help="Show today's usage stats and exit")
    args = parser.parse_args()

    tracker.init_db()

    if args.stats:
        show_stats(args.account)
    elif args.unfollow_only:
        run_unfollow_only(args.account, dry_run=args.dry_run)
    else:
        if not args.focus:
            parser.error("--focus is required unless using --unfollow-only or --stats")
        run_session(args.account, args.focus, args.duration, dry_run=args.dry_run)
