#!/usr/bin/env python3
"""
LinkedIn Comment Reply Bot
Checks Rich's recent LinkedIn posts for new comments between 2-5 PM daily
and auto-replies using Claude AI. Logs all activity to Google Sheets.

Usage:
    python main.py          # Run scheduler (keeps running all day)
    python main.py --now    # Run one check immediately (for testing)
"""

import sys
import time
import random
import datetime
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

from linkedin_bot import LinkedInCommentBot
from sheets_logger import SheetsLogger

WINDOW_START_HOUR = 14   # 2 PM
WINDOW_END_HOUR = 17     # 5 PM
CHECKS_PER_DAY_MIN = 3
CHECKS_PER_DAY_MAX = 6


def get_run_times_for_today():
    """Pick 3-6 random check times in today's 2-5 PM window."""
    now = datetime.datetime.now()
    today = now.date()

    window_start = datetime.datetime.combine(today, datetime.time(WINDOW_START_HOUR, 0))
    window_end = datetime.datetime.combine(today, datetime.time(WINDOW_END_HOUR, 0))

    # If past the window, schedule for tomorrow
    if now >= window_end:
        tomorrow = today + datetime.timedelta(days=1)
        window_start = datetime.datetime.combine(tomorrow, datetime.time(WINDOW_START_HOUR, 0))
        window_end = datetime.datetime.combine(tomorrow, datetime.time(WINDOW_END_HOUR, 0))

    window_seconds = int((window_end - window_start).total_seconds())
    count = random.randint(CHECKS_PER_DAY_MIN, CHECKS_PER_DAY_MAX)

    times = sorted([
        window_start + datetime.timedelta(seconds=random.randint(0, window_seconds))
        for _ in range(count)
    ])

    # Drop times already past
    return [t for t in times if t > now]


def sleep_until(target: datetime.datetime):
    now = datetime.datetime.now()
    secs = (target - now).total_seconds()
    if secs <= 0:
        return
    mins = secs / 60
    print(f"[{now.strftime('%H:%M:%S')}] Sleeping {mins:.1f} min until {target.strftime('%H:%M:%S')}...")
    time.sleep(secs)


def run_check(sheets_logger):
    """Single check cycle: scrape posts, find new comments, reply, log."""
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting comment check...")
    bot = None
    try:
        bot = LinkedInCommentBot()
        results = bot.run()
    finally:
        if bot:
            bot.close()

    if not results:
        print("No new comments found or replied to.")
        return

    print(f"Replied to {len(results)} comment(s).")

    if sheets_logger:
        try:
            sheets_logger.log_batch(results)
            print(f"Logged {len(results)} row(s) to Google Sheets.")
        except Exception as e:
            print(f"Sheets log error: {e}")


def main():
    run_now = "--now" in sys.argv

    print("=== LinkedIn Comment Reply Bot ===")
    print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Init Sheets (optional - bot still runs without it)
    sheets_logger = None
    try:
        sheets_logger = SheetsLogger()
        print("Google Sheets logger ready.")
    except Exception as e:
        print(f"Sheets unavailable ({e}) — logging to console only.")

    if run_now:
        run_check(sheets_logger)
        return

    # Continuous scheduler
    while True:
        run_times = get_run_times_for_today()

        if not run_times:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            next_window = datetime.datetime.combine(tomorrow, datetime.time(WINDOW_START_HOUR, 0))
            print(f"\nWindow closed for today. Next window: {next_window.strftime('%Y-%m-%d %H:%M')}")
            sleep_until(next_window)
            continue

        print(f"\nScheduled {len(run_times)} check(s) today:")
        for t in run_times:
            print(f"  {t.strftime('%H:%M:%S')}")

        for run_time in run_times:
            sleep_until(run_time)
            try:
                run_check(sheets_logger)
            except Exception as e:
                print(f"Check failed: {e}")
                traceback.print_exc()

            # Random cooldown between checks so they don't cluster
            if run_time != run_times[-1]:
                cooldown = random.randint(90, 300)
                print(f"Cooldown {cooldown}s before next check...")
                time.sleep(cooldown)

        print("\nAll checks done for today.")


if __name__ == "__main__":
    main()
