"""
TARSEN main orchestrator.

Usage:
  python main.py --dry-run          # default - generate + log to sheet, never touches X
  python main.py --live              # actually scrape X and post replies
  python main.py --status            # show today's stats and exit
  python main.py --once              # process exactly one tweet then exit (good for testing)

Default flow per run:
  1. Check kill switch (control!B2)
  2. Check active hours (7am-11pm ET)
  3. Check today's daily cap from warm-up schedule
  4. Pull seed accounts and recent tweets
  5. Filter: not replied today twice, not already replied to this tweet, not political
  6. Pick the highest-priority tweet
  7. Generate reply via Claude
  8. Validate against banlists + word count + URL/hashtag/em-dash checks
  9. Insert into Sheet as 'pending' (week 1) or 'auto' + post (after week 1)
"""
import argparse
import logging
import random
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    ACTIVE_HOURS_START, ACTIVE_HOURS_END, TIMEZONE,
    LIKE_TO_POST_DELAY_SECONDS, MIN_TWEET_AGE_MINUTES,
    LOG_FILE, daily_cap_for_day,
)
from sheet_client import SheetClient
from x_client import XClient, Tweet
from reply_generator import generate_reply
from validator import validate_reply, tweet_is_political


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("tarsen")


# TARSEN launch date - day 1 of warm-up. Update if you push the launch.
LAUNCH_DATE = datetime(2026, 4, 7).date()


def days_since_launch() -> int:
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    return max(1, (today - LAUNCH_DATE).days + 1)


def in_active_hours() -> bool:
    now = datetime.now(ZoneInfo(TIMEZONE)).time()
    return ACTIVE_HOURS_START <= now <= ACTIVE_HOURS_END


def follower_for_tier(tier: str) -> int:
    return {"mega": 1_500_000, "high": 200_000, "mid": 25_000, "small": 7_000}.get(tier, 10_000)


def pick_target(tweets: list[Tweet], sheet: SheetClient, banlists: dict, seed_lookup: dict) -> Tweet | None:
    """Filter and pick the highest-priority tweet."""
    candidates = []
    for t in tweets:
        # Don't reply to the same tweet twice
        if sheet.already_replied_to_tweet(t.url):
            log.info(f"  skip (already replied): {t.url}")
            continue
        # Twice-per-account-per-day rule
        if not sheet.can_reply_to_account(t.handle):
            log.info(f"  skip (account cap): @{t.handle}")
            continue
        # Political/religious skip
        is_political, kw = tweet_is_political(t.text, banlists)
        if is_political:
            log.info(f"  skip (political:{kw}): {t.url}")
            sheet.log_skip(t.url, f"political:{kw}", t.handle)
            continue
        # Patch in real follower count from seed lookup
        if t.handle.lower() in seed_lookup:
            seed = seed_lookup[t.handle.lower()]
            t.tier = seed.get("tier", t.tier)
            t.follower_count = follower_for_tier(t.tier)
        candidates.append(t)

    if not candidates:
        return None

    # Priority = follower count weighted slightly by recency
    def score(t: Tweet) -> float:
        age_min = max(1, (datetime.now(t.posted_at.tzinfo) - t.posted_at).total_seconds() / 60)
        return t.follower_count / (age_min ** 0.3)

    return sorted(candidates, key=score, reverse=True)[0]


def run_once(dry_run: bool) -> int:
    """Process one cron tick. Returns 0 on success, non-zero on early exit."""
    sheet = SheetClient()

    # 1. Kill switch
    if sheet.is_paused():
        log.warning("PAUSE flag is set in control!B2 - exiting.")
        return 1

    # 2. Active hours
    if not in_active_hours():
        log.info(f"Outside active hours ({ACTIVE_HOURS_START}-{ACTIVE_HOURS_END} ET) - exiting.")
        return 2

    # 3. Daily cap
    day = days_since_launch()
    cap = sheet.daily_cap_override() or daily_cap_for_day(day)
    posted_today = sheet.replied_today_count()
    log.info(f"Day {day}, cap {cap}, posted today {posted_today}")
    if posted_today >= cap:
        log.info("Daily cap reached - exiting.")
        return 3

    # 4. Pull tweets
    seeds = sheet.load_seed_accounts()
    seed_lookup = {s["handle"].lower(): s for s in seeds}
    log.info(f"Loaded {len(seeds)} active seed accounts")

    with XClient(dry_run=dry_run) as x:
        tweets = x.fetch_recent_from_seeds(seeds, max_per=3)
        log.info(f"Pulled {len(tweets)} candidate tweets")

        # 5. Filter and pick
        banlists = sheet.load_banlists()
        target = pick_target(tweets, sheet, banlists, seed_lookup)
        if not target:
            log.info("No eligible target tweet this run.")
            return 4
        log.info(f"Target: @{target.handle} - {target.url}")
        log.info(f"  text: {target.text[:120]}...")

        # 6. Enforce min age
        age_min = (datetime.now(target.posted_at.tzinfo) - target.posted_at).total_seconds() / 60
        min_age = random.randint(*MIN_TWEET_AGE_MINUTES)
        if age_min < min_age:
            wait_sec = int((min_age - age_min) * 60)
            log.info(f"  tweet age {age_min:.1f}min < {min_age}min - waiting {wait_sec}s")
            if not dry_run:
                time.sleep(wait_sec)

        # 7. Generate reply
        log.info("  generating reply...")
        try:
            result = generate_reply(
                tweet_text=target.text,
                handle=target.handle,
                follower_count=target.follower_count,
                tier=target.tier,
                posted_at=target.posted_at.isoformat(),
                thread_context=target.thread_context,
            )
        except Exception as e:
            log.error(f"  generation failed: {e}")
            return 5

        if result.get("skip_reason"):
            log.info(f"  model skipped: {result['skip_reason']}")
            sheet.log_skip(target.url, f"model:{result['skip_reason']}", target.handle)
            return 6

        reply_text = result.get("reply_text", "")
        log.info(f"  draft ({result.get('word_count')}w, style={result.get('reply_style')}, ex#{result.get('closest_example')}): {reply_text}")

        # 8. Validate
        passed, failed_check = validate_reply(reply_text, banlists)
        if not passed:
            log.warning(f"  validation FAILED: {failed_check}")
            sheet.log_validation_failure(target.url, reply_text, failed_check)
            return 7
        log.info("  validation passed")

        # 9. Decide approval path
        if sheet.manual_approval_on():
            # Week 1: log as pending, do not post
            row_id = sheet.insert_draft({
                "target_handle": target.handle,
                "tweet_url": target.url,
                "tweet_text": target.text,
                "thread_context": target.thread_context or "",
                "tweet_type": result.get("tweet_type", ""),
                "reply_style": result.get("reply_style", ""),
                "reply_text": reply_text,
                "word_count": result.get("word_count", len(reply_text.split())),
                "approval_status": "pending",
                "notes": f"closest_example={result.get('closest_example')}",
            })
            log.info(f"  logged as PENDING (id={row_id}). Approve in the Sheet to post.")
            return 0

        # After week 1: like + delay + post
        x.like_tweet(target.url)
        delay = random.randint(*LIKE_TO_POST_DELAY_SECONDS)
        log.info(f"  liked. waiting {delay}s before reply...")
        if not dry_run:
            time.sleep(delay)
        posted = x.post_reply(target.url, reply_text)
        if not posted:
            log.error("  reply post failed")
            return 8

        sheet.insert_draft({
            "target_handle": target.handle,
            "tweet_url": target.url,
            "tweet_text": target.text,
            "thread_context": target.thread_context or "",
            "tweet_type": result.get("tweet_type", ""),
            "reply_style": result.get("reply_style", ""),
            "reply_text": reply_text,
            "word_count": result.get("word_count", len(reply_text.split())),
            "approval_status": "auto",
            "approved_by": "auto",
            "notes": f"closest_example={result.get('closest_example')}",
        })
        log.info("  posted and logged.")
    return 0


def show_status():
    sheet = SheetClient()
    day = days_since_launch()
    cap = daily_cap_for_day(day)
    posted = sheet.replied_today_count()
    paused = sheet.is_paused()
    approval = sheet.manual_approval_on()
    print(f"TARSEN status:")
    print(f"  day {day} of operation, cap {cap}, posted today {posted}")
    print(f"  paused: {paused}")
    print(f"  manual approval: {approval}")
    print(f"  active hours now: {in_active_hours()}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", default=True, help="default. fixture tweets, no X access, no posting")
    p.add_argument("--live", action="store_true", help="opens browser, scrapes X, posts (be sure)")
    p.add_argument("--once", action="store_true", help="one tick then exit")
    p.add_argument("--status", action="store_true", help="show stats and exit")
    args = p.parse_args()

    if args.status:
        show_status()
        return

    dry_run = not args.live
    if args.live:
        log.warning("LIVE MODE: TARSEN will read x.com and may post a reply.")
    else:
        log.info("DRY RUN: fixture tweets, no X access, no posting.")

    code = run_once(dry_run=dry_run)
    sys.exit(code)


if __name__ == "__main__":
    main()
