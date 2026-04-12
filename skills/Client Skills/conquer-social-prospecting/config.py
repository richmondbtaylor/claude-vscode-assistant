"""
Central configuration for Conquer.io Social Prospecting Agent.
Edit these lists to tune keywords, subreddits, thresholds, and sheet layout.
"""

# ── Reddit ─────────────────────────────────────────────────────────────────────
# Narrowed to 3 high-signal subreddits where Conquer's ICP (enterprise VP Sales,
# Sales Ops, RevOps at 50+ rep teams using Salesforce) actually posts.
# Broad subs (SaaS, startups, entrepreneur) were producing solo founders, not enterprise.

REDDIT_SUBREDDITS = [
    "sales",
    "salesforce",
    "salesops",
    "RevOps",
    "B2Bsales",
    "OutboundSales",
    "AccountExecutive",
    "SDR",
]

# Competitor-specific keywords ONLY — generic terms produce noise.
# These map directly to Conquer's ICP pain: switching off a competitor, pricing pain,
# integration issues, or actively evaluating alternatives.
REDDIT_KEYWORDS = [
    # Competitor switching / dissatisfaction
    "switching from Outreach",
    "leaving Outreach",
    "Outreach alternative",
    "Outreach too expensive",
    "Outreach pricing",
    "Outreach problems",
    "Outreach issues",

    "switching from Salesloft",
    "leaving Salesloft",
    "Salesloft alternative",
    "Salesloft too expensive",
    "Salesloft pricing",
    "Salesloft problems",
    "Salesloft issues",

    "Gong alternative",
    "Gong problems",
    "switching from Gong",

    "RingDNA alternative",
    "Revenue.io alternative",
    "switching from RingDNA",

    "Dialpad alternative",
    "Dialpad Sell problems",
    "switching from Dialpad",

    # Active evaluation signals
    "Outreach vs Salesloft",
    "Outreach vs Conquer",
    "Salesloft vs Conquer",
    "best sales engagement platform Salesforce",
    "sales engagement Salesforce native",
    "dialer native Salesforce",
    "Salesforce native dialer",
]

REDDIT_POST_LIMIT = 25
REDDIT_POLL_INTERVAL_MINUTES = 30

# ── G2 Review Scraping ────────────────────────────────────────────────────────
# Primary lead source: 1–3 star reviews of competitors on G2.
# Every result is a real enterprise user with a working direct review URL.
# No Brave/DDG web search — those return articles, not real people's pain posts.

G2_POLL_INTERVAL_HOURS = 6

# ── Analysis / Scoring ────────────────────────────────────────────────────────

MIN_INTENT_FOR_ALERT = 50       # Send to Slack for anything scoring 50+
MIN_INTENT_FOR_SHEETS = 18      # Log anything with a real signal to Sheets
LOG_ALL_TO_SHEETS = False

# ── Google Sheets ─────────────────────────────────────────────────────────────

SHEET_WORKSHEET_NAME = "Leads"

SHEET_COLUMNS = [
    "Timestamp",
    "Platform",
    "Source Community",
    "URL",
    "Poster Handle",
    "Post Snippet",
    "Intent Score",
    "Score Tier",
    "Job Title",
    "Company Name",
    "Salesforce Confirmed",
    "GDPR Flag",
    "Industry Signal",
    "Company Size Signal",
    "Pain Category",
    "Competitor Mentioned",
    "Date of Post",
    "Post Age Days",
    "Decision Maker Name",
    "Decision Maker Title",
    "Estimated Email",
    "Contact Source",
    "Outreach - Public Forum",
    "Outreach - DM Pivot",
    "Outreach - Direct Internal",
    "Should Contact",
    "Escalation",
    "CRM Check",
    "Claude Reasoning",
    "Status",
]

# ── Company Context (fed to Claude) ──────────────────────────────────────────

CONQUER_CONTEXT = """
Conquer.io is a sales engagement platform built natively inside Salesforce.

TARGET MARKET: Mid-market to Enterprise companies with 50+ sales reps who use Salesforce as their CRM.

CORE VALUE PROPS:
- 100% native Salesforce integration — no sync lag, no data mismatch, reps never leave SFDC
- CRM-native power dialer for high-volume outbound teams
- Sales cadences, call recording, local presence, voicemail drop — all inside Salesforce
- Call recording compliance built in (GDPR, TCPA)
- Rep productivity tracking without leaving Salesforce
- Eliminates the "Salesforce + third-party tool" sync failure problem

PRIMARY BUYERS: VP of Sales, CRO, Head of Sales Ops, Revenue Operations leaders, Director-level
sales management. IT decision-makers are secondary.

PRIORITY INDUSTRIES: Financial services, tech, healthcare, insurance.

COMPETITORS (and Conquer.io's edge against each):
- Outreach: Conquer.io is native to Salesforce; Outreach requires external sync and is expensive at scale
- Salesloft: Same sync issue; Salesloft is often cited as overpriced for enterprise teams with 50+ reps
- RingDNA / Revenue.io: Conquer.io has broader cadence and engagement features beyond just calling
- Dialpad Sell: Conquer.io is deeper in Salesforce; Dialpad is better for UCaaS, not pure sales engagement
- Gong: Gong is conversation intelligence only — Conquer.io handles the full engagement workflow inside SFDC

QUALIFICATION REQUIREMENTS:
- Must use Salesforce (or be evaluating it)
- Company size: 50+ sales reps ideal; 200+ employees on LinkedIn is a proxy signal
- US and English-speaking markets primary focus
"""
