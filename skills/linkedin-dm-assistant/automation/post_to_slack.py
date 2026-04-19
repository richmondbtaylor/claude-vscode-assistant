"""Post LinkedIn DM drafts to Slack #human-in-the-loop with Send/Skip buttons."""
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "linkedin-dm-assistant.env")
SLACK_TOKEN = os.getenv('SLACK_BOT_TOKEN')
CHANNEL = os.getenv('SLACK_CHANNEL_ID', 'C0AP1AU3109')

def post_dm(name, company, fit, rec, profile_summary, draft, thread_url, notes="None", priority=False):
    flag = " ⚡" if priority else ""
    draft_block = "\n".join(f">{line}" for line in draft.split("\n") if line.strip())
    send_val = json.dumps({"conversation_url": thread_url, "message": draft, "sender_name": name})
    skip_val = json.dumps({"conversation_url": thread_url, "message": "", "sender_name": name})

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn",
            "text": f"*New LinkedIn DM — {name} @ {company}*{flag}\n\n*Fit:* {fit}\n*Rec:* {rec}\n\n*Profile:* {profile_summary}\n\n*Draft:*\n{draft_block}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Notes:* {notes}"}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "✅ Send it"},
             "style": "primary", "action_id": "approve_dm", "value": send_val},
            {"type": "button", "text": {"type": "plain_text", "text": "⏭️ Skip"},
             "style": "danger", "action_id": "skip_dm", "value": skip_val}
        ]}
    ]

    resp = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"},
        json={"channel": CHANNEL, "blocks": blocks, "text": f"LinkedIn DM: {name}"})
    r = resp.json()
    status = "✅" if r.get('ok') else f"❌ {r.get('error')}"
    print(f"{status} {name}")

# ── THE DMS ────────────────────────────────────────────────────────────────────

post_dm(
    name="Jason Lopez", company="Scale Miami",
    fit="Not a sales thread — event tonight",
    rec="Send ⚡ URGENT — event is tonight",
    profile_summary="AI community builder in Miami, runs AI Builders events.",
    draft="Yes sir, 6pm! See you there.",
    thread_url="https://www.linkedin.com/messaging/thread/2-NWMxYTUzZmMtYTk3My00YWI3LWJmY2UtN2M4NmU0NGUxMDc1XzEwMA==/",
    notes="He confirmed he's ready. Event tonight March 26 at 6pm.",
    priority=True
)

post_dm(
    name="Dmitry Kotov", company="Conference (Miami April 11)",
    fit="Not a sales thread — speaking invitation",
    rec="Send — he's asking you to check WhatsApp",
    profile_summary="Organizing an investor/entrepreneur conference in Miami, April 11, ~200 guests. Invited Rich as speaker.",
    draft="Checked WhatsApp! Will respond there.",
    thread_url="https://www.linkedin.com/messaging/thread/2-ZGE1NjAyODAtMjFjYS00MjcwLWFiYzQtZTUwMmVkMzNjMzdmXzEwMA==/",
    notes="Rich already filled out the speaker form. Dmitry said 'check whatsapp' — needs acknowledgment."
)

post_dm(
    name="Marijana Nedevska", company="Warmly",
    fit="Not a fit — sells AI for revenue teams (competitor-adjacent)",
    rec="Engage warmly, no pitch back",
    profile_summary="Works at Warmly — AI agents for revenue teams (inbound + proactive). Sent a casual opener then pitched.",
    draft="Haha the deer thing is very on-brand for LinkedIn. And Macedonian — that's a first for me! Appreciate the Warmly context too. Sounds like we're both in the AI-for-sales world from different angles. Would love to swap notes sometime.",
    thread_url="https://www.linkedin.com/messaging/thread/2-ZDVmZjAzZDQtNTM3NC00MGNiLTljMmQtZmI3YmE2M2Q2YzU5XzAxMg==/",
    notes="She started casual/playful, ended with a Warmly pitch. Not a prospect — engage but don't pitch."
)

post_dm(
    name="Clinton Rex Stebbing", company="OnviSource",
    fit="Possible competitor — AI Transformation company, US vendor for Contact Centres",
    rec="Engage — possible collaboration, flag competitor risk",
    profile_summary="Works at OnviSource, a US AI Transformation business serving Contact Centres globally. Based in South Africa.",
    draft="Eastern time here — Miami. Will grab time on your calendar and we can dig into where we overlap. The contact centre AI space is moving fast.",
    thread_url="https://www.linkedin.com/messaging/thread/2-MjQ1YTEwZGMtZWEzYy00ZGU5LTkyYTctOTE2YTliYWJhYWVkXzEwMA==/",
    notes="He works for a US AI vendor targeting global Contact Centres. May be a competitor. He shared a booking link — consider booking his calendar."
)

post_dm(
    name="Mathiyazhahan Maheswaran", company="Commerce/Retail",
    fit="Possibly — retail/commerce companies use automation",
    rec="Send — warm close + light qualifier",
    profile_summary="Commerce and retail professional. Friendly, brief exchange.",
    draft="Will do! Always good to have retail/commerce folks in the network. What's keeping you busy these days — any interesting projects?",
    thread_url="https://www.linkedin.com/messaging/thread/2-NzgxMmEyYTYtYWYyYi00ZDQxLWFkZjUtMThlYTI4ZDdiZWM3XzEwMA==/",
    notes="Short thread, closed with 'Please keep in touch.' Worth a light qualifier to understand his role/company size."
)

post_dm(
    name="Harsh Kumar", company="Web/App Dev Services",
    fit="Not a fit — vendor spam",
    rec="Skip recommended — mass outreach",
    profile_summary="Offers web and app development services. Sent a generic pitch twice.",
    draft="Appreciate the message, Harsh. Not in the market for dev services right now. Best of luck!",
    thread_url="https://www.linkedin.com/messaging/thread/2-Y2U1MjkxYTYtYTY0OC00N2E5LThjNzctNjZkNmU2OWZjZDAwXzEwMA==/",
    notes="Classic vendor spam. Recommend Skip — no engagement value."
)

post_dm(
    name="Brady Kirby, A-CSPO", company="Unknown",
    fit="Unclear — responded to Rich's engagement with a template pitch",
    rec="Skip unless you know what they shared",
    profile_summary="Agile/product professional (A-CSPO). Sent 'Here you go, thanks for the engagement!' — unclear what was shared.",
    draft="What did you send over? Happy to take a look.",
    thread_url="https://www.linkedin.com/messaging/thread/2-ODBjMzQxYjEtN2ZmYi00Y2U4LThmZDItZDZjYjc0NjFiYjMzXzEwMA==/",
    notes="Template-style message. No context on what 'here you go' refers to."
)

post_dm(
    name="Prerona Basu", company="LinkedIn Automation",
    fit="Possible competitor — does LinkedIn automation for B2B clients",
    rec="Send — reference the real referral conversation, ignore the template at end",
    profile_summary="Helps B2B clients get more clients through LinkedIn automation. Met via a WhatsApp LinkedIn group.",
    draft="Still curious about the referral structure when you get a chance to circle back — genuinely might have someone for you.",
    thread_url="https://www.linkedin.com/messaging/thread/2-OGRjOTg4MjUtZjFmMy00OTZmLTgzMTQtODdlYWVjYmM4MWZiXzEwMA==/",
    notes="Had a real conversation about referrals, then got a template follow-up. Adjacent space (LinkedIn automation) — not a direct competitor to Bishop AI's custom agent work."
)

print("\nDone!")
