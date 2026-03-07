---
name: bishop-research-agent
description: Manage, run, troubleshoot, or modify the Bishop AI Research Agent — a Python agent that monitors Reddit, LinkedIn, Quora, Twitter/X, and the web for AI automation leads. Use this skill when the user asks to run the agent, change keywords, add subreddits, adjust thresholds, fix errors, view leads, update the Google Sheet, or make any changes to how the agent finds or scores leads.
---

# Bishop AI Research Agent

A continuously running lead intelligence agent that monitors social platforms for people actively seeking AI automation, education, or prompting help. Claude Sonnet 4.6 scores each post, classifies intent, checks for decision-maker status and budget signals, then sends batched alerts to Slack and logs everything to Google Sheets.

---

## Project Location

```
C:\Users\richm\bishop-research-agent\
```

---

## How to Run

```bash
cd C:\Users\richm\bishop-research-agent
venv\Scripts\activate

python main.py --once        # Single pass through all sources (Reddit + Web)
python main.py --once --reddit-only   # Reddit only
python main.py --once --web-only      # LinkedIn / Quora / Twitter / Web only
python main.py               # Continuous mode (Reddit every 15 min, Web every 1 hour)
```

**Scheduled:** Windows Task Scheduler runs `run-daily.bat` at 8:00 AM daily.
Logs are written to `logs\agent.log`.

---

## Architecture

```
main.py              Orchestrator — schedules cycles, runs the pipeline
config.py            All tunable settings (keywords, subreddits, thresholds)
analyzer.py          Claude Sonnet 4.6 lead scoring and intent classification
reddit_monitor.py    Reddit via public RSS feeds (no API key needed)
web_monitor.py       DuckDuckGo search (LinkedIn, Quora, Twitter/X, forums, web)
linkedin_monitor.py  LinkedIn-specific DuckDuckGo searches
notifier.py          Google Sheets logging + Slack batch digest
storage.py           SQLite deduplication (seen_posts.db)
setup_sheets.py      One-time Google OAuth authorization
update_sheet_headers.py  One-time script to update Sheet header row
run-daily.bat        Windows Task Scheduler entry point
```

---

## Key Configuration (config.py)

| Setting | Default | What it controls |
|---|---|---|
| `REDDIT_SUBREDDITS` | 29 subs | Which communities to monitor |
| `REDDIT_KEYWORDS` | 20+ phrases | Keyword filter for Reddit posts |
| `WEB_SEARCH_QUERIES` | 36 queries | DuckDuckGo queries (LinkedIn/Quora/Twitter/web) |
| `MIN_RELEVANCE_FOR_ALERT` | 50 | Minimum score to queue for Slack |
| `MIN_RELEVANCE_FOR_SHEETS` | 40 | Minimum score to log to Sheets |
| `LOG_ALL_TO_SHEETS` | True | If True, logs everything regardless of score |
| `REDDIT_POLL_INTERVAL_MINUTES` | 15 | Reddit cycle frequency |
| `WEB_POLL_INTERVAL_HOURS` | 1 | Web cycle frequency |
| `BISHOP_AI_CONTEXT` | — | Description of Bishop AI fed to Claude |

---

## Claude Scoring System (analyzer.py)

### Relevance Score (0–100)
- **90–100** — Explicitly asking for AI automation help, mentions budget, seeking agency
- **70–89** — Struggling with a problem Bishop AI solves, asking for tool recs
- **50–69** — Tangentially related, discussing AI automation
- **30–49** — Curious / educational, not a near-term buyer
- **0–29** — Not relevant, competitor, or already solved

### Intent Types
- `ai_automation_help` — Needs help building/managing AI workflows (n8n, Zapier, Make, GPT pipelines)
- `ai_education` — Wants training, workshops, or coaching on AI tools
- `ai_prompting_help` — Needs better prompts or help using ChatGPT/Claude effectively
- `purchase_intent` — Clear buying signals: budget, hire, quote, agency comparison
- `pain_expressing` — Frustrated about a problem Bishop AI solves, not yet asking for help
- `competitor` — Post is from a competing agency or freelancer
- `not_relevant` — Doesn't fit Bishop AI's services

### Additional Signals
- **already_solved** — Post is a tutorial, success announcement, or solved problem → score 0–15, no contact
- **is_decision_maker** — Owner, founder, CEO, manager with buying authority
- **budget_tier** — `can_afford` | `uncertain` | `budget_limited`

---

## Google Sheets Columns (18 total)

| Column | Description |
|---|---|
| Timestamp | Date/time found (MM/DD/YYYY HH:MM) |
| Platform | Reddit, LinkedIn, Twitter, Quora, Web |
| Subreddit | Which subreddit (Reddit only) |
| URL | Link to original post |
| Author | Username or name |
| Title / Snippet | First 120 chars of the post |
| Relevance Score | 0–100 from Claude |
| Intent Type | One of the 7 intent categories above |
| Urgency | high / medium / low |
| Decision Maker | Yes / No |
| Budget Tier | can_afford / uncertain / budget_limited |
| Already Solved | Yes / No |
| Pain Points | Pipe-separated list of specific problems |
| Budget Signals | Phrases that informed the budget assessment |
| Suggested Reply | Claude's draft response (2–4 sentences) |
| Should Contact | Yes / No |
| Claude Reasoning | 1–2 sentence explanation of the score |
| Status | **User fills in** — "Contacted", "Pass", "Replied", etc. |

Sheet ID: `15PVXkBIr4Xqa2k3dWtygsUjLfXw47wSxhxfyDmw_B_E`
Sheet name: `VS Code <> Research Agent` → Worksheet: `Leads`

---

## Slack Output

Leads are **batched in groups of 5** before sending. Each batch digest includes:
- Header with lead count
- "Open Google Sheet" button
- Per-lead: score, intent, urgency, contact recommendation, decision maker, budget tier, author, pain points, suggested reply, "View Post" button

Slack only receives leads scoring ≥ 50. At the end of each cycle, any remaining queued leads (fewer than 5) are flushed automatically.

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
GOOGLE_OAUTH_CREDENTIALS=./client_secret_....json
GOOGLE_SHEET_ID=15PVXkBIr4Xqa2k3dWtygsUjLfXw47wSxhxfyDmw_B_E
```

Google OAuth token is cached at `~/.config/gspread/authorized_user.json` after first run.

---

## Common Tasks

### Add a new subreddit to monitor
Edit `REDDIT_SUBREDDITS` in `config.py`.

### Add a new keyword to search for on Reddit
Edit `REDDIT_KEYWORDS` in `config.py`.

### Add a new web search query (LinkedIn, Twitter, Quora, etc.)
Edit `WEB_SEARCH_QUERIES` in `config.py`. Use natural language — `site:` operators don't work programmatically with DuckDuckGo. Use `-site:reddit.com` to exclude Reddit.

### Lower or raise the Slack alert threshold
Change `MIN_RELEVANCE_FOR_ALERT` in `config.py`.

### Reset deduplication (re-process all posts)
```bash
cd C:\Users\richm\bishop-research-agent
del seen_posts.db
```

### Update Google Sheet headers after adding columns
```bash
python update_sheet_headers.py
```

### Re-authorize Google Sheets (if token expires)
```bash
python setup_sheets.py
```

### Check the Task Scheduler job
```powershell
powershell -Command "schtasks /query /tn 'BishopAI Research Agent' /fo LIST"
```

### Change the scheduled run time (e.g., 9 AM instead of 8 AM)
```powershell
powershell -Command "schtasks /change /tn 'BishopAI Research Agent' /st 09:00"
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ANTHROPIC_API_KEY` not found | Check `.env` file exists and `load_dotenv()` runs before imports |
| `UnicodeEncodeError` on Windows | `sys.stdout.reconfigure(encoding="utf-8")` is in main.py — already fixed |
| `ddgs` import error | `pip install ddgs` — the package was renamed from `duckduckgo_search` |
| Google Sheets auth error | Run `python setup_sheets.py` to re-authorize |
| 0 results from web monitor | DuckDuckGo rate limit — increase `_REQUEST_DELAY` in web_monitor.py |
| Slack not receiving alerts | Check score threshold (50+), check `SLACK_WEBHOOK_URL` in `.env` |
| SQLite ResourceWarning | Already fixed — storage.py uses context manager with `finally: conn.close()` |
| JSON parse error from Claude | Claude returned markdown — stripping is handled in analyzer.py |

---

## File Map (quick reference)

- `config.py` — Edit this to tune keywords, subreddits, thresholds, and Bishop AI context
- `analyzer.py` — Edit this to change Claude's scoring logic, intent types, or add new fields
- `notifier.py` — Edit this to change Slack formatting, Sheets columns, or batch size
- `main.py` — Edit this to change the pipeline, add new sources, or adjust scheduling
- `reddit_monitor.py` — Reddit RSS polling and keyword filtering
- `web_monitor.py` — DuckDuckGo multi-platform search
- `storage.py` — SQLite deduplication — touch only if adding new tables
- `seen_posts.db` — SQLite database — delete to reset dedup history
- `logs/agent.log` — Daily run logs from Task Scheduler
