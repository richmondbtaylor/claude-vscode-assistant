"""
One-time setup for the TARSEN reply history Google Sheet.

Creates a new spreadsheet titled "TARSEN - Reply History" with all required tabs:
  - replies              (main log)
  - control              (kill switch + manual approval flag)
  - seed_accounts        (the 26 confirmed handles)
  - banlist_competitors  (Rich populates)
  - banlist_political    (pre-populated)
  - banlist_phrases      (pre-populated)
  - skipped              (logged when TARSEN skips a tweet)
  - failed_validation    (drafts that failed guardrail checks)
  - kill_log             (logged when kill switch fires)

Reuses the same Google OAuth credentials as the receipt-filer pipeline.
After running, the Sheet ID is printed - paste it into:
  references/reply_history_schema.md

Run once: python setup_sheet.py
"""
import json
import os
import sys
from datetime import datetime

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = os.path.expanduser(r"~\AppData\Roaming\gspread\authorized_user.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_TITLE = "TARSEN - Reply History"

REPLIES_HEADERS = [
    "id", "timestamp_et", "target_handle", "tweet_url", "tweet_text",
    "thread_context", "tweet_type", "reply_style", "reply_text",
    "reply_word_count", "approval_status", "approved_by", "posted_at",
    "likes_received", "replies_received", "profile_clicks", "notes",
]

CONTROL_ROWS = [
    ["setting", "value", "notes"],
    ["run_state", "RUN", "Set to PAUSE to kill all TARSEN workflows instantly. Workflows check this on every run."],
    ["manual_approval", "ON", "ON during week 1. OFF after warm-up. When ON, every draft requires Rich's approval."],
    ["daily_cap_override", "", "Leave blank to use the warm-up schedule. Set an integer to override for today only."],
    ["last_pause_reason", "", "Free text. Set when flipping run_state to PAUSE so future-Rich knows why."],
]

SEED_ACCOUNTS = [
    ["handle", "tier", "topic", "added_at", "active"],
    # Tier 1 - AI thought leaders
    ["alliekmiller", "mega", "Enterprise AI, AI business", "2026-04-07", "TRUE"],
    ["AndrewYNg", "mega", "AI/ML, education", "2026-04-07", "TRUE"],
    ["jeremyphoward", "high", "Practical AI, fast.ai, answer.ai", "2026-04-07", "TRUE"],
    # Tier 2 - GTM/RevOps
    ["kazanjy", "mid", "Founder-led sales, Modern Sales Pros", "2026-04-07", "TRUE"],
    ["kyleporter", "high", "Sales engagement, Salesloft", "2026-04-07", "TRUE"],
    ["kieranflanagan", "high", "B2B marketing, HubSpot, AI in GTM", "2026-04-07", "TRUE"],
    ["jillkonrath", "mid", "Sales strategy, B2B selling", "2026-04-07", "TRUE"],
    ["markroberge", "mid", "GTM science, Stage 2 Capital", "2026-04-07", "TRUE"],
    ["motoceo", "mid", "Predictable Revenue, outbound", "2026-04-07", "TRUE"],
    ["jasonlk", "high", "SaaS, SaaStr, founder advice", "2026-04-07", "TRUE"],
    ["davegerhardt", "high", "B2B marketing, Exit Five", "2026-04-07", "TRUE"],
    ["ChrisWalker171", "high", "Demand gen, GTM strategy, Passetto", "2026-04-07", "TRUE"],
    ["kylecnorton", "mid", "Revenue leadership, Owner.com CRO", "2026-04-07", "TRUE"],
    ["ttunguz", "high", "SaaS data, AI investing, Theory Ventures", "2026-04-07", "TRUE"],
    ["nrmehta", "mid", "Customer success, Gainsight", "2026-04-07", "TRUE"],
    ["SVMansuri", "mid", "Sales community, Bravado", "2026-04-07", "TRUE"],
    ["Jacco_vd_Kooij", "mid", "Revenue architecture, Winning by Design", "2026-04-07", "TRUE"],
    ["pc4media", "mid", "Marketing analytics, Databox", "2026-04-07", "TRUE"],
    # Tier 3 - B2B AI tooling founders
    ["kareemamin", "mid", "Clay, growth automation", "2026-04-07", "TRUE"],
    ["RetentionAdam", "high", "RB2B, person-level visitor ID", "2026-04-07", "TRUE"],
    ["WillAllred117", "mid", "Lavender, AI cold email", "2026-04-07", "TRUE"],
    ["kyletcoleman", "mid", "GTM AI, Copy.ai", "2026-04-07", "TRUE"],
    ["LindaMLian", "mid", "Common Room, signal-based GTM", "2026-04-07", "TRUE"],
    ["austinh___", "mid", "Unify, warm outbound", "2026-04-07", "TRUE"],
    ["banditmove", "high", "Gong, revenue intelligence", "2026-04-07", "TRUE"],
    ["Patticus", "high", "Pricing, SaaS metrics, ProfitWell/Paddle", "2026-04-07", "TRUE"],
]

BANLIST_PHRASES = [
    ["banned_phrase", "reason"],
    ["Great point", "Generic agreement opener - kills authenticity"],
    ["Love this", "Generic agreement opener"],
    ["100%", "Generic agreement opener"],
    ["This!", "Generic agreement opener"],
    ["So true", "Generic agreement opener"],
    ["Absolutely", "Generic agreement opener"],
    ["Couldn't agree more", "Generic agreement opener"],
    ["Nailed it", "Generic agreement opener"],
    ["Spot on", "Generic agreement opener"],
    ["Well said", "Generic agreement opener"],
    ["Hot take", "Hype word - feels low-effort"],
    ["Game changer", "Hype word"],
    ["Mind blown", "Hype word"],
    ["—", "Em dash - Rich's standing rule, never use"],
]

BANLIST_POLITICAL = [
    ["banned_keyword", "reason"],
    ["trump", "Political - hard skip per Rich's spec"],
    ["biden", "Political - hard skip"],
    ["election", "Political - hard skip"],
    ["abortion", "Political - hard skip"],
    ["israel", "Political - hard skip"],
    ["palestine", "Political - hard skip"],
    ["gaza", "Political - hard skip"],
    ["ukraine", "Political - hard skip"],
    ["religion", "Religious - hard skip"],
    ["christian", "Religious - hard skip"],
    ["muslim", "Religious - hard skip"],
    ["jewish", "Religious - hard skip"],
    ["doomer", "Doomer rhetoric - hard skip per spec"],
    ["AI will kill", "Doomer rhetoric"],
    ["replace humans", "Per Rich's standing rule - never engage with humans-replaced framing"],
    ["fire your", "Per Rich's standing rule - never encourage firing people"],
]

BANLIST_COMPETITORS = [
    ["competitor_name", "reason"],
    # Rich populates - leave with header only
]


def get_credentials():
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def main():
    creds = get_credentials()
    gc = gspread.authorize(creds)

    # Check if it already exists
    try:
        existing = gc.open(SHEET_TITLE)
        print(f"Sheet '{SHEET_TITLE}' already exists.")
        print(f"Sheet ID: {existing.id}")
        print(f"URL: https://docs.google.com/spreadsheets/d/{existing.id}/")
        return existing.id
    except gspread.SpreadsheetNotFound:
        pass

    # Create the spreadsheet
    spreadsheet = gc.create(SHEET_TITLE)
    print(f"Created spreadsheet: {SHEET_TITLE}")
    print(f"Sheet ID: {spreadsheet.id}")

    # The default first sheet is "Sheet1" - rename it to "replies"
    default_ws = spreadsheet.sheet1
    default_ws.update_title("replies")
    default_ws.append_row(REPLIES_HEADERS)
    print("Tab 'replies' created with headers.")

    # control
    ws = spreadsheet.add_worksheet(title="control", rows=20, cols=5)
    for row in CONTROL_ROWS:
        ws.append_row(row)
    print("Tab 'control' created and populated.")

    # seed_accounts
    ws = spreadsheet.add_worksheet(title="seed_accounts", rows=100, cols=6)
    for row in SEED_ACCOUNTS:
        ws.append_row(row)
    print("Tab 'seed_accounts' created and populated with 26 handles.")

    # banlist_phrases
    ws = spreadsheet.add_worksheet(title="banlist_phrases", rows=100, cols=3)
    for row in BANLIST_PHRASES:
        ws.append_row(row)
    print("Tab 'banlist_phrases' created and populated.")

    # banlist_political
    ws = spreadsheet.add_worksheet(title="banlist_political", rows=100, cols=3)
    for row in BANLIST_POLITICAL:
        ws.append_row(row)
    print("Tab 'banlist_political' created and populated.")

    # banlist_competitors (header only)
    ws = spreadsheet.add_worksheet(title="banlist_competitors", rows=100, cols=3)
    for row in BANLIST_COMPETITORS:
        ws.append_row(row)
    print("Tab 'banlist_competitors' created (header only - Rich populates).")

    # skipped
    ws = spreadsheet.add_worksheet(title="skipped", rows=1000, cols=5)
    ws.append_row(["timestamp_et", "tweet_url", "skip_reason", "target_handle", "notes"])
    print("Tab 'skipped' created.")

    # failed_validation
    ws = spreadsheet.add_worksheet(title="failed_validation", rows=1000, cols=6)
    ws.append_row(["timestamp_et", "tweet_url", "draft_text", "failed_check", "details", "notes"])
    print("Tab 'failed_validation' created.")

    # kill_log
    ws = spreadsheet.add_worksheet(title="kill_log", rows=200, cols=4)
    ws.append_row(["timestamp_et", "workflow", "trigger_reason", "notes"])
    print("Tab 'kill_log' created.")

    print()
    print("=" * 60)
    print(f"DONE. Sheet ID: {spreadsheet.id}")
    print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/")
    print("=" * 60)
    print()
    print("Next: paste the Sheet ID into references/reply_history_schema.md")
    return spreadsheet.id


if __name__ == "__main__":
    main()
