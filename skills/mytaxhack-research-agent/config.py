"""
Central configuration for MyTaxHack Research Agent.
Edit these lists to tune what the agent monitors and how sensitive it is.
"""

# ── Reddit ────────────────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    # Tax / Finance / Accounting
    "tax", "AskAccountants", "Accounting", "taxadvice",
    # Core ICP: SMB founders, agencies, SaaS, ecommerce
    "smallbusiness", "Entrepreneur", "EntrepreneurRideAlong", "business",
    "agency", "PPC", "digital_marketing", "marketing",
    "SaaS", "microsaas", "startups", "Bootstrapped",
    "ecommerce", "shopify", "AmazonSeller",
    # Software / tech founders (R&D credit eligible)
    "webdev", "freelance", "consulting", "Upwork",
    # Manufacturing / hardware / DevOps (R&D credit eligible, on mytaxhack.com)
    "manufacturing", "devops", "hardware",
    # Service businesses
    "sweatystartup", "msp", "lawncare",
    # Finance / personal (catches founders asking personal tax questions)
    "personalfinance",
]

REDDIT_KEYWORDS = [
    # R&D Tax Credit — highest value
    "R&D tax credit", "research and development tax credit", "R&D credit",
    "research tax credit", "Section 41", "qualified research expenses",
    "can I claim R&D", "eligible for R&D credit", "software R&D credit",
    # CPA / advisor search — active buying signals
    "need a CPA", "looking for a CPA", "recommend a CPA",
    "find a tax advisor", "looking for a tax advisor",
    "need tax help", "small business CPA", "tax advisor recommendation",
    "hire a tax accountant", "tax consultant recommendation",
    # Tax pain — business owners
    "paying too much in taxes", "tax bill too high", "owe so much taxes",
    "huge tax bill", "surprised by my taxes", "overpaying taxes",
    "generalist CPA", "my CPA doesn't", "accountant doesn't know",
    # Tax strategy
    "lower my taxes", "reduce tax liability", "tax strategy",
    "minimize taxes", "tax savings", "tax optimization",
    # Entity structure
    "S-corp election", "LLC vs S-corp", "should I elect S-corp",
    "LLC tax savings", "switching to S-corp",
    # Self-employment / quarterly
    "1099 taxes", "self-employed taxes", "quarterly taxes",
    "estimated taxes", "quarterly tax payment",
    # Industry-specific ICP signals
    "agency taxes", "SaaS taxes", "ecommerce taxes",
    "software company taxes", "our CPA", "local CPA",
    # Additional mytaxhack.com services
    "409A valuation", "sales tax nexus", "IRS audit", "need a bookkeeper",
]

REDDIT_POST_LIMIT = 25
REDDIT_POLL_INTERVAL_MINUTES = 15

# ── Web Search ────────────────────────────────────────────────────────────────

WEB_SEARCH_QUERIES = [
    # ── Quora ─────────────────────────────────────────────────────────────────
    'site:quora.com "R&D tax credit" qualify startup software',
    'site:quora.com taxes "need a CPA" OR "find a CPA" "small business"',
    'site:quora.com "how do I lower" OR "reduce" "business taxes" LLC owner',
    'site:quora.com "S-corp" taxes save "should I" freelancer consultant',
    'site:quora.com "quarterly taxes" "self employed" confused help',
    'site:quora.com "agency" OR "SaaS" taxes CPA strategy',
    "site:quora.com \"my accountant\" OR \"my CPA\" \"doesn't know\" OR \"overcharging\" business",
    'site:quora.com "R&D credit" software startup "qualify" OR "eligible"',
    'site:quora.com "too much in taxes" business owner CPA strategy',

    # ── Indie Hackers ─────────────────────────────────────────────────────────
    'site:indiehackers.com taxes CPA "R&D" OR "S-corp" OR "strategy"',
    'site:indiehackers.com "paying taxes" OR "tax bill" CPA help advice',
    'site:indiehackers.com "need a CPA" OR "our accountant" taxes',
    'site:indiehackers.com "S-corp" OR "LLC" taxes accountant questions',
    'site:indiehackers.com "R&D tax credit" startup software eligible',

    # ── Hacker News ───────────────────────────────────────────────────────────
    'site:news.ycombinator.com "R&D tax credit" qualify startup',
    'site:news.ycombinator.com taxes CPA "small business" "S-corp" OR "LLC"',

    # ── Stack Exchange (money.stackexchange) ─────────────────────────────────
    'site:money.stackexchange.com "R&D tax credit" qualify startup software',
    'site:money.stackexchange.com "S-corp election" save taxes LLC',
    'site:money.stackexchange.com taxes "small business" CPA strategy reduce',
    'site:money.stackexchange.com "agency" OR "SaaS" OR "freelancer" taxes CPA',

    # ── Shopify Community ─────────────────────────────────────────────────────
    'site:community.shopify.com taxes CPA accountant help',
    'site:community.shopify.com "S-corp" OR "accountant" taxes help',

    # ── Nomad List / ConvertKit Community ────────────────────────────────────
    'site:forum.nomadlist.com taxes CPA accountant US business',
    'site:community.convertkit.com taxes CPA accountant creator business',
]

WEB_RESULTS_PER_QUERY = 8
WEB_POLL_INTERVAL_HOURS = 1

# ── Analysis / Scoring ────────────────────────────────────────────────────────

MIN_RELEVANCE_FOR_ALERT = 70
LOG_ALL_TO_SHEETS = False
MIN_RELEVANCE_FOR_SHEETS = 70

# ── Contact Enrichment ────────────────────────────────────────────────────────
# Only enrich leads that are both hot (score >= threshold) AND flagged should_contact.
# Enrichment calls Apify + Apollo + Hunter — costs money, so gate it carefully.
ENRICH_MIN_SCORE = 70   # Minimum relevance score to trigger enrichment

# ── Google Sheets ─────────────────────────────────────────────────────────────

SHEET_WORKSHEET_NAME = "Leads - 2026-04-24"

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
    # Contact enrichment columns (populated for hot leads only)
    "Email",
    "Email Confidence %",
    "Phone",
    "Phone Type",
    "LinkedIn Profile",
    "Enriched Name",
    "Company",
    "Company Website",
    "Enrichment Source",
]

# ── Company Context (fed to Claude) ──────────────────────────────────────────

TAX_HACK_CONTEXT = """
MyTaxHack is a full-service tax advisory and accounting firm (founded by ex-PricewaterhouseCoopers)
specializing in R&D tax credits, proactive tax strategy, and bookkeeping automation for founder-led SMBs.
Offices in CA, TX, NY, NC. Recognized by Inc. Magazine as #120 fastest-growing private company (2025).

SERVICES OFFERED:
- R&D tax credits (core specialty — AI, SaaS, DevOps, IoT, manufacturing)
- Proactive tax strategy & planning (entity optimization, S-corp, QBI stacking)
- Bookkeeping & accounting setup with automation
- Sales tax compliance & multi-state nexus
- 409A valuations for startups issuing equity
- IRS audit representation
- Entity selection & quarterly estimates
- Payroll / HR advisory

TARGET CLIENTS:
- Industries: SaaS/software, marketing agencies, e-commerce, manufacturing, IoT/hardware,
  DevOps/platform engineering, MarTech/AdTech, professional services, creative agencies,
  IT/MSP, consulting firms, real estate investors
- Stage: Seed-stage startups with employees through Series B; established SMBs
- Revenue: $300K-$20M annual revenue
- Structure: LLC, S-corp, C-corp (not sole proprietors with no employees)
- Decision makers: founder, owner, CEO, COO, CFO, managing partner

HOT LEAD SIGNALS — Score 80-100:
- Founder/owner explicitly asking for a CPA recommendation or saying they need a new CPA
- Complaining their current CPA is too expensive, doesn't understand their industry, or is a generalist
- Asking about R&D tax credits (especially for software, SaaS, IoT, or product development)
- Expressing shock or frustration about a large tax bill
- Asking about S-corp election, LLC vs S-corp, or entity structure for tax savings
- Asking about tax strategy for their specific industry (agency, SaaS, e-commerce, manufacturing)
- Revenue signals: mentions employees, payroll, $300K+, significant revenue
- Founder asking about 409A valuation or startup equity tax implications
- Business owner panicking about an IRS audit notice or audit representation
- Ecommerce/multi-state business asking about sales tax nexus compliance
- Startup with employees asking about payroll taxes, QSB stock, or R&D credit for dev costs

WARM LEAD SIGNALS — Score 70-79:
- Business owner with general tax frustration but not actively seeking a CPA yet
- Asking about quarterly taxes, self-employment taxes with business context
- Questions about tax optimization, deductions, or reducing tax liability for a real business
- Post is from an ICP industry (SaaS, agency, ecommerce, manufacturing) and mentions taxes + CPA
- Manufacturing or IoT company asking about R&D credits for product development costs
- DevOps/infrastructure company asking about software capitalization or qualifying R&D expenses
- Asking about needing a bookkeeper or accounting setup as they scale

DISQUALIFY — Score 0-49:
- W-2 employee asking about personal taxes (no business income)
- Hobbyist, student, side hustler with no real business
- Someone who already has a great CPA and is just asking general questions
- Tax professionals themselves (competitors)
- Posts about tax software (TurboTax, TaxAct) — these are not our clients
- International tax questions (non-US)
- Revenue clearly under $100K or solo freelancer with minimal income

MESSAGING ANGLE: "Your generalist CPA probably doesn't know about R&D credits. Most SMBs
in software/SaaS/agencies qualify and leave $50K-$500K on the table every year.
Book a free consultation at https://mytaxhack.com/consultation"
"""
