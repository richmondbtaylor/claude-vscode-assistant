# Bishop AI Research Agent — Setup Guide

## What this agent does
Continuously monitors Reddit, LinkedIn, Quora, Twitter/X, and the web for people
asking for AI automation help or showing buying intent. Claude Sonnet 4.6 scores
each post (0–100), classifies intent, checks if they're a decision maker and can
afford services, extracts pain points, and drafts a suggested reply.
Leads are batched and sent to Slack in groups of 5, and logged to Google Sheets.

---

## Quick start (already configured)

```bash
cd C:\Users\richm\bishop-research-agent
venv\Scripts\activate

# One-time test pass (all sources)
python main.py --once

# Run continuously (Reddit every 15 min, Web/LinkedIn/Twitter every 1 hour)
python main.py
```

---

## First-time setup (if starting fresh)

### 1. Install dependencies
```bash
cd bishop-research-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure .env
```
ANTHROPIC_API_KEY=sk-ant-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
GOOGLE_OAUTH_CREDENTIALS=./client_secret_....json
GOOGLE_SHEET_ID=your_sheet_id_here
```

### 3. Authorize Google Sheets (one-time, opens browser)
```bash
python setup_sheets.py
```

### 4. Test then run
```bash
python main.py --once   # single pass to verify
python main.py          # continuous mode
```

---

## Run flags

| Flag | What it does |
|---|---|
| *(none)* | Runs continuously — Reddit every 15 min, Web every 1 hour |
| `--once` | Single pass through all sources then exits |
| `--reddit-only` | Reddit RSS only |
| `--web-only` | LinkedIn / Quora / Twitter / Web only |

---

## Tuning (config.py)

| Setting | Default | What it does |
|---|---|---|
| `MIN_RELEVANCE_FOR_ALERT` | 50 | Slack alert threshold |
| `MIN_RELEVANCE_FOR_SHEETS` | 40 | Sheets logging threshold |
| `REDDIT_POLL_INTERVAL_MINUTES` | 15 | How often to check Reddit |
| `WEB_POLL_INTERVAL_HOURS` | 1 | How often to check web sources |
| `REDDIT_SUBREDDITS` | 29 subs | Which communities to monitor |
| `REDDIT_KEYWORDS` | 20+ phrases | What to look for in Reddit posts |
| `WEB_SEARCH_QUERIES` | 30+ queries | DuckDuckGo queries for LinkedIn/Quora/Twitter/web |
| `BISHOP_AI_CONTEXT` | — | Description of Bishop AI fed to Claude |

---

## Google Sheets columns

| Column | Description |
|---|---|
| Timestamp | When the agent found the post |
| Platform | Reddit, LinkedIn, Twitter, Quora, etc. |
| URL | Link to the original post |
| Author | Username or profile name |
| Title / Snippet | First 120 chars of the post |
| Relevance Score | 0–100 from Claude Sonnet 4.6 |
| Intent Type | ai_automation_help / ai_education / ai_prompting_help / purchase_intent / pain_expressing |
| Urgency | high / medium / low |
| Decision Maker | Yes / No — does this person have buying authority? |
| Budget Tier | can_afford / uncertain / budget_limited |
| Pain Points | Specific problems the author described |
| Budget Signals | Phrases Claude used to assess affordability |
| Suggested Reply | Claude's draft response to the post |
| Should Contact | Yes / No |
| **Status** | **You fill this in** (e.g. "Contacted", "Pass", "Replied") |

---

## Running as a background service (Windows)

Keep a log file and run on startup via Task Scheduler:

```bash
# Run with logging
python main.py >> logs\agent.log 2>&1
```

Task Scheduler setup:
1. Open Task Scheduler → Create Basic Task
2. Trigger: "When the computer starts" (or daily at a set time)
3. Action: Start a program
   - Program: `C:\Users\richm\bishop-research-agent\venv\Scripts\python.exe`
   - Arguments: `C:\Users\richm\bishop-research-agent\main.py`
   - Start in: `C:\Users\richm\bishop-research-agent`
