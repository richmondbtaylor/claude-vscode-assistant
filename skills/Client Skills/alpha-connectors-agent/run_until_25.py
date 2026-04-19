"""
Run the Alpha Connectors agent continuously until 25 leads scored 70+ are logged.
"""
import os
import sys

# Load .env before any other imports
from dotenv import load_dotenv
load_dotenv()

# Fix Windows encoding
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import sqlite3
import time
from pathlib import Path

from analyzer import analyze
from config import WEB_POLL_INTERVAL_HOURS
from linkedin_monitor import fetch_signals as linkedin_signals
from notifier import flush_slack_buffer, log_to_sheets, send_slack_alert
from storage import count_seen
from twitter_monitor import fetch_signals as twitter_signals
from web_monitor import fetch_signals as web_signals

TARGET_LEADS = 25
HOT_THRESHOLD = 70
DB_PATH = Path(__file__).parent / "seen_signals.db"


def count_hot_leads() -> int:
    """Count rows logged to Sheets with score >= 70 this session."""
    return _session_hot_count


_session_hot_count = 0


def run_cycle() -> int:
    """Run one full cycle. Returns number of hot leads found this cycle."""
    global _session_hot_count
    cycle_hot = 0

    sources = [
        ("LinkedIn", linkedin_signals()),
        ("Twitter/X", twitter_signals()),
        ("Web/Press", web_signals()),
    ]

    for source_name, signal_gen in sources:
        print(f"\n[{source_name}] Scanning... (hot leads so far: {_session_hot_count}/{TARGET_LEADS})")
        for signal in signal_gen:
            analysis = analyze(signal)
            if analysis is None or analysis.vertical == "not_relevant":
                continue

            score = analysis.relevance_score
            print(f"  [{score:3d}] {analysis.vertical_label} | {analysis.signal_type} | {signal.author[:40]}")

            if score >= HOT_THRESHOLD:
                send_slack_alert(signal, analysis)
                if log_to_sheets(signal, analysis):
                    _session_hot_count += 1
                    cycle_hot += 1
                    print(f"  *** HOT LEAD {_session_hot_count}/{TARGET_LEADS} logged ***")

                    if _session_hot_count >= TARGET_LEADS:
                        flush_slack_buffer()
                        return cycle_hot
            elif score >= 40:
                log_to_sheets(signal, analysis)

        flush_slack_buffer()

        if _session_hot_count >= TARGET_LEADS:
            break

    return cycle_hot


def main():
    print(f"Alpha Connectors Agent — running until {TARGET_LEADS} leads scored {HOT_THRESHOLD}+")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{os.environ['GOOGLE_SHEET_ID']}/edit\n")

    cycle = 0
    while _session_hot_count < TARGET_LEADS:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"CYCLE {cycle} | Hot leads: {_session_hot_count}/{TARGET_LEADS}")
        print(f"{'='*60}")

        try:
            run_cycle()
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"[error] Cycle {cycle} failed: {e}")

        if _session_hot_count >= TARGET_LEADS:
            break

        wait = WEB_POLL_INTERVAL_HOURS * 3600
        print(f"\nWaiting {WEB_POLL_INTERVAL_HOURS}h before next cycle... ({_session_hot_count}/{TARGET_LEADS} hot leads)")
        time.sleep(wait)

    print(f"\nDone. {_session_hot_count} hot leads (score {HOT_THRESHOLD}+) logged to Sheets.")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{os.environ['GOOGLE_SHEET_ID']}/edit")


if __name__ == "__main__":
    main()
