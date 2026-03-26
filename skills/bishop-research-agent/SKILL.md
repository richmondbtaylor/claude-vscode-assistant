---
name: bishop-research-agent
description: Manage, run, troubleshoot, or modify the Bishop AI Research Agent — a Python agent that monitors Reddit, n8n Community Jobs, and the web for AI automation and prompting leads. Use this skill when the user asks to run the agent, change keywords, add subreddits, adjust thresholds, fix errors, view leads, update the Google Sheet, run the reply agent, or make any changes to how the agent finds or scores leads.
---

# Bishop AI Research Agent

A daily lead intelligence agent that monitors Reddit, n8n Community Jobs, LinkedIn, Facebook, Twitter/X, and the web (via Brave Search with DuckDuckGo fallback) for people actively seeking AI automation, education, or prompting help. Claude Sonnet 4.6 scores each post, classifies intent, checks for decision-maker status and budget signals, then sends batched alerts to Slack and logs qualifying leads to Google Sheets.

An auto-reply agent (`reply_agent.py`) then reads qualifying leads from the sheet and sends comments + DMs on behalf of Bishop AI across Reddit (PRAW API), n8n Community (Playwright/Discourse), LinkedIn (Playwright), and Facebook (assisted/clipboard).

---

## Project Location

```
C:\Users\richm\.claude\skills\bishop-research-agent\
```

---

## How to Run

```bash
cd /c/Users/richm/.claude/skills/bishop-research-agent
source venv/Scripts/activate   # bash syntax (not venv\Scripts\activate)

python main.py --once              # Full pass (Reddit + Brave/Web + n8n jobs)
python main.py --once --reddit-only
python main.py --once --web-only

python reply_agent.py              # Send replies to all pending leads
python reply_agent.py --dry-run    # Preview without posting
python reply_agent.py --limit 5    # Process at most 5 leads
```

**Scheduled:** Windows Task Scheduler runs `run-daily.bat` at **7:00 AM EST** daily (`--once` mode only — does NOT run continuously).

**To run manually:** use `python main.py --once` or ask Claude Code to run it.

---

## Architecture

```
main.py                Orchestrator — runs the pipeline in --once mode
config.py              All tunable settings (keywords, subreddits, thresholds, sheet columns)
analyzer.py            Claude Sonnet 4.6 lead scoring — returns relevance_score + intent_score
reddit_monitor.py      Reddit via public RSS feeds (no API key needed). 7-day filter via published_parsed.
web_monitor.py         DuckDuckGo fallback (used if BRAVE_API_KEY not set). timelimit='w' for 7-day filter.
brave_monitor.py       Brave Search API (preferred over DDG). freshness=pw filters to past week server-side.
n8n_jobs_monitor.py    Scrapes community.n8n.io/c/jobs/ via Discourse JSON API. Runs at end of web cycle.
notifier.py            Logs to Google Sheets + sends Slack batch digests (count + sheet link only, no per-lead detail)
storage.py             SQLite dedup (seen_posts.db). Also tracks authors for cross-platform detection.
reply_agent.py         Auto-reply agent — reads sheet leads, sends comments + DMs across all platforms
setup_reddit_app.py    One-shot Playwright script to create Reddit API app and save credentials to .env
setup_sheets.py        One-time Google OAuth authorization
update_sheet_headers.py  One-time script to update Sheet header row
run-daily.bat          Windows Task Scheduler entry point
```

**Web search also covers:** LinkedIn, Facebook groups, Twitter/X — all via Brave/DDG site: queries.

---

## Key Configuration (config.py)

| Setting | Current Value | What it controls |
|---|---|---|
| `REDDIT_SUBREDDITS` | 47 subs | Which communities to monitor |
| `REDDIT_KEYWORDS` | 50+ phrases | Keyword filter for Reddit posts (includes Prompt Anything signals) |
| `WEB_SEARCH_QUERIES` | 44+ queries | site: operator queries for forums, n8n, OpenAI Community, Make, Zapier, LinkedIn, Facebook, Twitter/X, etc. |
| `MIN_RELEVANCE_FOR_ALERT` | 50 | Minimum score to queue for Slack |
| `MIN_RELEVANCE_FOR_SHEETS` | 50 | Minimum score to log to Sheets |
| `LOG_ALL_TO_SHEETS` | False | Only leads scoring 50+ are logged |
| `REDDIT_POLL_INTERVAL_MINUTES` | 15 | Reddit cycle frequency (continuous mode only) |
| `WEB_POLL_INTERVAL_HOURS` | 1 | Web cycle frequency (continuous mode only) |
| `BISHOP_AI_CONTEXT` | — | Description of Bishop AI + Prompt Anything fed to Claude |

---

## Bishop AI — Two Products to Score For

### Service: AI Automation & Education Agency
- Automate workflows (n8n, Zapier, Make, custom GPT pipelines)
- Build AI chatbots and agents for business operations
- Team training, workshops, AI strategy

**Ideal clients:** SMBs 5–200 employees, agency owners, e-commerce, marketing agencies, professional services. NOT a SaaS/mobile app dev shop.

### Product: Prompt Anything (promptanything.io)
- $15.99/month prompt engineering tool
- Helps people write better prompts for ChatGPT, Claude, Gemini using CRISPE/CLEAR/SOPS/STAR frameworks
- **Ideal customers:** Anyone frustrated that AI gives bad/generic results. Individuals welcome — doesn't need to be a business owner.

---

## Claude Scoring System (analyzer.py)

### Relevance Score (0–100) — fit for Bishop AI
- **90–100** — Real person explicitly asking for AI automation help, mentions budget, or actively seeking an agency RIGHT NOW
- **70–89** — Real person struggling with a problem Bishop AI solves, asking for tool/service recommendation
- **50–69** — Real person tangentially related, discussing AI automation but not clearly looking for help yet
- **30–49** — Real person with curious/educational interest, not a near-term buyer
- **0–15** — Marketing article, blog post, tutorial, directory, aggregator, competitor, news, already-solved problem, or anything NOT written by a real person with an active need

### Intent Score (0–100) — buying intent only
- **90–100** — Actively seeking to hire/buy right now with budget signals
- **70–89** — Strong buying signals but no explicit budget
- **50–69** — Moderate intent (pain is real, solution-seeking)
- **30–49** — Mild interest
- **0–29** — No buying signals at all

### Intent Types
- `ai_automation_help` — Needs help building/managing AI workflows (n8n, Zapier, Make, GPT pipelines)
- `ai_education` — Wants training, workshops, or coaching on AI tools
- `ai_prompting_help` — Struggling with prompts / bad AI outputs → **valid Prompt Anything lead, score 70+ if clearly frustrated**
- `purchase_intent` — Clear buying signals: budget, hire, quote, agency comparison
- `pain_expressing` — Frustrated about a problem Bishop AI solves, not yet asking for help
- `competitor` — Post is from a competing agency or freelancer
- `not_relevant` — Doesn't fit Bishop AI's services

### Disqualifying Content (score 0–10, no contact)
Marketing articles, blog posts, listicles, tutorials, success announcements, past-tense problems, directory/aggregator pages, job board aggregate pages, news articles, academic content, promotional content.

### Additional Signals
- **already_solved** — Solved problem → score 0–15, no contact
- **is_decision_maker** — Owner, founder, CEO, manager with buying authority
- **budget_tier** — `can_afford` | `uncertain` | `budget_limited`
- **cross_platform** — SQLite tracks author names; sheet shows if same author appears on multiple platforms

### Suggested Reply Format
- **2-3 sentences** — specific to the person's situation, not generic
- Acknowledges their exact problem, then explains how Bishop AI solves it
- No filler phrases ("great question", "we can help", "I understand your frustration")
- Always ends with booking link on its own line: `https://cal.com/bishopai.io/15min`
- Example: `Sounds like your n8n workflow is missing an error-handling layer — we build and maintain exactly this kind of automation for agencies. Took a client from 4 hours of manual reporting to 10 minutes last month.\nhttps://cal.com/bishopai.io/15min`

---

## Google Sheets — 20 Columns

| Column | Description |
|---|---|
| Timestamp | Date/time found (MM/DD/YYYY HH:MM UTC) |
| Platform | Reddit, Web, n8n Community, LinkedIn, Facebook, Twitter/X, etc. |
| Subreddit | Which subreddit (Reddit only) |
| URL | Link to original post |
| Author | Username or name |
| Title / Snippet | First 120 chars of the post |
| Relevance Score | 0–100 — fit for Bishop AI |
| Intent Score | 0–100 — buying intent only |
| Cross Platform | Other platforms where this author was seen, or "No" |
| Intent Type | One of the 7 intent categories above |
| Urgency | high / medium / low |
| Decision Maker | Yes / No |
| Budget Tier | can_afford / uncertain / budget_limited |
| Already Solved | Yes / No |
| Pain Points | Pipe-separated list of specific problems |
| Budget Signals | Phrases that informed the budget assessment |
| Suggested Reply | Max 30 chars + booking link (Spartan-laconic) |
| Should Contact | Yes / No |
| Claude Reasoning | 1–2 sentence explanation of the score |
| Status | **User fills in** — "Contacted", "Pass", "Auto-Replied", "Manually Replied", etc. |

**Sheet ID:** `15PVXkBIr4Xqa2k3dWtygsUjLfXw47wSxhxfyDmw_B_E`
**Worksheet:** `Leads`

---

## Slack Output

Leads batch and flush at end of each cycle. Each Slack message contains **only**:
- Header: "Bishop AI — X New Leads Found"
- Body: "X new leads have been logged to Google Sheets. Click below to review."
- Button: "View Leads in Google Sheets" → direct link to sheet

No per-lead detail in Slack. All detail lives in Google Sheets.

---

## Auto-Reply Agent (reply_agent.py)

Reads all leads from Google Sheets where `Should Contact = Yes` and `Status` is blank, then sends the `Suggested Reply` as both a public comment and a DM.

### Platform behavior

| Platform | Method | Comment | DM |
|---|---|---|---|
| Reddit | PRAW (official API — no browser) | `submission.reply()` | `redditor.message()` |
| n8n Community | Playwright/Discourse | `.create` button → `.d-editor-input` | `/new-message?username=` |
| LinkedIn | Playwright | Comment box → Ctrl+Enter | Navigate to profile → Message button |
| Facebook | Assisted (clipboard) | Opens post, copies reply to clipboard, marks "Manually Replied" | Not automated |
| Twitter/X, Other | Manual listing | Prints URL + reply text to terminal | N/A |

### Delays (bot detection avoidance)
- Reddit: 45–120s between comment and DM
- n8n / LinkedIn: 45–120s comment, 60–150s DM
- LinkedIn DM: 90–180s
- All randomized via `random.uniform()`

### Session persistence
Browser sessions saved to `.browser_sessions/` for n8n and LinkedIn — avoids re-login on each run.

### Usage
```bash
python reply_agent.py              # Process all pending leads
python reply_agent.py --dry-run    # Preview without posting
python reply_agent.py --limit 5    # Process at most 5 leads
```

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=         # Claude API — required

# Reddit (PRAW — official API)
REDDIT_CLIENT_ID=          # From reddit.com/prefs/apps — short string under app name
REDDIT_CLIENT_SECRET=      # From reddit.com/prefs/apps — next to "secret" label
REDDIT_USERNAME=           # Your Reddit u/ handle
REDDIT_PASSWORD=           # Your Reddit password

# n8n Community
N8N_COMMUNITY_USERNAME=richmondbishopai
N8N_COMMUNITY_PASSWORD=    # Set this

# LinkedIn
LINKEDIN_USERNAME=richmondbtaylor@gmail.com
LINKEDIN_PASSWORD=         # Set this

# Other
BRAVE_API_KEY=             # Brave Search — preferred web source. Falls back to DuckDuckGo if blank.
SLACK_WEBHOOK_URL=         # Already set
GOOGLE_OAUTH_CREDENTIALS=  # Already set
GOOGLE_SHEET_ID=15PVXkBIr4Xqa2k3dWtygsUjLfXw47wSxhxfyDmw_B_E
```

Google OAuth token cached at `~/.config/gspread/authorized_user.json` after first run.

---

## Common Tasks

### Run the research agent now
```bash
cd /c/Users/richm/.claude/skills/bishop-research-agent && source venv/Scripts/activate && python main.py --once
```

### Run the reply agent (send messages to pending leads)
```bash
cd /c/Users/richm/.claude/skills/bishop-research-agent && source venv/Scripts/activate && python reply_agent.py
```

### Create Reddit API app credentials (one-time setup)
Run `setup_reddit_app.py` in an interactive terminal (not from Claude Code):
```bash
python setup_reddit_app.py
```
Then on `reddit.com/prefs/apps`, find your app: **Client ID** = short string under "personal use script"; **Client Secret** = string next to "secret" label.

### Add a subreddit
Edit `REDDIT_SUBREDDITS` in `config.py`.

### Add a Reddit keyword
Edit `REDDIT_KEYWORDS` in `config.py`.

### Add a web search query
Edit `WEB_SEARCH_QUERIES` in `config.py`. Use `site:` operators (e.g. `site:community.n8n.io`) — DDG handles these well for indexed forums.

### Change the Slack/Sheets score threshold
Change `MIN_RELEVANCE_FOR_ALERT` and/or `MIN_RELEVANCE_FOR_SHEETS` in `config.py`.

### Reset deduplication (reprocess all posts)
```bash
rm /c/Users/richm/bishop-research-agent/seen_posts.db
```

### Clear Google Sheet data (keep headers)
```bash
python -c "import gspread, os; from dotenv import load_dotenv; load_dotenv(); gc=gspread.oauth(credentials_filename=os.environ['GOOGLE_OAUTH_CREDENTIALS']); ws=gc.open_by_key(os.environ['GOOGLE_SHEET_ID']).worksheet('Leads'); rows=len(ws.get_all_values()); ws.delete_rows(2,rows) if rows>1 else None"
```

### Update Google Sheet headers after adding columns
```bash
python update_sheet_headers.py
```

### Re-authorize Google Sheets (if token expires)
```bash
python setup_sheets.py
```

### Check or change the Task Scheduler job
```powershell
powershell -Command "schtasks /query /tn 'BishopAI Research Agent' /fo LIST"
powershell -Command "schtasks /change /tn 'BishopAI Research Agent' /st 07:00"
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ANTHROPIC_API_KEY` not found | Check `.env` exists and `load_dotenv()` runs before imports |
| `UnicodeEncodeError` on Windows | `sys.stdout.reconfigure(encoding="utf-8")` already in main.py |
| `ddgs` import error | `pip install ddgs` — renamed from `duckduckgo_search` |
| Google Sheets auth error | Run `python setup_sheets.py` to re-authorize |
| 0 results from web monitor | DDG rate limit — increase `_REQUEST_DELAY` in web_monitor.py, or add `BRAVE_API_KEY` |
| Brave API returning 0 results | Check key is valid at brave.com/search/api; confirm `BRAVE_API_KEY` is set in `.env` |
| Slack not receiving alerts | Check score threshold (50+), check `SLACK_WEBHOOK_URL` in `.env` |
| JSON parse error from Claude | Claude returned markdown — stripping already handled in analyzer.py |
| n8n jobs monitor errors | community.n8n.io Discourse API may be rate-limiting — check n8n_jobs_monitor.py `_REQUEST_DELAY` |
| Sheet has wrong columns | Run `python update_sheet_headers.py` after any SHEET_COLUMNS change |
| Reddit reply_agent skipped | `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` missing in .env — run setup_reddit_app.py |
| n8n reply_agent login failed | Wrong password for `richmondbishopai` — reset password at community.n8n.io |
| LinkedIn security checkpoint | Playwright opens browser — complete the checkpoint manually, then press Enter |
| Facebook automation blocked | By design — reply_agent copies text to clipboard and marks "Manually Replied" |
| `setup_reddit_app.py` EOFError | Must run in an interactive terminal, not via Claude Code Bash tool |

---

## File Map (quick reference)

- `config.py` — Tune keywords, subreddits, thresholds, Bishop AI context, sheet columns
- `analyzer.py` — Claude scoring logic, intent types, relevance + intent scores, suggested reply format
- `notifier.py` — Slack formatting (count + link only), Sheets logging
- `main.py` — Pipeline orchestration, --once / --reddit-only / --web-only flags
- `reply_agent.py` — Auto-reply agent: reads sheet, sends comments + DMs across all platforms
- `reddit_monitor.py` — Reddit RSS polling, keyword filtering, 7-day date filter
- `web_monitor.py` — DuckDuckGo fallback, 7-day `timelimit='w'`
- `brave_monitor.py` — Brave Search API (preferred), `freshness=pw` for 7-day filter
- `n8n_jobs_monitor.py` — n8n Community Jobs via Discourse JSON API
- `storage.py` — SQLite dedup + cross-platform author tracking
- `setup_reddit_app.py` — One-shot script to create Reddit API app credentials
- `seen_posts.db` — Delete to reset dedup history
- `.browser_sessions/` — Playwright session storage for n8n and LinkedIn (avoids re-login)
- `run-daily.bat` — Task Scheduler entry point (runs at 7:00 AM EST)
