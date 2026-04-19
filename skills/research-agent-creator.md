# Research Agent Creator

## Trigger

Use this skill when the user wants to build a new social listening / lead research agent for a client. Triggered by phrases like "build a research agent for [client]", "new research agent", "set up lead monitoring for", or "create a client research agent".

## Purpose

This skill interviews the user about a new client, then generates a fully configured, production-ready research agent — a multi-source social listening bot that monitors Reddit, Twitter/X, LinkedIn, Facebook, Hacker News, Upwork, web forums, and optional Apify-gated sources for buyer intent signals. The output is a complete agent folder under `skills/Client Skills/[client-slug]-research-agent/` with all files ready to run.

The skill follows the **RESEARCH-AGENT Framework**:

**R** — Requirements intake (who is the client, what do they sell)  
**E** — Ecosystem mapping (where their buyers live online)  
**S** — Signal definition (what language qualifies a lead)  
**E** — Exclusion rules (what disqualifies a lead)  
**A** — Architecture selection (Python full / Node.js light / hybrid)  
**R** — Reporting setup (Sheets, Slack, Apify, enrichment)  
**C** — Configuration generation (produce all agent files)  
**H** — Handoff checklist (env vars, creds, test run, schedule)

---

## Intake Process

Work through each section below IN ORDER. Ask all questions in a section as a numbered list before moving to the next section. Wait for answers before proceeding.

Tell the user upfront: "I'll walk you through 8 quick sections. Most answers are 1-3 lines. The more detail you give, the sharper the agent's targeting will be."

---

### SECTION 1 — Client Basics

Ask these questions together:

1. **Client name** — What is the client's company name? (e.g., "Radley Tax Advisors")
2. **Slug** — What short slug should we use for the folder? (e.g., `radley` → folder becomes `radley-research-agent`)
3. **Website** — What is their website URL?
4. **Industry** — What industry/niche are they in? (e.g., "R&D tax credits for startups")
5. **What they sell** — Describe their core offer in 1-2 sentences. What problem does it solve, and for whom?
6. **Deal size / price point** — Roughly what does a client engagement cost, or what's the typical deal value? (helps calibrate budget signals)
7. **Who is this agent for?** — Is this for Bishop AI's internal use (we use it to prospect for the client), or will the client's own team access the data?
8. **Who receives the output?** — List everyone who gets results: Slack channels, email addresses, Google Sheet access. Include client contacts if applicable.

---

### SECTION 2 — Ideal Customer Profile (ICP)

Ask these questions together:

9. **Target titles / roles** — What job titles or roles are the ideal buyers? (e.g., "CFO, VP Finance, Founder at seed-stage startups")
10. **Target company types** — What kinds of companies are ideal? (size, stage, funding, industry verticals, geography)
11. **Pain points** — List the 3-5 core pains or frustrations their buyers express out loud. Use their language, not marketing language.
12. **Buying triggers** — What life events or business events make someone suddenly need this? (e.g., "just hired first engineers", "preparing for Series A audit", "got an IRS notice")
13. **Non-negotiables (disqualifiers)** — What makes a lead automatically NOT worth pursuing? (e.g., "already using a competitor", "solo freelancer with no employees", "outside the US")
14. **Example of a PERFECT lead post** — Paste or describe a real post or message that would be an ideal qualified lead. If you have one from Reddit, LinkedIn, or anywhere, paste it verbatim.
15. **Example of a FALSE POSITIVE** — Describe a post that looks related but is NOT a good lead (so the agent learns to skip it).

---

### SECTION 3 — Ecosystem Mapping

Ask these questions together:

16. **Reddit** — Which subreddits do their buyers hang out in? List as many as you know. (e.g., r/startups, r/accounting, r/Entrepreneur)  
    *Note: if unsure, say "suggest" and I'll recommend based on the ICP.*

17. **Other forums / communities** — Any specific communities beyond Reddit? (e.g., Indie Hackers, Hacker News, specific Slack groups, Discord servers, niche forums)

18. **LinkedIn** — Should we monitor LinkedIn? If yes, what kinds of posts or groups? Any specific LinkedIn search terms?

19. **Twitter / X** — Should we monitor Twitter/X? If yes, what hashtags or search terms?

20. **Facebook Groups** — Any Facebook groups to monitor? List names or URLs.

21. **Upwork** — Should we monitor Upwork job postings? If yes, what job category keywords?

22. **Web / Google dorks** — Any specific websites, forums, or platforms to DuckDuckGo/Brave search? (e.g., community.openai.com, specific trade association sites)

23. **Password-gated or JS-heavy sites (Apify)** — Are there any sites that require login or heavy JS rendering that we'd need Apify for? (e.g., LinkedIn Jobs, private Facebook groups, Glassdoor, Crunchbase)

---

### SECTION 4 — Signal Definition (Keywords & Scoring)

Ask these questions together:

24. **Primary intent keywords** — What exact words or phrases signal someone NEEDS this client's service? These are the highest-confidence terms. (e.g., "R&D tax credit", "qualified research expenses")

25. **Secondary / adjacent keywords** — What related terms indicate a potential need, even if not explicitly stated? (e.g., "hiring engineers", "startup tax savings", "IRS audit")

26. **Negative keywords** — What words should immediately disqualify a post? (e.g., "UK", "Canada", "RDEC", "self-employed")

27. **Budget signal phrases** — What language in a post suggests this person has or is spending real money? (e.g., "just closed our Series A", "we have 10 engineers on payroll", "our burn rate is")

28. **Decision-maker signals** — What language suggests the poster can actually buy? (e.g., "I'm the founder", "I manage our finances", "we're evaluating vendors")

29. **Urgency signals** — What language suggests they need help NOW? (e.g., "tax filing deadline", "our accountant doesn't know about this", "we got a notice")

---

### SECTION 5 — Exclusion & Qualification Rules

Ask these questions together:

30. **Geographic restriction** — Is this offer US-only, specific states, or global? Define what's in and out.

31. **Company size floor/ceiling** — Minimum and maximum company size or headcount to qualify?

32. **Already-solved filter** — What phrases suggest the person already has a solution and is NOT a lead? (e.g., "our R&D tax firm handles it", "already claiming the credit")

33. **Competitor mentions** — List competitors or alternatives. If a post mentions them positively, should we skip or still flag?

34. **Content type exclusions** — Any post types to ignore? (e.g., news articles, press releases, job postings by the ICP company itself, bot/spam patterns)

---

### SECTION 6 — Outreach & Reply Strategy

Ask these questions together:

35. **Outreach voice / tone** — How should the suggested reply sound? (e.g., "conversational and peer-to-peer", "authoritative expert", "curious and helpful, not salesy")

36. **Reply format** — Should suggested replies be: (a) a public comment, (b) a DM opener, or (c) both with separate drafts?

37. **Value prop in the reply** — What's the ONE thing the reply should communicate? What should it offer or say to earn trust?

38. **CTA** — What's the call to action? (e.g., "book a free 15-min call", "DM me and I'll send our breakdown", "happy to share our checklist")

39. **Reply examples** — Paste 1-2 real replies the client has sent that worked well. These become the tone reference.

---

### SECTION 7 — Output & Reporting Configuration

Ask these questions together:

40. **Google Sheet** — New sheet or existing? If existing, paste the Sheet ID. If new, what should it be titled? (e.g., "Radley Lead Intelligence — May 2026")

41. **Sheet tabs needed** — Standard tabs: HOT Leads, WARM Leads, Cold/Archived, Job Posting Tracker, Re-engagement. Add or remove any?

42. **Slack** — Should results be sent to Slack? If yes, paste the webhook URL or channel name. Should it be a real-time alert or daily digest?

43. **Email digest** — Should a daily/weekly summary email be sent? If yes, to whom?

44. **Apify integration** — Should we use Apify for contact enrichment or gated-site scraping? If yes, do you have an Apify API key ready?

45. **Contact enrichment fields** — Which fields should we try to enrich for hot leads? (Options: email, email confidence %, phone, phone type, LinkedIn profile URL, full name, company, company website, job title)

46. **Enrichment threshold** — What minimum relevance score should trigger enrichment? (Bishop uses 70. Higher = fewer but sharper enrichments.)

---

### SECTION 8 — Schedule & Operations

Ask these questions together:

47. **Run frequency** — How often should the agent poll? (e.g., "Reddit every 15 min, web every 2 hours", or "once per day at 7am")

48. **On-demand option** — Should the agent also support a single manual `--once` run? (Almost always yes)

49. **Post age filter** — How old can a post be and still be actionable? (Bishop uses 24 hours. Radley uses 365 days for evergreen content.)

50. **Multi-client isolation** — The agent will run in its own folder with its own `.env` and `seen_posts.db`. Confirm this is correct, or do you want to share infrastructure with another agent?

51. **Where will this run?** — Local machine (Windows/Mac), a server, or a scheduled Claude Code remote trigger?

52. **Client subcompanies or brands** — Does this client have sister companies, subsidiaries, or co-brands we should include or exclude from the research?

---

## After Intake: Build the Agent

Once all sections are answered, perform the following steps IN ORDER:

### Step 1 — Confirm & Summarize

Output a one-page summary of the configuration:
- Client name, slug, industry, offer
- ICP snapshot (roles, company type, pain points, triggers)
- Sources being monitored (list all platforms + specific subreddits/groups)
- Keyword lists (primary, secondary, negative)
- Output configuration (Sheet title + tabs, Slack, Apify Y/N)
- Schedule

Ask: "Does this look right? Any corrections before I build?"

---

### Step 2 — Generate Agent Files

Create the folder: `c:/Users/richm/.claude/skills/Client Skills/[slug]-research-agent/`

Generate these files:

#### `config.py`
Full configuration module. Include ALL of the following, customized from the intake:

```python
# ── Client Identity ──────────────────────────────────────────────────────────
CLIENT_NAME = "[Client Name]"
CLIENT_SLUG = "[slug]"
CLIENT_WEBSITE = "[website]"
CLIENT_OFFER = "[1-2 sentence offer description]"

# ── ICP ──────────────────────────────────────────────────────────────────────
ICP_TITLES = [...]  # job titles of ideal buyers
ICP_COMPANY_TYPES = [...]  # company sizes, stages, verticals
ICP_PAIN_POINTS = [...]  # verbatim pain phrases

# ── Keywords ─────────────────────────────────────────────────────────────────
PRIMARY_KEYWORDS = [...]  # highest-confidence intent terms
SECONDARY_KEYWORDS = [...]  # adjacent / softer signals
NEGATIVE_KEYWORDS = [...]  # instant disqualifiers

BUDGET_SIGNALS = [...]  # phrases that suggest real money
DECISION_MAKER_SIGNALS = [...]  # phrases that suggest authority
URGENCY_SIGNALS = [...]  # phrases that suggest immediate need

# ── Sources ───────────────────────────────────────────────────────────────────
REDDIT_SUBREDDITS = [...]
REDDIT_POLL_INTERVAL_MINUTES = 15

MONITOR_LINKEDIN = True/False
MONITOR_TWITTER = True/False
MONITOR_FACEBOOK = True/False
MONITOR_UPWORK = True/False
MONITOR_HN = True/False
MONITOR_WEB = True/False

WEB_SEARCH_QUERIES = [...]  # DuckDuckGo/Brave search strings
UPWORK_KEYWORDS = [...]
WEB_POLL_INTERVAL_HOURS = 2

APIFY_ENABLED = True/False
APIFY_ACTORS = {...}  # actor IDs for gated sources

# ── Scoring Thresholds ────────────────────────────────────────────────────────
MIN_RELEVANCE_FOR_ALERT = 65       # Slack alert threshold
MIN_RELEVANCE_FOR_SHEETS = 50      # Sheet log threshold
ENRICH_MIN_SCORE = 70              # Contact enrichment threshold
LOG_ALL_TO_SHEETS = False

# ── Google Sheets ─────────────────────────────────────────────────────────────
SHEET_WORKSHEET_NAME = "Leads"
SHEET_COLUMNS = [
    "Timestamp", "Platform", "Source", "URL", "Author",
    "Title / Snippet", "Relevance Score", "Intent Score",
    "Cross Platform", "Intent Type", "Urgency", "Decision Maker",
    "Budget Tier", "Already Solved", "Pain Points", "Budget Signals",
    "Suggested Reply (Comment)", "Suggested Reply (DM)",
    "Should Contact", "Claude Reasoning",
    "Status", "Reply Sent Date", "Comment Posted", "DM Sent",
    "Email", "Email Confidence %", "Phone", "Phone Type",
    "LinkedIn Profile", "Enriched Name", "Company",
    "Company Website", "Job Title", "Enrichment Source",
]

# ── Outreach ──────────────────────────────────────────────────────────────────
REPLY_TONE = "[tone description]"
REPLY_CTA = "[CTA phrase]"
REPLY_VALUE_PROP = "[one-liner value prop]"
REPLY_EXAMPLES = [
    "[example reply 1]",
    "[example reply 2]",
]

# ── Geographic / Qualification Rules ─────────────────────────────────────────
GEO_ALLOWED = [...]        # e.g., ["US", "USA", "United States"]
GEO_BLOCKED = [...]        # e.g., ["UK", "Canada", "Australia"]
MIN_COMPANY_HEADCOUNT = 0  # 0 = no floor
MAX_COMPANY_HEADCOUNT = 0  # 0 = no ceiling
COMPETITORS = [...]        # competitor names to flag

# ── Post Age Filter ───────────────────────────────────────────────────────────
MAX_POST_AGE_DAYS = 1      # posts older than this are skipped

# ── Notifications ─────────────────────────────────────────────────────────────
SLACK_ENABLED = True/False
SLACK_BATCH_SIZE = 5       # send digest after this many leads accumulate
EMAIL_DIGEST_ENABLED = False
EMAIL_RECIPIENTS = []
```

#### `main.py`
Orchestrator that imports all monitors, runs the poll loop, handles `--once`, `--reddit-only`, `--web-only`, `--apify-only` flags. Include graceful shutdown on Ctrl+C. Mirror the Bishop AI architecture but wired to this client's config.

#### `analyzer.py`
Claude-powered scoring engine. The system prompt must be fully customized with:
- Client's offer and ICP
- The exact PRIMARY_KEYWORDS, SECONDARY_KEYWORDS, NEGATIVE_KEYWORDS from config
- The BUDGET_SIGNALS, DECISION_MAKER_SIGNALS, URGENCY_SIGNALS
- The example perfect lead and example false positive from the intake
- Geographic and company-size rules
- Competitor handling rules
- The reply tone, CTA, and value prop for generating Suggested Reply fields
- Scoring rubric: 0-100 relevance, 0-100 intent, hot/warm/cold classification

The analyzer must return a structured JSON response with ALL SHEET_COLUMNS fields populated.

#### `notifier.py`
Slack + Google Sheets output layer. Batch Slack digests. Auto-create Sheet tabs if not found. Color-code rows by score (green = hot, yellow = warm, grey = cold). Freeze header row.

#### `storage.py`
SQLite deduplication. Table: `seen_posts(id TEXT PRIMARY KEY, platform TEXT, seen_at TIMESTAMP)`. Methods: `is_seen(post_id, platform)`, `mark_seen(post_id, platform)`.

#### `contact_enricher.py`
Apify-based enrichment (if enabled). Accepts a lead dict, queries Apify actors for email, phone, LinkedIn, company data. Returns `EnrichmentResult` dataclass. If Apify is disabled, returns empty result.

#### `reddit_monitor.py`
Reddit JSON API (no auth required). Polls each subreddit in `REDDIT_SUBREDDITS` for new posts matching PRIMARY_KEYWORDS + SECONDARY_KEYWORDS. Also runs keyword search across Reddit. Deduplicates by post ID.

#### `web_monitor.py`
DuckDuckGo + Brave search using all `WEB_SEARCH_QUERIES`. Parses result snippets. Fetches page content for top results using httpx.

#### `[platform]_monitor.py` (one per enabled platform)
Generate monitor files for each enabled platform: `linkedin_monitor.py`, `twitter_monitor.py`, `facebook_monitor.py`, `upwork_monitor.py`, `hn_monitor.py`, `apify_monitor.py`.

Each platform monitor returns a list of `RawPost` objects with fields: `id`, `platform`, `source`, `title`, `url`, `author`, `content`, `published_at`, `profile_url`.

#### `setup_sheets.py`
One-time Google Sheets auth + sheet creation script. Creates the spreadsheet (or opens existing), creates all configured tabs with headers, applies formatting (frozen header, column widths, color scheme).

#### `.env.example`
```
ANTHROPIC_API_KEY=
GOOGLE_SHEET_ID=
GOOGLE_OAUTH_CREDENTIALS=./credentials.json
SLACK_WEBHOOK_URL=
APIFY_API_KEY=
```

#### `requirements.txt`
All Python dependencies pinned. Includes: `anthropic`, `gspread`, `google-auth`, `schedule`, `python-dotenv`, `requests`, `httpx`, `playwright`, `apify-client` (if Apify enabled).

---

### Step 3 — Generate Skill MD

Create `c:/Users/richm/.claude/skills/[slug]-research-agent.md` using the bishop-research-agent.md skill as a template, but customized with:
- Client name and description in the trigger/description
- Client-specific run commands
- Troubleshooting notes specific to the platforms enabled

---

### Step 4 — Output Handoff Checklist

Print a numbered checklist the user can check off:

```
SETUP CHECKLIST — [Client Name] Research Agent

[ ] 1. Copy .env.example → .env and fill in all values
[ ] 2. Place Google OAuth credentials.json in the agent folder
[ ] 3. Run: python setup_sheets.py  (opens browser to authorize Google)
[ ] 4. Confirm Google Sheet ID is in .env
[ ] 5. Set SLACK_WEBHOOK_URL in .env (if Slack enabled)
[ ] 6. Set APIFY_API_KEY in .env (if Apify enabled)
[ ] 7. Install Playwright browsers: python -m playwright install chromium
[ ] 8. Install deps: pip install -r requirements.txt
[ ] 9. Test single pass: python main.py --once
[ ] 10. Review first batch of leads in Google Sheet
[ ] 11. Tune scoring thresholds in config.py if needed
[ ] 12. Start continuous agent: python main.py
[ ] 13. (Optional) Set up Windows Task Scheduler or Claude remote trigger for auto-start
```

---

## Quality Rules

- Every generated file must be complete and runnable — no placeholder comments like `# TODO: implement this`
- The `analyzer.py` system prompt must reference the client's actual keywords, ICP, examples, and reply guidance verbatim from the intake answers
- All monitor files must be functional implementations, not stubs
- The `config.py` must be the single source of truth — no hardcoded values in other files
- Each agent folder is fully isolated: its own `.env`, `seen_posts.db`, `credentials.json`, `venv/`
- If Apify is disabled, `contact_enricher.py` must still exist but return empty results gracefully
- Multi-client simultaneous operation is guaranteed by isolation — each agent has its own DB and Sheet

---

## Notes for Future Conversations

- This skill creates agents that run like `bishop-research-agent` and `radley-research-agent`
- All client agents live under `skills/Client Skills/[slug]-research-agent/`
- Each has its own skill MD at `skills/[slug]-research-agent.md`
- When managing an existing client agent, load that client's skill MD instead of this one
- This skill is a factory — it creates, it does not manage
