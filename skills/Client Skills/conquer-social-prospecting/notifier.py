"""
Output layer: logs leads to Google Sheets and sends Slack digest alerts.
Slack batches leads and flushes at end of each poll cycle.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import gspread
import requests

import enrichment
from analyzer import PostAnalysis, RawPost
from config import (
    LOG_ALL_TO_SHEETS,
    MIN_INTENT_FOR_ALERT,
    MIN_INTENT_FOR_SHEETS,
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
            rows=1000,
            cols=len(SHEET_COLUMNS),
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        print(f"[sheets] Created worksheet '{SHEET_WORKSHEET_NAME}' with headers")
    return ws


def log_to_sheets(post: RawPost, analysis: PostAnalysis) -> bool:
    """Append a lead row to Google Sheets. Returns True on success."""
    should_log = LOG_ALL_TO_SHEETS or (analysis.intent_score >= MIN_INTENT_FOR_SHEETS)
    if not should_log:
        return False

    try:
        ws = _get_worksheet()

        _platform_labels = {
            "linkedin": "LinkedIn",
            "reddit": "Reddit",
            "twitter": "Twitter / X",
            "quora": "Quora",
            "facebook": "Facebook",
            "g2": "G2",
            "trustpilot": "Trustpilot",
            "facebook": "Facebook",
            "saleshacker": "Sales Hacker",
            "trailblazer": "Salesforce Trailblazer",
            "web": "Web",
        }
        platform_label = _platform_labels.get(post.platform, post.platform.capitalize())

        # Decision maker enrichment
        contact = enrichment.enrich(analysis.company_name, analysis.job_title)
        contact_email    = contact.get("email", "")
        contact_name     = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        contact_title    = contact.get("title", "")
        contact_source   = contact.get("source", "")

        row = [
            datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M"),
            platform_label,
            post.subreddit or "",
            post.url,
            post.author,
            post.title[:200],
            analysis.intent_score,
            analysis.score_tier,
            analysis.job_title,
            analysis.company_name,
            "Yes" if analysis.salesforce_confirmed else "No",
            "Yes" if analysis.gdpr_flag else "No",
            analysis.industry_signal,
            analysis.company_size_signal,
            analysis.pain_category,
            analysis.competitor_mentioned,
            analysis.post_date if analysis.post_date != "unknown" else "",
            analysis.post_age_days if analysis.post_age_days >= 0 else "",
            contact_name,
            contact_title,
            contact_email,
            contact_source,
            analysis.outreach_public_forum,
            analysis.outreach_dm_pivot,
            analysis.outreach_direct_internal,
            "Yes" if analysis.should_contact else "No",
            analysis.escalation,
            analysis.crm_check,
            analysis.reasoning,
            "",  # Status — user fills in manually
        ]

        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[sheets] Logged [{analysis.score_tier}] {post.title[:60]}...")
        return True

    except Exception as e:
        print(f"[sheets] Failed to log post {post.id}: {e}")
        return False


# ── Slack ─────────────────────────────────────────────────────────────────────

_pending_slack_leads: list[tuple[RawPost, PostAnalysis]] = []


def _tier_emoji(tier: str) -> str:
    return {"High": "🔥", "Medium": "⭐", "Low": "📌"}.get(tier, "📌")


def _category_label(category: str) -> str:
    labels = {
        "competitor_dissatisfaction": "😤 Competitor Complaint",
        "pricing_pain": "💰 Pricing Pain",
        "integration_pain": "🔗 Integration Pain",
        "buying_intent": "💳 Buying Intent",
        "general_pain": "🎯 General Pain",
        "brand_mention": "🏷 Brand Mention",
        "not_relevant": "❌ Not Relevant",
    }
    return labels.get(category, category)


def send_slack_alert(post: RawPost, analysis: PostAnalysis) -> bool:
    """Queue a lead for Slack. Fires when flush_slack_buffer() is called."""
    if analysis.intent_score < MIN_INTENT_FOR_ALERT:
        return False

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("[slack] SLACK_WEBHOOK_URL not set — skipping alert")
        return False

    _pending_slack_leads.append((post, analysis))
    print(
        f"[slack] Queued lead (score {analysis.intent_score} | {analysis.score_tier} | {analysis.pain_category})"
    )
    return True


def flush_slack_buffer() -> None:
    """Send any queued leads at the end of a cycle."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url or not _pending_slack_leads:
        return
    _flush_slack_batch(webhook_url)


def _flush_slack_batch(webhook_url: str) -> bool:
    global _pending_slack_leads

    if not _pending_slack_leads:
        return False

    leads = _pending_slack_leads[:]
    _pending_slack_leads.clear()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SHEET_ID', '')}/edit"
    count = len(leads)
    high_count = sum(1 for _, a in leads if a.score_tier == "High")
    medium_count = sum(1 for _, a in leads if a.score_tier == "Medium")

    summary_text = f"{count} new lead{'s' if count > 1 else ''} logged"
    if high_count:
        summary_text += f" | 🔥 {high_count} High"
    if medium_count:
        summary_text += f" | ⭐ {medium_count} Medium"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Conquer.io — {count} New Lead{'s' if count > 1 else ''} Found",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{summary_text}. Click below to review and assign.",
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
        print(f"[slack] Sent batch of {count} lead(s)")
        return True
    except requests.RequestException as e:
        print(f"[slack] Failed to send batch: {e}")
        _pending_slack_leads.extend(leads)
        return False
