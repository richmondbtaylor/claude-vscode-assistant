"""
Alpha Connectors Deal Flow Agent
Monitors 6 verticals for buying signals within the last 7 days.
Logs to Google Sheets + sends Slack alerts for qualifying signals.

Usage:
    python main.py              # Run once
    python main.py --loop       # Run continuously
"""

import argparse
import time
from datetime import datetime, timezone

from analyzer import analyze
from config import WEB_POLL_INTERVAL_HOURS
from linkedin_monitor import fetch_signals as linkedin_signals
from notifier import flush_slack_buffer, log_to_sheets, send_slack_alert
from storage import count_seen
from twitter_monitor import fetch_signals as twitter_signals
from web_monitor import fetch_signals as web_signals


def run_cycle() -> dict:
    stats = {"scanned": 0, "scored": 0, "logged": 0, "skipped_old": 0}
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'='*60}")
    print(f"Alpha Connectors Agent — {timestamp}")
    print(f"{'='*60}")

    sources = [
        ("LinkedIn", linkedin_signals()),
        ("Twitter/X", twitter_signals()),
        ("Web/Press", web_signals()),
    ]

    for source_name, signal_gen in sources:
        print(f"\n[{source_name}] Scanning...")
        source_count = 0
        for signal in signal_gen:
            stats["scanned"] += 1
            source_count += 1

            analysis = analyze(signal)
            if analysis is None:
                stats["skipped_old"] += 1
                continue

            stats["scored"] += 1
            if analysis.vertical == "not_relevant" or analysis.relevance_score < 30:
                continue

            print(
                f"  [{analysis.relevance_score:3d}] {analysis.vertical_label} | "
                f"{analysis.signal_type} | {signal.author[:40]}"
            )

            send_slack_alert(signal, analysis)
            if log_to_sheets(signal, analysis):
                stats["logged"] += 1

        flush_slack_buffer()
        print(f"  Done: {source_count} signals from {source_name}")

    print(f"\n[Summary] Scanned: {stats['scanned']} | Scored: {stats['scored']} | "
          f"Logged: {stats['logged']} | Skipped (old): {stats['skipped_old']} | "
          f"Total seen: {count_seen()}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Alpha Connectors Deal Flow Agent")
    parser.add_argument("--loop", action="store_true", help="Run continuously on a schedule")
    args = parser.parse_args()

    if args.loop:
        interval_seconds = WEB_POLL_INTERVAL_HOURS * 3600
        print(f"Starting continuous loop every {WEB_POLL_INTERVAL_HOURS}h...")
        while True:
            try:
                run_cycle()
            except KeyboardInterrupt:
                print("\nStopping agent.")
                break
            except Exception as e:
                print(f"[main] Cycle error: {e}")
            print(f"Sleeping {WEB_POLL_INTERVAL_HOURS}h until next cycle...")
            time.sleep(interval_seconds)
    else:
        run_cycle()


if __name__ == "__main__":
    main()
