"""
Run the Alpha Connectors agent across ALL sources, enforce source diversity,
then log the top 25 leads scored 70+ to Google Sheets.

Source caps prevent LinkedIn from dominating — each source contributes evenly.
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from dataclasses import dataclass
from typing import Optional

from analyzer import RawSignal, SignalAnalysis, analyze
from config import WEB_POLL_INTERVAL_HOURS
from linkedin_monitor import fetch_signals as linkedin_signals
from notifier import flush_slack_buffer, log_to_sheets, send_slack_alert
from twitter_monitor import fetch_signals as twitter_signals
from web_monitor import fetch_signals as web_signals

TARGET_LEADS = 25
HOT_THRESHOLD = 70
MAX_PER_SOURCE = 10  # Cap per source to enforce diversity


@dataclass
class ScoredLead:
    signal: RawSignal
    analysis: SignalAnalysis


def collect_from_source(name: str, generator, cap: int) -> list[ScoredLead]:
    """Drain a source generator, score each signal, return hot leads up to cap."""
    leads: list[ScoredLead] = []
    scanned = 0

    print(f"\n[{name}] Collecting signals (cap: {cap} hot leads)...")
    for signal in generator:
        scanned += 1
        analysis = analyze(signal)
        if analysis is None or analysis.vertical == "not_relevant":
            continue

        score = analysis.relevance_score
        status = f"[{score:3d}] {analysis.vertical_label} | {analysis.signal_type} | {signal.author[:35]}"

        if score >= HOT_THRESHOLD:
            print(f"  HOT  {status}")
            leads.append(ScoredLead(signal, analysis))
            if len(leads) >= cap:
                print(f"  [{name}] Cap of {cap} hot leads reached — moving to next source")
                break
        elif score >= 40:
            print(f"  WARM {status}")

    print(f"  [{name}] Done: {scanned} scanned, {len(leads)} hot leads found")
    return leads


def run_mixed_cycle() -> int:
    print("\n" + "="*60)
    print(f"Alpha Connectors — Mixed Source Run (target: {TARGET_LEADS} leads across all sources)")
    print("="*60)

    # ── Collect from all 3 sources ────────────────────────────────
    all_leads: list[ScoredLead] = []

    sources = [
        ("LinkedIn",  linkedin_signals()),
        ("Twitter/X", twitter_signals()),
        ("Web/Press",  web_signals()),
    ]

    for name, gen in sources:
        leads = collect_from_source(name, gen, MAX_PER_SOURCE)
        all_leads.extend(leads)
        print(f"  Running total: {len(all_leads)} hot leads so far")

    # ── Sort by score descending, take top 25 ────────────────────
    all_leads.sort(key=lambda x: x.analysis.relevance_score, reverse=True)
    top_leads = all_leads[:TARGET_LEADS]

    # ── Summary by source ────────────────────────────────────────
    source_counts: dict[str, int] = {}
    for lead in top_leads:
        src = lead.signal.platform.capitalize()
        source_counts[src] = source_counts.get(src, 0) + 1

    print(f"\n{'='*60}")
    print(f"Top {len(top_leads)} leads selected (sorted by score):")
    for src, count in sorted(source_counts.items()):
        print(f"  {src}: {count} leads")
    print("="*60)

    # ── Log to Sheets + Slack ─────────────────────────────────────
    logged = 0
    for lead in top_leads:
        send_slack_alert(lead.signal, lead.analysis)
        if log_to_sheets(lead.signal, lead.analysis):
            logged += 1
        print(f"  [{lead.analysis.relevance_score:3d}] {lead.analysis.vertical_label} | "
              f"{lead.signal.platform.capitalize()} | {lead.signal.author[:40]}")

    flush_slack_buffer()

    print(f"\nDone. {logged} leads logged to Sheets.")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{os.environ['GOOGLE_SHEET_ID']}/edit")
    return logged


if __name__ == "__main__":
    run_mixed_cycle()
