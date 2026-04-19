"""
Output layer: Slack alerts + Google Sheets logging for Alpha Connectors deal signals.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import gspread
import requests

from analyzer import RawSignal, SignalAnalysis
from config import (
    MIN_RELEVANCE_FOR_ALERT,
    MIN_RELEVANCE_FOR_SHEETS,
    SHEET_COLUMNS,
    SHEET_WORKSHEET_NAME,
)

# ── Google Sheets ─────────────────────────────────────────────────────────────

_sheets_client: Optional[gspread.Client] = None


def _get_sheets_client() -> gspread.Client:
    global _sheets_client
    if _sheets_client is None:
        creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")
        _sheets_client = gspread.oauth(credentials_filename=creds_path)
    return _sheets_client


def _get_worksheet() -> gspread.Worksheet:
    gc = _get_sheets_client()
    spreadsheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    try:
        ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=SHEET_WORKSHEET_NAME,
            rows=2000,
            cols=len(SHEET_COLUMNS),
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        print(f"[sheets] Created worksheet '{SHEET_WORKSHEET_NAME}'")
    return ws


def log_to_sheets(signal: RawSignal, analysis: SignalAnalysis) -> bool:
    if analysis.relevance_score < MIN_RELEVANCE_FOR_SHEETS:
        return False
    try:
        ws = _get_worksheet()
        row = [
            datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M"),
            analysis.vertical_label,
            analysis.signal_type,
            signal.platform.capitalize(),
            signal.url,
            signal.author,
            signal.title,
            analysis.deal_size_estimate,
            analysis.relevance_score,
            analysis.urgency,
            "Yes" if analysis.is_decision_maker else "No",
            analysis.signal_age_days,
            analysis.connection_angle,
            " | ".join(analysis.pain_points),
            analysis.suggested_intro,
            "Yes" if analysis.should_contact else "No",
            analysis.reasoning,
            "",  # Status
            "",  # Contacted Date
            "",  # Meeting Booked
            "", "", "", "", "", "",  # Enrichment placeholders
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[sheets] Logged: {signal.title[:60]}... [{analysis.vertical_label}]")
        return True
    except Exception as e:
        print(f"[sheets] Failed to log {signal.id}: {e}")
        return False


# ── Slack ─────────────────────────────────────────────────────────────────────

_pending: list[tuple[RawSignal, SignalAnalysis]] = []
_BATCH_SIZE = 5


def _urgency_emoji(urgency: str) -> str:
    return {"high": "🔥", "medium": "⭐", "low": "📌"}.get(urgency, "📌")


def _vertical_emoji(vertical: str) -> str:
    return {
        "tech_projects": "💻",
        "real_estate": "🏗️",
        "renewables_data_centers": "⚡",
        "gov_contracts": "🏛️",
        "startup_founders": "🚀",
        "capital_partners": "💰",
    }.get(vertical, "📊")


def send_slack_alert(signal: RawSignal, analysis: SignalAnalysis) -> bool:
    if analysis.relevance_score < MIN_RELEVANCE_FOR_ALERT:
        return False
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("[slack] SLACK_WEBHOOK_URL not set")
        return False
    _pending.append((signal, analysis))
    print(f"[slack] Queued {len(_pending)} lead(s) (score {analysis.relevance_score} | {analysis.vertical_label})")
    if len(_pending) >= _BATCH_SIZE:
        _flush(webhook_url)
    return True


def flush_slack_buffer() -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if webhook_url and _pending:
        _flush(webhook_url)


def _flush(webhook_url: str) -> None:
    global _pending
    if not _pending:
        return

    leads = _pending[:]
    _pending.clear()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SHEET_ID', '')}/edit"
    count = len(leads)

    lead_lines = []
    for sig, ana in leads[:8]:
        emoji = _urgency_emoji(ana.urgency)
        vert = _vertical_emoji(ana.vertical)
        lead_lines.append(
            f"{emoji}{vert} *{ana.vertical_label}* — {ana.signal_type} | Score: {ana.relevance_score}\n"
            f"   _{sig.author}_ · {sig.platform.capitalize()}\n"
            f"   {ana.connection_angle}"
        )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Alpha Connectors — {count} New Deal Signal{'s' if count > 1 else ''}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "\n\n".join(lead_lines)},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in Google Sheets"},
                    "url": sheet_url,
                    "style": "primary",
                }
            ],
        },
    ]

    try:
        resp = requests.post(webhook_url, json={"blocks": blocks}, timeout=10)
        resp.raise_for_status()
        print(f"[slack] Sent batch of {len(leads)} signal(s)")
    except requests.RequestException as e:
        print(f"[slack] Failed to send: {e}")
        _pending.extend(leads)
