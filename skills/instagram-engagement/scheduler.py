"""
Daily Session Scheduler — Instagram Engagement Automation

Runs once at the start of each day (via Windows Task Scheduler at 7:35 AM).
Calculates how many sessions to run today based on the account's RISEN ramp-up day,
picks random start times distributed across the allowed window, and fires off
main.py at each scheduled time.

Allowed window: 7:35 AM – 10:10 PM (local time)
Session duration: 60 minutes each
Minimum gap between sessions: 90 minutes (so they never overlap)
"""

import argparse
import logging
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Window configuration (local time)
# ---------------------------------------------------------------------------

WINDOW_START = (7, 35)    # 7:35 AM
WINDOW_END   = (22, 10)   # 10:10 PM

SESSION_DURATION_MINUTES = 60
MIN_GAP_MINUTES = 90       # minimum minutes between session start times

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent


def _window_minutes() -> tuple[int, int]:
    """Return window start and end as minutes-since-midnight."""
    return (
        WINDOW_START[0] * 60 + WINDOW_START[1],
        WINDOW_END[0] * 60 + WINDOW_END[1],
    )


def _today_at(minutes_since_midnight: int) -> datetime:
    now = datetime.now()
    return now.replace(
        hour=minutes_since_midnight // 60,
        minute=minutes_since_midnight % 60,
        second=0,
        microsecond=0,
    )


def pick_session_times(n: int) -> list[datetime]:
    """
    Pick n random, non-overlapping session start times within today's window.
    Sessions are separated by at least MIN_GAP_MINUTES.
    If launched mid-day, only schedules sessions from 5 minutes from now onward.
    Returns sorted list of datetime objects.
    """
    win_start, win_end = _window_minutes()
    now = datetime.now()
    now_mins = now.hour * 60 + now.minute + 5  # 5-min buffer from now
    win_start = max(win_start, now_mins)  # don't schedule in the past
    required_span = SESSION_DURATION_MINUTES + (n - 1) * MIN_GAP_MINUTES
    available = win_end - win_start

    if available < required_span:
        # Can't fit all sessions — fit as many as possible
        n = max(1, (available - SESSION_DURATION_MINUTES) // MIN_GAP_MINUTES + 1)
        logger.warning(f"Window too narrow for requested sessions — fitting {n} instead")

    # Generate n start offsets with min gap enforced
    slots = []
    for _ in range(1000):  # retry loop
        candidates = sorted(random.randint(win_start, win_end - SESSION_DURATION_MINUTES) for _ in range(n))
        valid = True
        for i in range(1, len(candidates)):
            if candidates[i] - candidates[i - 1] < MIN_GAP_MINUTES:
                valid = False
                break
        if valid:
            slots = candidates
            break

    if not slots:
        # Fallback: evenly space them with jitter
        step = (win_end - win_start - SESSION_DURATION_MINUTES) // max(n, 1)
        slots = [win_start + i * step + random.randint(0, min(20, step // 2)) for i in range(n)]

    return [_today_at(m) for m in slots]


def sessions_for_today(account: str) -> int:
    """
    Determine how many sessions to run today based on the account's ramp-up day.
    Imports engagement_tracker locally to avoid issues if DB doesn't exist yet.
    """
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        import engagement_tracker as tracker
        from config import RAMP_UP_MATRIX

        tracker.init_db()
        day = tracker.get_account_day_number(account)
        for tier in RAMP_UP_MATRIX:
            start, end = tier["days"]
            if start <= day <= end:
                logger.info(f"Account day {day} — ramp tier: {tier['sessions']} sessions/day")
                return tier["sessions"]
        return 5  # default max
    except Exception as e:
        logger.warning(f"Could not determine ramp-up day ({e}) — defaulting to 3 sessions")
        return 3


def run_session(account: str, focus: str):
    """Launch main.py for one session as a subprocess."""
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "main.py"),
        "--account", account,
        "--focus", focus,
        "--duration", str(SESSION_DURATION_MINUTES),
    ]
    logger.info(f"Launching: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
        if result.returncode != 0:
            logger.error(f"Session exited with code {result.returncode}")
        else:
            logger.info("Session completed successfully")
    except Exception as e:
        logger.error(f"Failed to launch session: {e}")


def _is_in_blackout(dt: datetime) -> bool:
    """Return True if the given datetime falls within the daily blackout window."""
    current_mins = dt.hour * 60 + dt.minute
    start_mins = WINDOW_END[0] * 60 + WINDOW_END[1]    # blackout starts at window end
    end_mins   = WINDOW_START[0] * 60 + WINDOW_START[1] # blackout ends at window start
    # Window wraps midnight (e.g. 22:10 → 07:35)
    return current_mins >= start_mins or current_mins < end_mins


def main():
    parser = argparse.ArgumentParser(description="Daily Instagram Engagement Scheduler")
    parser.add_argument("--account", required=True, help="Account key (e.g. main_account)")
    parser.add_argument("--focus", required=True, help="Hashtag to target (e.g. #AIautomation)")
    args = parser.parse_args()

    n = sessions_for_today(args.account)
    times = pick_session_times(n)

    logger.info(f"Today's schedule ({n} sessions) for @{args.account}:")
    for i, t in enumerate(times, 1):
        logger.info(f"  Session {i}: {t.strftime('%I:%M %p')}")

    for i, scheduled_time in enumerate(times, 1):
        now = datetime.now()
        wait_secs = max(0, (scheduled_time - now).total_seconds())

        if wait_secs > 0:
            logger.info(
                f"Session {i}/{n}: waiting {wait_secs/60:.0f}min until "
                f"{scheduled_time.strftime('%I:%M %p')}"
            )
            time.sleep(wait_secs)

        # After sleeping (or if already past), re-check time in case PC was asleep
        now = datetime.now()

        # If scheduled time passed by more than the session duration, the window is gone — skip
        overdue_mins = (now - scheduled_time).total_seconds() / 60
        if overdue_mins > SESSION_DURATION_MINUTES:
            logger.warning(
                f"Session {i}/{n}: skipping — overdue by {overdue_mins:.0f}min "
                f"(scheduled {scheduled_time.strftime('%I:%M %p')}, now {now.strftime('%I:%M %p')})"
            )
            continue

        # If we're in the blackout window, skip rather than launching a process that sleeps overnight
        if _is_in_blackout(now):
            logger.warning(
                f"Session {i}/{n}: skipping — current time {now.strftime('%I:%M %p')} "
                f"is in blackout window ({WINDOW_END[0]:02d}:{WINDOW_END[1]:02d}–"
                f"{WINDOW_START[0]:02d}:{WINDOW_START[1]:02d})"
            )
            continue

        logger.info(f"Starting session {i}/{n}")
        run_session(args.account, args.focus)

    logger.info("All sessions complete for today.")


if __name__ == "__main__":
    main()
