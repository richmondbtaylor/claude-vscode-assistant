"""
Instagram Engagement Automation -- Main Orchestrator (RISEN Framework)

Usage:
  python main.py --account main_account --focus "#AIautomation" --duration 120
  python main.py --account main_account --unfollow-only
  python main.py --account main_account --stats
  python main.py --account main_account --focus "#AIeducation" --duration 60 --dry-run

Session model (RISEN):
  --duration is the total wall-clock time budget (minutes).
  The bot runs 20-25 min active blocks separated by 30-90 min inter-session
  breaks, cycling until the budget is exhausted.
"""

import argparse
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

import engagement_tracker as tracker
from comment_generator import generate_comment
import sheets_reporter
from config import (
    get_credentials,
    get_ramp_up_limits,
    ACTION_DELAY_RANGE,
    INTER_SESSION_DELAY_RANGE,
    SESSION_ACTIVE_DURATION_RANGE,
    BLACKOUT_START,
    BLACKOUT_END,
    COMMENT_COOLDOWN_DAYS,
    POSTS_TO_LIKE,
    RATE_LIMITS_DAILY,
    COMPETITOR_ACCOUNTS,
    AUTHORITY_ACCOUNTS,
    LIKE_PROBABILITY,
    AUTHORITY_LIKE_PROBABILITY,
    COMMENT_PROBABILITY,
    FOLLOW_PROBABILITY,
    LIKES_PER_TARGET_RANGE,
    REENGAGE_CADENCE_DAYS,
)
from instagram_session import InstagramSession, LoginChallengeError, RateLimitError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RISEN: Alert system
# ---------------------------------------------------------------------------

def send_alert(account: str, trigger: str, daily_stats: dict, recommended_action: str):
    """High-priority alert to human operator. Extend to add email/Slack as needed."""
    border = "=" * 60
    print(f"\n{border}")
    print("  [!] RISEN ALERT -- HUMAN OPERATOR ACTION REQUIRED")
    print(border)
    print(f"  Account    : {account}")
    print(f"  Trigger    : {trigger}")
    print(f"  Timestamp  : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Daily stats: follows={daily_stats.get('follows',0)} | "
          f"comments={daily_stats.get('comments',0)} | "
          f"likes={daily_stats.get('likes',0)}")
    print(f"  Action     : {recommended_action}")
    print(f"{border}\n")
    logger.error(f"[{account}] RISEN ALERT -- {trigger}")


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
# RISEN: Blackout check
# ---------------------------------------------------------------------------

def is_blackout_time() -> bool:
    """Return True if current local time falls within the daily blackout window."""
    now = datetime.now()
    current_mins = now.hour * 60 + now.minute
    start_mins = BLACKOUT_START[0] * 60 + BLACKOUT_START[1]
    end_mins = BLACKOUT_END[0] * 60 + BLACKOUT_END[1]
    if start_mins <= end_mins:
        return start_mins <= current_mins < end_mins
    else:  # wraps midnight
        return current_mins >= start_mins or current_mins < end_mins


def wait_for_blackout_end():
    end_h, end_m = BLACKOUT_END
    now = datetime.now()
    wake = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if wake <= now:
        wake += timedelta(days=1)
    wait_secs = (wake - now).total_seconds()
    logger.info(f"RISEN BLACKOUT: sleeping {wait_secs/60:.0f}min until {wake.strftime('%H:%M')}")
    time.sleep(wait_secs)


# ---------------------------------------------------------------------------
# Rate limit helpers (ramp-up aware)
# ---------------------------------------------------------------------------

def can_act(account: str, action: str, ramp_limits: dict) -> bool:
    multiplier = tracker.get_limit_multiplier(account)
    ramp_daily = int(ramp_limits.get(action, 9999) * multiplier)
    daily = tracker.get_daily_stats(account)
    if daily.get(action, 0) >= ramp_daily:
        day = ramp_limits.get("_day", "?")
        logger.info(f"[{account}] Daily {action} limit reached ({ramp_daily}, ramp day {day})")
        return False
    return tracker.check_rate_limit(account, action)


def do_action(account: str, action: str):
    tracker.record_action(account, action)


def _human_delay():
    time.sleep(random.uniform(*ACTION_DELAY_RANGE))


# ---------------------------------------------------------------------------
# Unfollow pass
# ---------------------------------------------------------------------------

def run_unfollow_pass(session: InstagramSession, account: str, stats: SessionStats,
                      dry_run: bool, ramp_limits: dict):
    candidates = tracker.get_unfollow_candidates(account)
    logger.info(f"[{account}] Unfollow candidates: {len(candidates)}")
    for username in candidates:
        if not can_act(account, "follows", ramp_limits):
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


# ---------------------------------------------------------------------------
# RISEN: Engagement sequence for one target
# ---------------------------------------------------------------------------

def engage_with_target(
    session: InstagramSession,
    account: str,
    username: str,
    stats: SessionStats,
    dry_run: bool,
    ramp_limits: dict,
    is_authority: bool = False,
    skip_filter: bool = False,
):
    """Run the full engagement sequence for a single target account."""
    logger.info(f"[{account}] Engaging @{username} (authority={is_authority}, reengage={skip_filter})")

    profile = session.get_profile_info(username)
    if not skip_filter and not session.passes_filter(profile):
        stats.skipped += 1
        return

    already_following = tracker.already_following(account, username)
    recently_commented = tracker.commented_recently(account, username, COMMENT_COOLDOWN_DAYS)
    recent_enough = session.is_recent_enough_for_comment(profile)

    # Authority targets: only like 60% of posts (RISEN rule)
    like_prob = AUTHORITY_LIKE_PROBABILITY if is_authority else LIKE_PROBABILITY
    should_like = random.random() < like_prob
    should_comment = (
        not recently_commented
        and recent_enough
        and random.random() < COMMENT_PROBABILITY
    )
    should_follow = (
        not already_following
        and random.random() < FOLLOW_PROBABILITY
    )

    logger.info(
        f"[{account}] @{username} decisions: like={should_like} comment={should_comment} "
        f"follow={should_follow} (already_following={already_following}, "
        f"recently_commented={recently_commented}, recent_enough={recent_enough})"
    )

    num_to_like = random.randint(*LIKES_PER_TARGET_RANGE)
    post_links = session._get_recent_post_links(
        f"https://www.instagram.com/{username}/", count=num_to_like + 1
    )
    most_recent_post_url = post_links[0] if post_links else ""

    # --- Like recent posts ---
    if should_like:
        for post_url in post_links[:num_to_like]:
            if not can_act(account, "likes", ramp_limits):
                logger.info(f"[{account}] Like limit reached")
                break
            success = session.like_post(post_url)
            if success:
                if not dry_run:
                    tracker.record_like(account, username, post_url)
                    do_action(account, "likes")
                stats.liked += 1
            _human_delay()

    # --- Comment (with RISEN content filter) ---
    if should_comment and most_recent_post_url and can_act(account, "comments", ramp_limits):
        _, most_recent_caption = session.get_recent_post_with_caption(username)
        if not session.passes_content_filter(most_recent_caption):
            logger.info(f"[{account}] @{username}: content filter blocked comment")
        else:
            comment_text = generate_comment(username, most_recent_caption)
            success = session.comment_on_post(most_recent_post_url, comment_text)
            if success:
                if not dry_run:
                    tracker.record_comment(account, username, most_recent_post_url, comment_text)
                    do_action(account, "comments")
                stats.commented += 1
        _human_delay()

    # --- Follow ---
    if should_follow and can_act(account, "follows", ramp_limits):
        success = session.follow_user(username)
        if success:
            if not dry_run:
                tracker.record_follow(account, username)
                do_action(account, "follows")
            stats.followed += 1
        _human_delay()

    # Update re-engagement timestamp for accounts we're already following
    if skip_filter and not dry_run:
        tracker.update_last_engaged(account, username)


# ---------------------------------------------------------------------------
# RISEN: One active block (20-25 min of engagement)
# ---------------------------------------------------------------------------

def _daily_limits_exhausted(account: str, ramp_limits: dict) -> bool:
    daily = tracker.get_daily_stats(account)
    multiplier = tracker.get_limit_multiplier(account)
    return (
        daily.get("follows", 0)   >= int(ramp_limits["follows"]   * multiplier) and
        daily.get("comments", 0)  >= int(ramp_limits["comments"]  * multiplier) and
        daily.get("likes", 0)     >= int(ramp_limits["likes"]     * multiplier)
    )


def run_active_block(
    session: InstagramSession,
    account: str,
    focus: str,
    stats: SessionStats,
    dry_run: bool,
    ramp_limits: dict,
    block_duration_minutes: float,
):
    """One active engagement block: Authority targets first, then hashtag/community."""
    block_start = time.time()

    def time_up() -> bool:
        return (time.time() - block_start) / 60 >= block_duration_minutes

    # Pre-flight simulation (RISEN anti-detection: browse feed before acting)
    session.preflight_simulation()

    # --- Category A: Authority targets (highest priority) ---
    if AUTHORITY_ACCOUNTS:
        logger.info(f"[{account}] Category A -- {len(AUTHORITY_ACCOUNTS)} authority targets")
        for username in AUTHORITY_ACCOUNTS:
            if time_up() or _daily_limits_exhausted(account, ramp_limits):
                break
            try:
                engage_with_target(session, account, username, stats, dry_run,
                                   ramp_limits, is_authority=True)
            except RateLimitError as e:
                _handle_rate_limit(account, e, stats)
                return
            except Exception as e:
                logger.error(f"Error on authority @{username}: {e}")
                stats.errors += 1

    # --- Category R: Re-engagement pass (followed accounts due for cadence check) ---
    reengage_targets = tracker.get_reengage_candidates(account, REENGAGE_CADENCE_DAYS)
    # Exclude authority accounts (already handled above)
    authority_set = set(a.lower() for a in AUTHORITY_ACCOUNTS)
    reengage_targets = [u for u in reengage_targets if u.lower() not in authority_set]
    if reengage_targets:
        logger.info(f"[{account}] Category R (re-engage) -- {len(reengage_targets)} accounts due")
    for username in reengage_targets:
        if time_up() or _daily_limits_exhausted(account, ramp_limits):
            break
        try:
            engage_with_target(session, account, username, stats, dry_run,
                               ramp_limits, skip_filter=True)
        except RateLimitError as e:
            _handle_rate_limit(account, e, stats)
            return
        except Exception as e:
            logger.error(f"Re-engage error for @{username}: {e}")
            stats.errors += 1

    # --- Category B + C: Hashtag targets and community ---
    targets = []
    if focus:
        try:
            targets = session.get_hashtag_targets(focus, max_accounts=80)
        except Exception as e:
            logger.error(f"Hashtag search failed: {e}")
            stats.errors += 1

    for competitor in COMPETITOR_ACCOUNTS:
        try:
            targets.extend(session.get_competitor_followers(competitor, max_accounts=30))
        except Exception as e:
            logger.warning(f"Competitor follower scrape failed (@{competitor}): {e}")

    # Deduplicate, exclude authority accounts already processed
    seen = set(a.lower() for a in AUTHORITY_ACCOUNTS)
    unique_targets = []
    for t in targets:
        if t and t.lower() not in seen:
            seen.add(t.lower())
            unique_targets.append(t)
    random.shuffle(unique_targets)
    logger.info(f"[{account}] Category B/C -- {len(unique_targets)} targets this block")

    for username in unique_targets:
        if time_up():
            logger.info(f"[{account}] Block time limit reached")
            break
        if _daily_limits_exhausted(account, ramp_limits):
            logger.info(f"[{account}] All daily limits reached")
            break
        try:
            engage_with_target(session, account, username, stats, dry_run, ramp_limits)
        except RateLimitError as e:
            _handle_rate_limit(account, e, stats)
            return
        except Exception as e:
            logger.error(f"Unexpected error for @{username}: {e}")
            stats.errors += 1


def _handle_rate_limit(account: str, error: RateLimitError, stats: SessionStats):
    """RISEN hard-stop protocol on rate limit signals."""
    daily = tracker.get_daily_stats(account)
    error_str = str(error).lower()
    if "try again later" in error_str:
        tracker.set_limit_multiplier(account, 0.5)
        send_alert(
            account,
            trigger="Try again later detected -- permanent 50% limit reduction applied",
            daily_stats=daily,
            recommended_action="Limits permanently halved. Review account health before next session."
        )
    else:
        send_alert(
            account,
            trigger=f"Rate limit / action block: {error}",
            daily_stats=daily,
            recommended_action="Pausing 10 minutes then stopping this session block."
        )
    stats.errors += 1
    logger.info("Pausing 10 minutes after rate limit signal...")
    time.sleep(600)


# ---------------------------------------------------------------------------
# Main session runner (multi-block RISEN architecture)
# ---------------------------------------------------------------------------

def run_session(account: str, focus: str, duration_minutes: int, dry_run: bool):
    """
    Outer runner. Fits as many 20-25 min active blocks as possible within
    duration_minutes, with 30-90 min inter-session breaks between blocks.
    """
    creds = get_credentials(account)
    stats = SessionStats()

    tracker.init_db()
    day_number = tracker.get_account_day_number(account)
    ramp_limits = get_ramp_up_limits(day_number)
    ramp_limits["_day"] = day_number

    logger.info(
        f"RISEN Session -- account={account}, focus={focus}, budget={duration_minutes}min, "
        f"ramp_day={day_number}, limits=follows:{ramp_limits['follows']} "
        f"comments:{ramp_limits['comments']} likes:{ramp_limits['likes']}"
    )
    if dry_run:
        logger.info("DRY RUN -- no actions will be taken")

    session = InstagramSession(account, creds["username"], creds["password"], dry_run=dry_run)
    try:
        session.start()
    except LoginChallengeError as e:
        send_alert(
            account,
            trigger=f"Login challenge at session start: {e}",
            daily_stats=tracker.get_daily_stats(account),
            recommended_action="Complete verification manually in a real browser, then retry."
        )
        return

    wall_start = time.time()

    try:
        block_num = 0
        while True:
            elapsed_total = (time.time() - wall_start) / 60
            if elapsed_total >= duration_minutes:
                logger.info(f"[{account}] Duration budget exhausted ({duration_minutes}min)")
                break

            if is_blackout_time():
                wait_for_blackout_end()
                wall_start = time.time()  # reset budget — don't count blackout sleep
                continue

            block_num += 1
            block_duration = random.uniform(*SESSION_ACTIVE_DURATION_RANGE)
            logger.info(
                f"[{account}] Block #{block_num} starting "
                f"({block_duration:.0f}min active, {elapsed_total:.0f}min elapsed)"
            )

            try:
                run_active_block(session, account, focus, stats, dry_run, ramp_limits, block_duration)
            except LoginChallengeError as e:
                send_alert(
                    account,
                    trigger=f"Login challenge mid-session (block #{block_num}): {e}",
                    daily_stats=tracker.get_daily_stats(account),
                    recommended_action="HARD STOP. Complete verification manually, then retry."
                )
                break

            elapsed_total = (time.time() - wall_start) / 60
            if elapsed_total >= duration_minutes:
                break

            # Inter-session break (30-90 min) -- only if budget remains
            break_secs = random.uniform(*INTER_SESSION_DELAY_RANGE)
            break_mins = break_secs / 60
            if elapsed_total + break_mins >= duration_minutes:
                logger.info(f"[{account}] Not enough budget for another block -- stopping")
                break
            logger.info(f"[{account}] Inter-session break: {break_mins:.0f}min")
            time.sleep(break_secs)

    finally:
        try:
            run_unfollow_pass(session, account, stats, dry_run, ramp_limits)
        except Exception as e:
            logger.warning(f"Unfollow pass error: {e}")
        try:
            session.stop()
        except Exception as e:
            logger.warning(f"Session cleanup error (browser may have crashed): {e}")
        try:
            _print_report(account, focus, duration_minutes, stats, day_number, ramp_limits, dry_run=dry_run)
        except Exception as e:
            logger.error(f"Report generation failed (non-fatal): {e}")


# ---------------------------------------------------------------------------
# Unfollow-only mode
# ---------------------------------------------------------------------------

def run_unfollow_only(account: str, dry_run: bool):
    creds = get_credentials(account)
    stats = SessionStats()
    tracker.init_db()
    day_number = tracker.get_account_day_number(account)
    ramp_limits = get_ramp_up_limits(day_number)
    session = InstagramSession(account, creds["username"], creds["password"], dry_run=dry_run)
    try:
        session.start()
        run_unfollow_pass(session, account, stats, dry_run, ramp_limits)
    except LoginChallengeError as e:
        logger.error(str(e))
    finally:
        try:
            session.stop()
        except Exception:
            pass
    logger.info(f"Unfollow pass complete. Unfollowed: {stats.unfollowed}")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def show_stats(account: str):
    tracker.init_db()
    day_number = tracker.get_account_day_number(account)
    ramp_limits = get_ramp_up_limits(day_number)
    multiplier = tracker.get_limit_multiplier(account)
    daily = tracker.get_daily_stats(account)
    print(f"\nToday's stats for {account} (ramp day {day_number}, multiplier {multiplier:.1f}x):")
    print(f"  Follows   : {daily['follows']}/{int(ramp_limits['follows'] * multiplier)}")
    print(f"  Comments  : {daily['comments']}/{int(ramp_limits['comments'] * multiplier)}")
    print(f"  Likes     : {daily.get('likes', 0)}/{int(ramp_limits['likes'] * multiplier)}")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _print_report(account: str, focus: str, duration_minutes: int, stats: SessionStats,
                  day_number: int, ramp_limits: dict, dry_run: bool = False):
    daily = tracker.get_daily_stats(account)
    multiplier = tracker.get_limit_multiplier(account)
    elapsed = int(stats.elapsed_minutes())
    print("\n" + "=" * 45)
    print("  Instagram Engagement Report (RISEN)")
    print("=" * 45)
    print(f"Account      : {account}")
    print(f"Focus        : {focus}")
    print(f"Duration     : {elapsed} minutes")
    print(f"Ramp day     : {day_number}")
    print("-" * 45)
    print(f"Followed     : {stats.followed} accounts")
    print(f"Commented    : {stats.commented} posts")
    print(f"Liked        : {stats.liked} posts")
    print(f"Unfollowed   : {stats.unfollowed} accounts")
    print(f"Skipped      : {stats.skipped} accounts (filtered)")
    print(f"Errors       : {stats.errors}")
    print("-" * 45)
    print(f"Daily totals : {daily['follows']}/{int(ramp_limits['follows']*multiplier)} follows | "
          f"{daily['comments']}/{int(ramp_limits['comments']*multiplier)} comments | "
          f"{daily.get('likes',0)}/{int(ramp_limits['likes']*multiplier)} likes")
    print("=" * 45)

    spreadsheet_id = os.environ.get("SHEETS_SPREADSHEET_ID")
    tab_name = os.environ.get("SHEETS_TAB_NAME", "Instagram Engagement")
    if spreadsheet_id:
        sheets_reporter.log_session(
            account=account,
            focus=focus or "",
            duration_minutes=elapsed,
            day_number=day_number,
            dry_run=dry_run,
            followed=stats.followed,
            commented=stats.commented,
            liked=stats.liked,
            unfollowed=stats.unfollowed,
            skipped=stats.skipped,
            errors=stats.errors,
            daily_follows=daily["follows"],
            daily_follows_limit=int(ramp_limits["follows"] * multiplier),
            daily_comments=daily["comments"],
            daily_comments_limit=int(ramp_limits["comments"] * multiplier),
            daily_likes=daily.get("likes", 0),
            daily_likes_limit=int(ramp_limits["likes"] * multiplier),
            spreadsheet_id=spreadsheet_id,
            tab_name=tab_name,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram Engagement Automation (RISEN)")
    parser.add_argument("--account", required=True, help="Account key from .env (e.g. main_account)")
    parser.add_argument("--focus", default=None, help="Hashtag to target (e.g. '#AIautomation')")
    parser.add_argument("--duration", type=int, default=120,
                        help="Total time budget in minutes (includes inter-session breaks)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only -- no actions taken")
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
