---
name: instagram-engagement
description: Automate Instagram engagement (likes, comments, follows/unfollows) for AI automation education accounts using Playwright. Use this skill whenever the user says "run Instagram engagement", "start an Instagram session", "engage on Instagram for me", "run the Instagram bot", "like and follow on Instagram", "grow my Instagram account", or gives a command like "run Instagram engagement for my [account] focusing on [hashtag] for [X] minutes". Also trigger when the user wants to start or stop an engagement session, check session results, view the engagement report, configure Instagram accounts/credentials, add accounts to the unfollow whitelist, or troubleshoot any Instagram automation issue. Always use this skill before running any Instagram automation — don't improvise without it.
---

# Instagram Engagement Automation

Playwright-based headless browser agent that automates liking, commenting, and following on Instagram to drive organic follower growth for AI automation education accounts. Uses Claude to generate contextual, non-generic comments. Tracks all engagement in SQLite and enforces strict per-hour and per-day rate limits to reduce detection risk.

---

## Project Location

```
C:\Users\richm\.claude\skills\instagram-engagement\
```

---

## How to Run

```bash
cd /c/Users/richm/.claude/skills/instagram-engagement
source venv/Scripts/activate

# Run a session
python main.py --account main_account --focus "#AIautomation" --duration 60

# Dry run (preview targets without taking action)
python main.py --account main_account --focus "#AIeducation" --duration 30 --dry-run

# Unfollow non-reciprocators (runs independently of engagement session)
python main.py --account main_account --unfollow-only

# Check today's usage stats
python main.py --account main_account --stats
```

**Parameters:**
| Flag | Required | Example | Description |
|---|---|---|---|
| `--account` | Yes | `main_account` | Account key from `.env` config |
| `--focus` | Yes (unless --unfollow-only) | `#AIautomation` | Hashtag to target |
| `--duration` | Yes (unless --unfollow-only) | `60` | Session length in minutes |
| `--dry-run` | No | — | Preview only, no actions taken |
| `--unfollow-only` | No | — | Run unfollow pass without engagement |
| `--stats` | No | — | Show today's usage counters and exit |

---

## Setup (First Time)

### 1. Install dependencies
```bash
cd /c/Users/richm/.claude/skills/instagram-engagement
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure credentials
Copy `.env.example` to `.env` and fill in your account credentials:
```bash
cp .env.example .env
```

Edit `.env` with your Instagram login details per account (see `.env.example` for format).

### 3. Initialize the database
The SQLite database (`engagement.db`) is created automatically on first run.

---

## Architecture

```
main.py                 Orchestrator — parses args, runs session loop
config.py               Credentials, rate limits, whitelist, hashtags
instagram_session.py    Playwright login, hashtag search, profile scraping, actions
engagement_tracker.py   SQLite tracking — history, follow-back monitoring, rate counters
comment_generator.py    Claude API — generates contextual AI-relevant comments
run.bat                 Windows Task Scheduler entry point (optional)
engagement.db           SQLite — auto-created on first run
```

---

## Key Configuration (config.py)

| Setting | Default | What it controls |
|---|---|---|
| `RATE_LIMITS_HOURLY` | 20 follows, 30 comments, 50 likes | Max actions per hour per account |
| `RATE_LIMITS_DAILY` | 100 follows, 120 comments, 200 likes | Max actions per day per account |
| `ACTION_DELAY_RANGE` | (45, 120) seconds | Random delay between each action |
| `HOURLY_BREAK_RANGE` | (5, 10) minutes | Break taken every ~60 minutes |
| `MIN_FOLLOWERS` | 500 | Minimum followers to engage |
| `MAX_POST_AGE_DAYS` | 7 | Account must have posted within this window |
| `MIN_FOLLOW_RATIO` | 0.5 | followers / following ratio floor |
| `COMMENT_COOLDOWN_DAYS` | 30 | Days before re-commenting on same account |
| `FOLLOW_BACK_WAIT_DAYS` | 7 | Days to wait for follow-back before unfollow |
| `BIO_KEYWORDS` | `['AI', 'automation', 'consulting']` | At least one must appear in bio |
| `UNFOLLOW_WHITELIST` | See `.env` | Accounts to never unfollow |

---

## Engagement Logic

### Target Discovery
Searches the specified hashtag and collects recent post authors. Also supports scraping followers of competitor/leader accounts (configure `COMPETITOR_ACCOUNTS` in `.env`).

### Account Filtering (all criteria must pass)
- Follower count > 500
- Posted within last 7 days
- Bio contains at least one of: 'AI', 'automation', 'consulting'
- followers/following ratio ≥ 0.5
- Not an obvious content aggregator (checked via post cadence and bio)
- Prioritizes personal brand accounts over large corporate pages

### Per-Account Engagement Sequence
1. **History check** — if commented on their post in last 30 days: skip comment + follow, but still like if recent posts exist
2. **Recency check** — if most recent post > 14 days old: like only, no comment or follow
3. **Like** 2–3 most recent posts
4. **Comment** — one contextual comment generated by Claude on most recent post (analyzes caption topic)
5. **Follow** the account

### Comment Style
Comments are inquisitive and encouraging — they analyze the post caption to reference the specific AI topic. No generic "great post!" phrases. Examples of the style:
- *"That's a sharp breakdown of prompt chaining — have you found that works better than a single mega-prompt in production workflows?"*
- *"Love this take on AI education. What's your biggest challenge getting clients to actually implement what they learn?"*

### Unfollow Logic
Runs on demand (`--unfollow-only`) or can be triggered at end of each session. Checks the `follows` table: if followed > 7 days ago and no follow-back detected, and not on the whitelist → unfollow.

---

## Rate Limits (strictly enforced)

| Window | Follows | Comments | Likes |
|---|---|---|---|
| Per hour | 20 | 30 | 50 |
| Per day | 100 | 120 | 200 |

When a limit is hit, the session pauses until the next window resets rather than throwing an error.

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=           # Claude API key — required for comment generation

# Account: main_account (add more blocks for additional accounts)
IG_main_account_USERNAME=    # Instagram username
IG_main_account_PASSWORD=    # Instagram password

# Optional: competitor accounts to scrape followers from
COMPETITOR_ACCOUNTS=account1,account2,account3

# Accounts to never unfollow (comma-separated usernames)
UNFOLLOW_WHITELIST=username1,username2
```

To add a second account named `agency_account`:
```
IG_agency_account_USERNAME=...
IG_agency_account_PASSWORD=...
```

---

## Session Report Format

After each session:
```
========================================
  Instagram Engagement Session Report
========================================
Account      : main_account
Focus        : #AIautomation
Duration     : 60 minutes
----------------------------------------
Followed     : 14 accounts
Commented    : 11 posts
Liked        : 38 posts
Unfollowed   : 3 accounts
Skipped      : 7 accounts (filtered out)
Errors       : 1 (rate limit pause)
----------------------------------------
Daily totals : 14/100 follows | 11/120 comments | 38/200 likes
========================================
```

---

## Common Tasks

### Run a 60-minute engagement session
```bash
cd /c/Users/richm/.claude/skills/instagram-engagement && source venv/Scripts/activate && python main.py --account main_account --focus "#AIautomation" --duration 60
```

### Preview targets without taking action
```bash
python main.py --account main_account --focus "#ClaudeAI" --duration 30 --dry-run
```

### Run unfollow pass only
```bash
python main.py --account main_account --unfollow-only
```

### Check today's stats
```bash
python main.py --account main_account --stats
```

### Add an account to the unfollow whitelist
Edit `UNFOLLOW_WHITELIST` in `.env` — add the username, comma-separated.

### Change rate limits
Edit `RATE_LIMITS_HOURLY` and `RATE_LIMITS_DAILY` in `config.py`.

### Change bio filter keywords
Edit `BIO_KEYWORDS` in `config.py`.

---

## Troubleshooting

| Error | Fix |
|---|---|
| Login challenge / CAPTCHA detected | Script stops automatically and notifies you. Complete the challenge manually in a normal browser, then retry. |
| `ANTHROPIC_API_KEY` not found | Add key to `.env` |
| Playwright browser not found | Run `playwright install chromium` |
| `engagement.db` permission error | Check file isn't locked by another process |
| Rate limit hit mid-session | Normal — script pauses and continues in next window |
| 0 targets found for hashtag | Hashtag may be restricted or too niche; try a broader one |
| Follow-back check not working | Instagram profile visibility settings; private accounts won't show followers list |
| `venv` not activating on Windows | Use `source venv/Scripts/activate` (bash) not `venv\Scripts\activate.bat` (cmd) |
