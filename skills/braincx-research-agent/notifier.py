"""
Output layer: sends analyzed leads to Slack and Google Sheets.

Slack leads are batched — a digest is sent only when 5 leads accumulate,
or when flush_slack_buffer() is called at the end of a poll cycle.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import gspread
import requests

import apollo_enrichment
import contact_finder
import email_finder
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
    """Append a row to Google Sheets. Returns True on success."""
    should_log = LOG_ALL_TO_SHEETS or (analysis.relevance_score >= MIN_RELEVANCE_FOR_SHEETS)
    if not should_log:
        return False

    try:
        ws = _get_worksheet()
        _platform_labels = {
            "n8n_community": "n8n Community",
            "indiehackers": "Indie Hackers",
            "producthunt": "Product Hunt",
        }
        platform_label = _platform_labels.get(post.platform, post.platform.capitalize())

        # Enrich with contact info for Hot/Warm leads
        contact = contact_finder.ContactInfo()
        if analysis.relevance_score >= 50:
            # Best company name source: author field, then parse title for job postings
            company = post.author if post.author and post.author not in ("unknown", "") else ""
            if not company and getattr(analysis, "is_job_posting", False):
                # LinkedIn jobs: "Sanitas Medical Centers hiring Medical Receptionist..."
                title = post.title or ""
                if " hiring " in title:
                    company = title.split(" hiring ")[0].strip()
                # Indeed specific company: "Front Desk Coordinator - Crystal City, MO - CompanyName"
                elif " - " in title and not title.lower().startswith("apply today"):
                    parts = title.split(" - ")
                    # Last segment before location is usually company name
                    if len(parts) >= 3:
                        company = parts[-2].strip()
                    elif len(parts) == 2:
                        company = parts[0].strip()
            if company:
                contact = contact_finder.lookup(company_name=company, platform=post.platform)

        # Decision-maker enrichment: Apollo first, then existing email_finder fallback
        dm = email_finder.DecisionMaker()
        if analysis.relevance_score >= 50 and company:
            icp = getattr(analysis, "icp_category", "")
            apollo = apollo_enrichment.enrich(company, icp)
            if apollo:
                dm = email_finder.DecisionMaker(
                    name=f"{apollo.get('first_name', '')} {apollo.get('last_name', '')}".strip(),
                    title=apollo.get("title", ""),
                    email=apollo.get("email", ""),
                    source=apollo.get("source", "apollo.io"),
                )
            else:
                dm = email_finder.lookup(
                    company_name=company,
                    website=contact.website,
                    icp_category=icp,
                )

        row = [
            datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M"),
            platform_label,
            post.subreddit or "",
            post.url,
            post.author,
            post.title,
            analysis.relevance_score,
            getattr(analysis, "lead_score", ""),
            getattr(analysis, "icp_category", ""),
            getattr(analysis, "business_type", "unknown"),
            getattr(analysis, "pain_point_description", ""),
            getattr(analysis, "why_it_fits", ""),
            analysis.urgency,
            "Yes" if getattr(analysis, "is_decision_maker", True) else "No",
            getattr(analysis, "competitor_mentioned", "") or "No",
            "Yes" if getattr(analysis, "is_job_posting", False) else "No",
            contact.phone,
            contact.website,
            dm.name,
            dm.title,
            dm.email,
            analysis.reasoning,
            "",  # Status — user fills in
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[sheets] Logged: {post.title[:60]}...")
        return True
    except Exception as e:
        print(f"[sheets] Failed to log post {post.id}: {e}")
        return False


# ── Slack ─────────────────────────────────────────────────────────────────────

_SLACK_BATCH_SIZE = 5
_pending_slack_leads: list[tuple[RawPost, PostAnalysis]] = []


def _score_emoji(score: int) -> str:
    if score >= 85:
        return "🔥"
    if score >= 70:
        return "⭐"
    if score >= 55:
        return "👀"
    return "📌"


def send_slack_alert(post: RawPost, analysis: PostAnalysis) -> bool:
    """Queue a lead for Slack. Fires automatically when 5 leads accumulate."""
    if analysis.relevance_score < MIN_RELEVANCE_FOR_ALERT:
        return False

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("[slack] SLACK_WEBHOOK_URL not set — skipping alert")
        return False

    _pending_slack_leads.append((post, analysis))
    print(
        f"[slack] Queued lead {len(_pending_slack_leads)} "
        f"(score {analysis.relevance_score} | {getattr(analysis, 'icp_category', '')} | {getattr(analysis, 'lead_score', '')})"
    )
    return True


def flush_slack_buffer() -> None:
    """Send any remaining queued leads at the end of a cycle."""
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

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"BrainCX — {count} New Lead{'s' if count > 1 else ''} Found",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{count} new lead{'s have' if count > 1 else ' has'} been logged to Google Sheets. Click below to review.",
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
