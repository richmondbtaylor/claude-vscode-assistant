---
name: braincx-research-agent
description: Manage, run, troubleshoot, or modify the BrainCX Social Listening Lead Finder — a Python agent that monitors Reddit, LinkedIn, Facebook, Twitter/X, and the web for businesses expressing pain around call volume, receptionist staffing, multilingual communication, and IVR/phone system problems. Use this skill when the user asks to run the BrainCX agent, add ICPs, change keywords, fix errors, view leads, update the Google Sheet, or adjust how the agent finds or scores leads for braincx.com.
---

# BrainCX Social Listening Lead Finder

A social listening agent that monitors Reddit, LinkedIn, Facebook Groups, Twitter/X, and the web (via Brave Search with DuckDuckGo fallback) for businesses actively expressing pain that BrainCX multilingual voice AI solves. Claude Sonnet 4.6 scores each post against 5 ICPs, classifies the pain point type, assigns a Hot/Warm/Cold lead score, generates a peer-like opening line for outreach, flags competitor mentions, and logs qualifying leads to Google Sheets with optional Slack alerts.

---

## Project Location

```
C:\Users\richm\.claude\skills\braincx-research-agent\
```

---

## How to Run

```bash
cd /c/Users/richm/.claude/skills/braincx-research-agent
source venv/Scripts/activate   # bash syntax

python main.py --once              # Full pass (Reddit + Web)
python main.py --once --reddit-only
python main.py --once --web-only
```

**Setup (first time):**
1. Copy `.env.example` to `.env` and fill in credentials
2. Run `python setup_sheets.py` to authorize Google Sheets OAuth
3. Run `python main.py --once` to test

---

## Architecture

```
main.py               Orchestrator — pipeline in --once or continuous mode
config.py             All tunable settings (ICPs, keywords, queries, thresholds, context)
analyzer.py           Claude Sonnet 4.6 lead scoring — ICP, pain point, lead score, opening line
reddit_monitor.py     Reddit via public RSS feeds (no API key needed)
web_monitor.py        DuckDuckGo fallback (used if BRAVE_API_KEY not set)
brave_monitor.py      Brave Search API (preferred) — freshness=pd for 24h filter
linkedin_monitor.py   LinkedIn keyword-based DDG monitor
facebook_monitor.py   Facebook Groups keyword-based DDG monitor
twitter_monitor.py    Twitter/X keyword-based DDG monitor
notifier.py           Logs to Google Sheets + sends Slack batch digests
storage.py            SQLite dedup (seen_posts.db) + cross-platform author tracking
```

---

## Target ICPs

| ICP | Key Pain Signals |
|---|---|
| Immigration attorneys / law firms | Multilingual intake calls, high volume, Spanish-speaking clients |
| Higher education (universities, community colleges) | Enrollment inquiry volume, multilingual student population |
| Healthcare practices | Scheduling calls, after-hours coverage, non-English patients, HIPAA |
| Professional services (financial, auto, title, real estate) | Multilingual clients, missed leads, after-hours inquiries |
| General legal / professional services | High call volume, staffing gaps, intake bottlenecks |

---

## Claude Scoring System (analyzer.py)

### Relevance Score (0–100)
- **90–100** — Real person explicitly asking for a voice AI, answering service, or receptionist solution with urgency
- **70–89** — Real person struggling with call volume, staffing, multilingual needs, or after-hours coverage
- **50–69** — Real person in target ICP discussing related pain, not yet seeking a solution
- **30–49** — Exploratory interest in relevant topic, not a near-term buyer
- **0–15** — Marketing article, blog post, tutorial, news, promotional content, already-solved problem

### Lead Score
- **Hot** — Explicitly expressed need + in ICP + decision maker
- **Warm** — In ICP with relevant pain, lower urgency or unclear decision authority
- **Cold** — Tangential or unclear fit

### Pain Point Types
- `call_volume_overflow` — Front desk overwhelmed, can't keep up with inbound calls
- `after_hours_coverage` — Missing calls or leads outside business hours
- `multilingual_barrier` — Can't serve non-English-speaking clients/patients
- `receptionist_staffing` — Can't hire, afford, or retain front desk staff
- `outdated_ivr` — Complaints about phone trees or IVR systems
- `scheduling_bottleneck` — Appointment scheduling is a pain point
- `intake_inefficiency` — Client/patient intake is slow or dropping leads
- `hipaa_compliance` — Asking about HIPAA-compliant phone/scheduling tools
- `lead_leakage` — Losing clients/patients because calls go unanswered
- `solution_seeking` — Actively asking for a recommendation or tool

### Competitor Flagging
If a post mentions Ruby Receptionists, Smith.ai, Air AI, Bland AI, Vapi, Retell AI, RingCentral, Twilio, Vonage, Zocdoc, NexHealth, or other answering/scheduling services, the `competitor_mentioned` field is populated so BrainCX can counter-position.

---

## Google Sheets — 20 Columns

| Column | Description |
|---|---|
| Timestamp | Date/time found (MM/DD/YYYY HH:MM UTC) |
| Platform | Reddit, LinkedIn, Facebook, Twitter/X, Web, etc. |
| Source | Subreddit or keyword source |
| URL | Link to original post |
| Author | Username or name |
| Title / Snippet | First 120 chars |
| Relevance Score | 0–100 — fit for BrainCX |
| Intent Score | 0–100 — buying intent |
| Cross Platform | Other platforms where this author was seen |
| ICP Category | immigration_law / healthcare / higher_education / professional_services / general_legal |
| Pain Point | Specific pain described by the author |
| Why It Fits | How BrainCX voice AI solves this specific problem |
| Urgency | high / medium / low |
| Decision Maker | Yes / No |
| Competitor Mentioned | Competitor product name or "No" |
| Lead Score | Hot / Warm / Cold |
| Suggested Opening Line | Peer-like outreach under 3 sentences |
| Should Contact | Yes / No |
| Claude Reasoning | 1–2 sentence score explanation |
| Status | User fills in — "Contacted", "Pass", etc. |

---

## Key Configuration (config.py)

| Setting | What it controls |
|---|---|
| `REDDIT_SUBREDDITS` | Legal, healthcare, higher ed, professional services, front desk communities |
| `REDDIT_KEYWORDS` | Call volume, multilingual, IVR, receptionist, after-hours pain signals |
| `LINKEDIN_KEYWORDS` | Personal help requests around calls, multilingual, AI receptionist |
| `TWITTER_KEYWORDS` | Pain signals and AI solution queries |
| `WEB_SEARCH_QUERIES` | site: operator queries for Reddit, LinkedIn, healthcare forums, Facebook |
| `MIN_RELEVANCE_FOR_ALERT` | 30 — minimum score to queue for Slack |
| `MIN_RELEVANCE_FOR_SHEETS` | 30 — minimum score to log to Sheets |
| `BRAINCX_CONTEXT` | ICP descriptions and fit criteria fed to Claude |

---

## Environment Variables (.env)

```
# Google Sheets
GOOGLE_OAUTH_CREDENTIALS=./credentials.json   # Path to OAuth client JSON
GOOGLE_SHEET_ID=                               # Spreadsheet ID for BrainCX leads

# Slack (optional)
SLACK_WEBHOOK_URL=                             # Incoming webhook URL

# Brave Search (optional — falls back to DuckDuckGo if blank)
BRAVE_API_KEY=
```

Google OAuth token is cached at `~/.config/gspread/authorized_user.json` after first `setup_sheets.py` run.

---

## Common Tasks

### Run the agent
```bash
cd /c/Users/richm/.claude/skills/braincx-research-agent && source venv/Scripts/activate && python main.py --once
```

### Add a new subreddit
Edit `REDDIT_SUBREDDITS` in `config.py`.

### Add a keyword / pain signal
Edit `REDDIT_KEYWORDS`, `LINKEDIN_KEYWORDS`, or `TWITTER_KEYWORDS` in `config.py`.

### Add a web search query
Edit `WEB_SEARCH_QUERIES` in `config.py`. Use `site:` operators.

### Change lead score threshold
Change `MIN_RELEVANCE_FOR_ALERT` and `MIN_RELEVANCE_FOR_SHEETS` in `config.py`.

### Reset deduplication
```bash
rm /c/Users/richm/.claude/skills/braincx-research-agent/seen_posts.db
```

### Re-authorize Google Sheets
```bash
python setup_sheets.py
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `GOOGLE_SHEET_ID` missing | Add to `.env` — create a new Google Sheet and paste the ID |
| Google Sheets auth error | Run `python setup_sheets.py` to re-authorize |
| 0 results from web monitor | DDG rate limit — increase `_REQUEST_DELAY` in web_monitor.py, or add `BRAVE_API_KEY` |
| Brave API returning 0 results | Check key at brave.com/search/api; confirm `BRAVE_API_KEY` is set in `.env` |
| JSON parse error from Claude | Claude returned markdown — stripping already handled in analyzer.py |
| Slack not receiving alerts | Check score threshold (30+), check `SLACK_WEBHOOK_URL` in `.env` |
| `UnicodeEncodeError` on Windows | `sys.stdout.reconfigure(encoding="utf-8")` already in main.py |
| `ddgs` import error | `pip install ddgs` |

---

## File Map

- `config.py` — ICPs, keywords, subreddits, thresholds, BrainCX context, sheet columns
- `analyzer.py` — BrainCX-specific scoring, ICP categories, pain types, competitor flagging
- `notifier.py` — Slack + Google Sheets output
- `main.py` — Pipeline orchestration
- `reddit_monitor.py` — Reddit RSS polling
- `brave_monitor.py` — Brave Search API (preferred)
- `web_monitor.py` — DuckDuckGo fallback
- `linkedin_monitor.py` — LinkedIn keyword monitor
- `facebook_monitor.py` — Facebook Groups monitor
- `twitter_monitor.py` — Twitter/X monitor
- `storage.py` — SQLite dedup + cross-platform tracking
