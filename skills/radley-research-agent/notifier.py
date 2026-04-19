"""
Output layer: sends analyzed leads to Slack and Google Sheets.

Slack leads are batched — a digest is sent only when flush_slack_buffer() is called
at the end of a poll cycle.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import gspread
import requests

from analyzer import PostAnalysis, RawPost
from config import (
    LOG_ALL_TO_SHEETS,
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
    spreadsheet = gc.open_by_key(os.environ["RADLEY_SHEET_ID"])
    try:
        ws = spreadsheet.worksheet(SHEET_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=SHEET_WORKSHEET_NAME,
            rows=1000,
            cols=len(SHEET_COLUMNS),
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        print(f"[sheets] Created worksheet '{SHEET_WORKSHEET_NAME}' with headers")
    return ws


def log_to_sheets(post: RawPost, analysis: PostAnalysis, cross_platform: str = "") -> bool:
    """Append a row to Google Sheets. Returns True on success."""
    should_log = LOG_ALL_TO_SHEETS or (analysis.relevance_score >= MIN_RELEVANCE_FOR_SHEETS)
    if not should_log:
        return False

    try:
        ws = _get_worksheet()
        _platform_labels = {
            "n8n_community": "n8n Community",
            "indiehackers": "Indie Hackers",
        }
        platform_label = _platform_labels.get(post.platform, post.platform.capitalize())

        row = [
            datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M"),
            platform_label,
            post.subreddit or "",
            post.url,
            post.author,
            post.title,
            analysis.relevance_score,
            getattr(analysis, "intent_score", 0),
            cross_platform or "No",
            analysis.intent_type,
            analysis.urgency,
            "Yes" if getattr(analysis, "is_decision_maker", True) else "No",
            getattr(analysis, "budget_tier", "uncertain"),
            "Yes" if getattr(analysis, "already_solved", False) else "No",
            " | ".join(analysis.pain_points),
            " | ".join(analysis.budget_signals),
            analysis.suggested_reply,
            "Yes" if analysis.should_contact else "No",
            analysis.reasoning,
            "",  # Status column — user fills in manually
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[sheets] Logged: {post.title[:60]}...")
        return True
    except Exception as e:
        print(f"[sheets] Failed to log post {post.id}: {e}")
        return False


# ── Slack ─────────────────────────────────────────────────────────────────────

_pending_slack_leads: list[tuple[RawPost, PostAnalysis]] = []


def send_slack_alert(post: RawPost, analysis: PostAnalysis) -> bool:
    """Queue a lead for Slack batch notification."""
    if analysis.relevance_score < MIN_RELEVANCE_FOR_ALERT:
        return False

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return False

    _pending_slack_leads.append((post, analysis))
    print(
        f"[slack] Queued lead {len(_pending_slack_leads)} "
        f"(score {analysis.relevance_score} | {analysis.intent_type})"
    )
    return True


def flush_slack_buffer() -> None:
    """Send any remaining queued leads at the end of a cycle."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url or not _pending_slack_leads:
        return
    _flush_slack_batch(webhook_url)


def _flush_slack_batch(webhook_url: str) -> bool:
    """Send a Slack notification with lead count and a link to Google Sheets."""
    global _pending_slack_leads

    if not _pending_slack_leads:
        return False

    leads = _pending_slack_leads[:]
    _pending_slack_leads.clear()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{os.environ.get('RADLEY_SHEET_ID', '')}/edit"
    count = len(leads)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Radley Lead Finder — {count} New Lead{'s' if count > 1 else ''} Found",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{count} new R&D tax credit lead{'s have' if count > 1 else ' has'} been logged to Google Sheets. Click below to review.",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Leads in Google Sheets"},
                    "url": sheet_url,
                    "style": "primary",
                }
            ],
        },
    ]

    try:
        resp = requests.post(webhook_url, json={"blocks": blocks}, timeout=10)
        resp.raise_for_status()
        print(f"[slack] Sent batch of {len(leads)} lead(s)")
        return True
    except requests.RequestException as e:
        print(f"[slack] Failed to send batch: {e}")
        _pending_slack_leads.extend(leads)
        return False
