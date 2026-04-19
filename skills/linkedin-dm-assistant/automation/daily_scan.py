"""
Daily LinkedIn DM scanner — runs at 9am EST via Task Scheduler.
Fetches pending DMs, drafts responses via Claude, posts to Slack for approval.
"""
import os
import json
import sys
import requests
import anthropic
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure correct working directory so cookies file resolves
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "linkedin-dm-assistant.env")

from fetch_dms import fetch_pending_dms

SLACK_TOKEN = os.getenv('SLACK_BOT_TOKEN')
CHANNEL = os.getenv('SLACK_CHANNEL_ID', 'C0AP1AU3109')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')

SYSTEM_PROMPT = """You are a LinkedIn DM ghostwriter for Rich at Bishop AI.

Bishop AI builds custom AI agents and automations. Helps businesses save 10-20 hours/week on repetitive work using Claude and n8n. Discovery calls: https://cal.com/bishopai.io/15min

TONE: Smart, friendly colleague. Short messages — 1-3 sentences max. Never use template language.

WHO TO PITCH: Founders, CEOs, ops leaders at 10-100 employee service businesses, agencies, SaaS.
DO NOT PITCH: AI agencies, automation consultants, job seekers, recruiters.

Messages where [ME] sent the last message should be SKIPPED.

Respond ONLY with valid JSON — no markdown, no explanation:
{
  "fit": "Good fit" | "Possible competitor" | "Not a fit",
  "rec": "Send" | "Wait" | "Skip",
  "profile_summary": "1-2 sentences on who this person is",
  "draft": "The reply to send — conversational, short",
  "notes": "Any flags or just 'None'"
}"""


def draft_response(thread):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    messages_text = "\n".join(
        f"{'[ME]' if m['is_me'] else '[THEM]'}: {m['text']}"
        for m in thread['messages']
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Sender: {thread['sender_name']}\n\nConversation:\n{messages_text}"}]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def post_to_slack(thread, analysis):
    name = thread['sender_name']
    url = thread['thread_url']
    fit = analysis.get('fit', 'Unknown')
    rec = analysis.get('rec', 'Wait')
    profile = analysis.get('profile_summary', '')
    draft = analysis.get('draft', '')
    notes = analysis.get('notes', 'None')
    priority = fit == 'Good fit' and rec == 'Send'

    flag = " (PRIORITY)" if priority else ""
    draft_block = "\n".join(f">{line}" for line in draft.split("\n") if line.strip())
    send_val = json.dumps({"conversation_url": url, "message": draft, "sender_name": name})
    skip_val = json.dumps({"conversation_url": url, "message": "", "sender_name": name})

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn",
            "text": f"*New LinkedIn DM \u2014 {name}*{flag}\n\n*Fit:* {fit}\n*Rec:* {rec}\n\n*Profile:* {profile}\n\n*Draft:*\n{draft_block}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Notes:* {notes}"}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Send it"},
             "style": "primary", "action_id": "approve_dm", "value": send_val},
            {"type": "button", "text": {"type": "plain_text", "text": "Skip"},
             "style": "danger", "action_id": "skip_dm", "value": skip_val}
        ]}
    ]
    resp = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"},
        json={"channel": CHANNEL, "blocks": blocks, "text": f"LinkedIn DM: {name}"})
    return resp.json().get('ok', False)


DM_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_activity.jsonl")


def append_dm_log(entry):
    with open(DM_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    print("=== Bishop AI Daily LinkedIn DM Scan ===")
    print("Fetching pending threads...")
    try:
        threads = fetch_pending_dms()
    except Exception as e:
        print(f"ERROR fetching DMs: {e}")
        sys.exit(1)

    print(f"Found {len(threads)} threads needing a reply")
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not threads:
        append_dm_log({"timestamp": scan_time, "event": "scan", "threads_found": 0})
        sys.exit(0)

    posted = 0
    for thread in threads:
        name = thread['sender_name']
        print(f"Drafting for {name}...", end=" ", flush=True)
        log_entry = {
            "timestamp": scan_time,
            "sender": name,
            "thread_url": thread.get("thread_url", ""),
            "fit": None,
            "rec": None,
            "draft_preview": None,
            "posted_to_slack": False,
            "error": None,
        }
        try:
            analysis = draft_response(thread)
            ok = post_to_slack(thread, analysis)
            print(f"{'OK' if ok else 'SLACK FAIL'} | {analysis.get('rec')} | {analysis.get('fit')}")
            log_entry.update({
                "fit": analysis.get("fit"),
                "rec": analysis.get("rec"),
                "draft_preview": (analysis.get("draft") or "")[:120],
                "posted_to_slack": ok,
            })
            if ok:
                posted += 1
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            log_entry["error"] = f"JSON parse: {e}"
        except Exception as e:
            print(f"ERROR: {e}")
            log_entry["error"] = str(e)
        finally:
            append_dm_log(log_entry)

    print(f"\nDone. {posted}/{len(threads)} posted to #human-in-the-loop.")
