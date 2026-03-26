---
name: clawdbot-linkedin
description: "Manages and runs ClawdBot — Rich's LinkedIn Auto Commenter bot. Monitors WhatsApp groups for LinkedIn post URLs, generates contextual comments as Rich Taylor using Claude AI, and posts them to LinkedIn. Use this skill whenever the user wants to start, stop, debug, or configure the bot. Trigger on: 'start the bot', 'run clawdbot', 'start the LinkedIn bot', 'run the LinkedIn commenter', 'start clawdbot', 'run the bot', 'check the bot logs', 'how many comments today', 'debug the bot', 'the bot is broken', 'reset the processed URLs', or any request to manage or troubleshoot the LinkedIn auto-commenting system. The bot lives at: c:/Users/richm/ClawdBot-LinkedIn/"
---

# ClawdBot - LinkedIn Auto Commenter

You are managing ClawdBot, Rich Taylor's LinkedIn engagement bot. It monitors a WhatsApp group for LinkedIn post URLs, generates short comments in Rich's voice using Claude AI, and posts them automatically.

## Project Location

```
c:/Users/richm/ClawdBot-LinkedIn/
├── main.py                 # Orchestrator — start here
├── whatsapp_monitor.py     # WhatsApp Web monitoring via Playwright
├── linkedin_commenter.py   # LinkedIn browser automation
├── claude_generator.py     # Claude API comment generation
├── .env                    # Credentials (ANTHROPIC_API_KEY, LinkedIn login)
├── processed_urls.json     # Tracks already-commented URLs (auto-managed)
├── bot_activity.log        # Live activity log
└── requirements.txt        # Python dependencies
```

## How to Start the Bot

**IMPORTANT — Before running, ask the user:**
> "Do you have a LinkedIn verification code/passcode ready? LinkedIn sometimes asks for one during login. If you have it, share it now and I'll pass it in automatically. If not, no worries — just say 'no code' and we'll proceed without it."

Wait for the user's reply, then run:

```bash
# With a passcode (user provided one):
cd "C:/Users/richm/.claude/skills/clawdbot-linkedin" && LINKEDIN_PASSCODE=<code_from_user> python main.py &

# Without a passcode:
cd "C:/Users/richm/.claude/skills/clawdbot-linkedin" && python main.py &
```

The `&` runs it in the background so it doesn't block. The browser window will appear on screen — that's normal (headless=False).

On first run (or new WhatsApp session), the user must scan the WhatsApp QR code in the browser window. LinkedIn session is persisted in `whatsapp_session/`.

Default WhatsApp group: **LinkedIn B2B Creators**

## Architecture

1. **WhatsApp scan** every 60s — finds new LinkedIn URLs in the group
2. **LinkedIn feed scan** every 60 min — scrapes first 10 new feed posts
3. For each URL: extract post content → generate comment via Claude → like → post comment
4. Delay 45-120s between comments to avoid rate limits
5. Daily limit: configurable via `MAX_COMMENTS_PER_DAY` in `.env` (default 50)

## Rich Taylor Persona (enforced in claude_generator.py)

- Full name: Richmond Taylor (goes by Rich)
- Founder at AI Builders, Miami FL
- Background: European soccer (East Tennessee State University, 2014-2017)
- Focus: AI automation, Claude Code, n8n, community building
- 13K+ LinkedIn followers, runs AI hackathons/meetups in Miami
- **Comments: 10-20 words, fun, conversational, no questions, no em dashes**
- **Never fabricate personal stories or anecdotes**
- Skip own posts (Richmond Taylor / "You")

## Key Technical Rules

- Playwright: uses `domcontentloaded` (NOT `networkidle` — causes timeouts on LinkedIn)
- LinkedIn interactions: use Playwright's native `.click()`, not JS `.click()`
- Comment submit: Ctrl+Enter first (editor focused), button click as fallback
- Shared Playwright instance between LinkedIn and WhatsApp (avoids async conflicts)
- WhatsApp: `launch_persistent_context` for session persistence
- Windows console (cp1252): no Unicode emojis in print statements — use ASCII `[OK]`, `[X]`, `[!]`
- Em dashes are banned in all generated comments

## Common Operations

### Check today's activity
```bash
cat c:/Users/richm/ClawdBot-LinkedIn/bot_activity.log | tail -50
```

### Reset processed URLs (re-process all posts)
Delete or clear `processed_urls.json` — the bot will re-process all previously seen URLs on next run.

### Check processed URL count
```python
import json
with open('processed_urls.json') as f:
    urls = json.load(f)
print(f"{len(urls)} URLs processed")
```

### Change daily comment limit
Edit `.env`:
```
MAX_COMMENTS_PER_DAY=30
```

### Change WhatsApp group
Pass a different group name when prompted at startup, or modify the `default_group` in `main.py:369`.

## Debugging Common Issues

| Symptom | Fix |
|---|---|
| WhatsApp not finding messages | Run `dump_page_diagnostics()` — check group selector |
| LinkedIn timeout on post load | Normal — bot uses `domcontentloaded` and retries |
| Comment not posting | Check `linkedin_post_attempt.png` screenshot |
| Bot exits immediately | Check `.env` for missing `ANTHROPIC_API_KEY` |
| QR code required again | Delete `whatsapp_session/` folder and re-scan |
| UnicodeEncodeError in terminal | Emoji in a print statement — use ASCII only |

## .env Required Variables

```
ANTHROPIC_API_KEY=sk-ant-...
LINKEDIN_EMAIL=...
LINKEDIN_PASSWORD=...
MAX_COMMENTS_PER_DAY=50
CHECK_INTERVAL=60
```

## When Modifying the Bot

- Read the relevant module first before suggesting changes
- The shared Playwright instance pattern is intentional — do not split into separate instances
- Test comment generation changes against `claude_generator.py` in isolation before running the full bot
- Do not add em dashes to any generated comment output — Rich has explicitly banned them
