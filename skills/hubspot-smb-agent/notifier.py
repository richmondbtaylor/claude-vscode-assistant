"""
Output layer: logs leads to Google Sheets and sends Slack alerts.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import gspread
import requests

from analyzer import PostAnalysis, RawPost
from config import (
    LOG_ALL_TO_SHEETS,
    MIN_RELEVANCE_FOR_SHEETS,
    SHEET_COLUMNS,
    SHEET_WORKSHEET_NAME,
)

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
            rows=1000,
            cols=len(SHEET_COLUMNS),
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        print(f"[sheets] Created worksheet '{SHEET_WORKSHEET_NAME}' with headers")
    return ws


def log_to_sheets(post: RawPost, analysis: PostAnalysis, cross_platform: str = "") -> bool:
    should_log = LOG_ALL_TO_SHEETS or (analysis.relevance_score >= MIN_RELEVANCE_FOR_SHEETS)
    if not should_log:
        return False

    try:
        ws = _get_worksheet()
        row = [
            datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M"),
            post.published_at.strftime("%m/%d/%Y") if post.published_at else "",
            post.platform.capitalize(),
            post.subreddit or "",
            post.url,
            post.author,
            post.title,
            analysis.relevance_score,
            analysis.lead_score,
            analysis.icp_category,
            analysis.business_type,
            analysis.pain_point_type,
            analysis.pain_point_description,
            analysis.why_it_fits,
            analysis.urgency,
            "Yes" if analysis.is_decision_maker else "No",
            analysis.competitor_mentioned or "",
            cross_platform,
            analysis.reasoning,
            "",  # Status
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[sheets] Logged: {post.title[:60]}...")
        return True
    except Exception as e:
        print(f"[sheets] Failed to log post {post.id}: {e}")
        return False


_SLACK_BATCH_SIZE = 5
_pending_slack_leads: list[tuple[RawPost, PostAnalysis]] = []


def send_slack_alert(post: RawPost, analysis: PostAnalysis) -> bool:
    if analysis.relevance_score < 50:
        return False
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return False
    _pending_slack_leads.append((post, analysis))
    return True


def flush_slack_buffer() -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url or not _pending_slack_leads:
        return

    leads = _pending_slack_leads[:]
    _pending_slack_leads.clear()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SHEET_ID', '')}/edit"
    count = len(leads)

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Bishop AI — {count} New Lead{'s' if count > 1 else ''} Found"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{count} new lead{'s' if count > 1 else ''} logged to Google Sheets."},
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
        print(f"[slack] Sent batch of {count} lead(s)")
    except requests.RequestException as e:
        print(f"[slack] Failed to send batch: {e}")
        _pending_slack_leads.extend(leads)
