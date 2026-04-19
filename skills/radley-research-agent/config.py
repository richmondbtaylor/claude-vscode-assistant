"""
Central configuration for Radley Lead Finder Agent.
Edit these lists to tune what the agent monitors and how sensitive it is.
"""

# ── Reddit ────────────────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    # Tax / Accounting professional
    "taxpros", "tax", "Accounting", "Bookkeeping", "CPA",
    # Startup / Founder
    "startups", "Entrepreneur", "smallbusiness", "SaaS",
    "techstartups", "YCombinator", "Bootstrapped", "microsaas",
    "EntrepreneurRideAlong",
    # Finance / CFO
    "CFO", "fintech", "FinancialPlanning",
    # Biotech / Medtech / Hardware (R&D heavy industries)
    "biotech", "medtech", "hardware", "robotics",
    # General business
    "business", "consulting",
]

REDDIT_KEYWORDS = [
    # Direct R&D tax credit intent
    "R&D tax credit", "research and development tax credit",
    "R&D credit", "research credit", "R&D tax",
    "section 41 credit", "section 41",
    "qualifying research expenses", "qualified research activities",
    "R&D tax claim", "claim R&D credit",
    # Documentation / compliance pain
    "R&D documentation", "R&D audit", "R&D compliance",
    "R&D record keeping", "R&D substantiation",
    "IRS R&D", "R&D study",
    # Software / tool seeking
    "R&D tax software", "R&D credit software",
    "automate R&D tax", "R&D credit tool",
    # Allocation / calculation pain
    "R&D payroll allocation", "R&D expense allocation",
    "R&D credit calculation", "four-part test",
    # Advisory / recommendation seeking
    "R&D tax accountant", "R&D tax advisor",
    "R&D credit consultant", "recommend R&D",
    "engineering tax credits", "startup tax credits",
    # Pain signals
    "R&D tax frustrat", "R&D documentation nightmare",
    "R&D audit risk", "R&D credit denied",
    "too much time documenting R&D", "R&D paperwork",
]

REDDIT_POST_LIMIT = 25
REDDIT_POLL_INTERVAL_MINUTES = 15

# ── LinkedIn ───────────────────────────────────────────────────────────────────

LINKEDIN_KEYWORDS = [
    # Direct R&D tax intent
    "R&D tax credit",
    "research and development tax credit",
    "section 41 credit",
    "qualifying research expenses",
    "R&D documentation",
    # Pain / help seeking
    "R&D tax audit",
    "R&D credit help",
    "R&D compliance",
    "R&D tax software",
    "automate R&D documentation",
    # Advisory seeking
    "R&D tax advisor",
    "R&D credit consultant",
    "R&D tax accountant",
    "engineering tax credit",
    # Founder / CFO signals
    "startup tax credits",
    "R&D payroll allocation",
    "R&D expense tracking",
    "R&D credit for software companies",
    "R&D credit for startups",
]

LINKEDIN_RESULTS_PER_KEYWORD = 5

# ── Facebook / Facebook Groups ─────────────────────────────────────────────────

FACEBOOK_KEYWORDS = [
    "R&D tax credit",
    "research and development tax credit",
    "R&D credit help",
    "R&D documentation",
    "R&D tax software",
    "R&D audit",
    "section 41 credit",
    "R&D tax advisor",
    "startup tax credits",
    "R&D credit consultant",
    "engineering tax credit",
    "R&D payroll allocation",
    "qualifying research expenses",
]

FACEBOOK_RESULTS_PER_KEYWORD = 5

# ── Twitter / X ────────────────────────────────────────────────────────────────

TWITTER_KEYWORDS = [
    "R&D tax credit",
    "R&D credit help",
    "R&D documentation nightmare",
    "R&D tax software",
    "R&D audit",
    "section 41 credit",
    "research and development tax credit",
    "R&D credit for startups",
    "R&D tax frustrating",
    "R&D payroll allocation",
    "engineering tax credits",
    "startup tax credits",
    "qualifying research expenses",
]

TWITTER_RESULTS_PER_KEYWORD = 5

# ── Web Search (DuckDuckGo / Brave — covers forums, communities, etc.) ───────

WEB_SEARCH_QUERIES = [
    # ── Tax professional forums ──────────────────────────────────────────────
    'site:community.intuit.com "R&D tax credit" OR "research credit" help',
    'site:community.intuit.com "section 41" OR "R&D documentation"',
    '"R&D tax credit" "need help" OR "looking for" OR "anyone recommend" site:reddit.com',
    '"R&D documentation" "nightmare" OR "frustrating" OR "painful" OR "time consuming"',

    # ── Accounting / CPA communities ─────────────────────────────────────────
    '"R&D tax credit" "how do I" OR "can anyone" OR "help me" -site:reddit.com',
    '"qualifying research expenses" help OR confused OR unclear',
    '"R&D credit" "denied" OR "rejected" OR "audit" frustrated OR worried',
    '"section 41" "four part test" help OR confused OR guidance',
    '"R&D study" cost OR expensive OR "too much" OR "worth it"',

    # ── Startup / Founder communities ────────────────────────────────────────
    'site:indiehackers.com "R&D tax credit" OR "R&D credit" OR "engineering tax"',
    'site:news.ycombinator.com "R&D tax credit" OR "research credit" startup',
    '"R&D tax credit" "software company" OR "SaaS" OR "tech startup" help',
    '"R&D credit" "first time" OR "how to claim" OR "is it worth" startup',
    '"R&D tax credit" "how much" OR "estimate" OR "calculator" startup',

    # ── Pain-specific queries ────────────────────────────────────────────────
    '"R&D documentation" "takes too long" OR "manual" OR "spreadsheet" OR "painful"',
    '"R&D tax credit" "audit" "worried" OR "scared" OR "risk" OR "what if"',
    '"R&D payroll allocation" "confusing" OR "how to" OR "help" OR "calculate"',
    '"R&D tax credit" "denied" OR "rejected" year OR claim',
    '"R&D credit" "accountant" OR "CPA" "doesn\'t know" OR "no experience" OR "recommend"',
    '"R&D tax" "documentation burden" OR "recordkeeping" OR "evidence" OR "substantiate"',

    # ── LinkedIn — high-intent posts ──────────────────────────────────────────
    'site:linkedin.com/posts "R&D tax credit" startup OR software OR SaaS',
    'site:linkedin.com/posts "qualifying research expenses" OR "R&D documentation"',
    'site:linkedin.com/posts "R&D credit" "help" OR "looking for" OR "recommend"',
    'site:linkedin.com/posts "section 41" OR "R&D audit" OR "R&D compliance"',
    'site:linkedin.com/posts "R&D tax" software OR automation OR tool',
    'site:linkedin.com/posts "engineering tax credit" OR "startup tax credit"',

    # ── Facebook Groups — public indexed content ──────────────────────────────
    'site:facebook.com/groups "R&D tax credit" help OR question OR advice',
    'site:facebook.com/groups "research and development tax" startup OR small business',
    'site:facebook.com/groups "R&D credit" accountant OR CPA OR advisor',
    'site:facebook.com/groups "R&D documentation" OR "R&D compliance"',

    # ── Twitter / X — public posts ────────────────────────────────────────────
    'site:x.com "R&D tax credit" help OR frustrated OR nightmare',
    'site:x.com "R&D credit" startup OR software OR SaaS',
    'site:x.com "R&D documentation" OR "R&D audit" help OR worried',
    'site:twitter.com "R&D tax credit" help OR looking OR recommend',

    # ── Quora ─────────────────────────────────────────────────────────────────
    'site:quora.com "R&D tax credit" software company OR startup OR SaaS',
    'site:quora.com "R&D credit" "how to claim" OR "is it worth" OR "qualify"',
    'site:quora.com "qualifying research expenses" OR "section 41 credit"',

    # ── General high-intent ──────────────────────────────────────────────────
    '"R&D tax credit" "anyone use" OR "recommend" OR "tool" OR "software" -site:reddit.com',
    '"R&D credit" "automate" OR "automation" OR "automated" documentation OR tracking',
    '"R&D tax credit" "startup" "first time" OR "new to" OR "how do" OR "worth it"',
    '"R&D tax" "too expensive" OR "cost" OR "DIY" OR "self-file" OR "in-house"',
]

WEB_RESULTS_PER_QUERY = 5
WEB_POLL_INTERVAL_HOURS = 1

# ── Analysis / Scoring ────────────────────────────────────────────────────────

MIN_RELEVANCE_FOR_ALERT = 70
LOG_ALL_TO_SHEETS = False
MIN_RELEVANCE_FOR_SHEETS = 70
MAX_LEADS_PER_RUN = 25

# ── Google Sheets ─────────────────────────────────────────────────────────────

SHEET_WORKSHEET_NAME = "Leads"

SHEET_COLUMNS = [
    "Timestamp",
    "Platform",
    "Subreddit",
    "URL",
    "Author",
    "Title / Snippet",
    "Relevance Score",
    "Intent Score",
    "Cross Platform",
    "Intent Type",
    "Urgency",
    "Decision Maker",
    "Budget Tier",
    "Already Solved",
    "Pain Points",
    "Budget Signals",
    "Suggested Reply",
    "Should Contact",
    "Claude Reasoning",
    "Status",
    "Reply Sent Date",
    "Comment Posted",
    "DM Sent",
]

# ── Company Context (fed to Claude) ──────────────────────────────────────────

RADLEY_CONTEXT = """
Radley (radley.tax) is a US-focused SaaS platform that automates R&D tax credit claims.

── WHAT RADLEY DOES ──
Radley connects to a company's existing tools — code repositories (GitHub, GitLab, Bitbucket),
payroll systems, and project management tools (Jira, Linear, Asana) — to automatically:
1. Identify qualifying research activities (the IRS four-part test)
2. Allocate employee time to qualifying vs. non-qualifying work
3. Calculate qualified research expenses (QREs) for both regular and ASC methods
4. Generate IRS-audit-ready documentation packages (Form 6765 support)
5. Continuously track R&D activities throughout the year (not just at tax time)

── IDEAL CUSTOMER PROFILES (ICPs) ──

ICP 1: Founders & CTOs at US Tech Startups
- Software, hardware, biotech, medtech, or manufacturing companies doing genuine R&D
- 10-500 employees, $1M-$100M revenue
- Currently either not claiming the credit (leaving money on the table) or using
  expensive consultants ($15K-$50K+/year) for manual R&D studies
- Pain: Don't know if they qualify, documentation is manual/nonexistent,
  or their current R&D study costs too much relative to the credit

ICP 2: CFOs & Finance Teams
- Managing R&D tax compliance and audit risk at mid-market tech companies
- Frustrated with manual time tracking, spreadsheet-based allocation,
  and retroactive documentation at year-end
- Pain: Audit anxiety, inaccurate QRE calculations, no continuous tracking,
  too dependent on expensive third-party R&D studies

ICP 3: Accountants, CPAs & Tax Advisors
- File R&D credit claims on behalf of multiple clients
- Need a scalable tool to serve more clients without proportional headcount
- Pain: Manual documentation process doesn't scale, clients don't keep good records,
  each study takes 40-80 hours of manual work

── WHAT RADLEY IS NOT ──
- Not a general tax software (TurboTax, Drake, etc.)
- Not an accounting firm or CPA practice
- Not a general business automation tool
- Focused exclusively on US Section 41 R&D tax credits

── COMPETITORS ──
- Manual R&D study firms: Alliant Group, KBKG, ADP SmartCompliance R&D
- Other R&D tax software: Neo.Tax, Boast.AI, TaxCredible, MainStreet (shut down)
- Big 4 R&D practices: Deloitte, PwC, EY, KPMG (for enterprise)

── OUTREACH TONE ──
Radley positions itself as the modern, tech-forward alternative to expensive manual R&D studies.
Key value props:
- "Stop paying $25K+/year for a manual R&D study — Radley automates it"
- "Your code already proves your R&D. Radley reads it."
- "Continuous R&D tracking, not a year-end scramble"
- "Audit-ready documentation, always up to date"
"""
