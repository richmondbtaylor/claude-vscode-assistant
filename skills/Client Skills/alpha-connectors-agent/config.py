"""
Central configuration for Alpha Connectors Deal Flow Agent.
Monitors 6 verticals for buying signals within the last 7 days.
"""

# ── Signal Freshness ──────────────────────────────────────────────────────────

MAX_SIGNAL_AGE_DAYS = 7

# ── Vertical Definitions ──────────────────────────────────────────────────────

VERTICALS = {
    "tech_projects": {
        "label": "Tech Projects",
        "signals": ["Series A", "Series B", "Series C", "seed round", "raised $", "closed funding",
                    "accelerator", "Y Combinator", "Techstars", "venture round", "pre-seed",
                    "growth round", "capital raise", "equity financing"],
    },
    "real_estate": {
        "label": "Real Estate",
        "signals": ["construction permit", "building permit", "land acquisition", "bridge loan",
                    "project financing", "distressed asset", "foreclosure", "note purchase",
                    "ground-up development", "entitlement", "mezzanine financing",
                    "real estate debt", "property acquisition"],
    },
    "renewables_data_centers": {
        "label": "Renewables / Data Centers",
        "signals": ["power purchase agreement", "PPA", "solar project", "wind project",
                    "data center financing", "renewable energy project", "federal grant",
                    "DOE grant", "IRA financing", "commercial solar", "battery storage",
                    "hyperscale", "colocation financing", "clean energy financing"],
    },
    "gov_contracts": {
        "label": "Gov Contract Holders",
        "signals": ["contract award", "IDIQ", "GSA schedule", "prime contractor",
                    "government contract", "federal contract", "DOD contract", "SBIR",
                    "accounts receivable financing", "receivables financing",
                    "contract-based financing", "government award", "USASpending"],
    },
    "startup_founders": {
        "label": "Startup Founders",
        "signals": ["thrilled to announce", "excited to share", "we raised", "just closed",
                    "new advisor", "joined as advisor", "strategic advisor", "fundraising",
                    "looking for investors", "angel round", "seeking investment",
                    "founder update", "we're raising"],
    },
    "capital_partners": {
        "label": "Capital Partners",
        "signals": ["deploying capital", "looking to invest", "investment mandate",
                    "active mandate", "thesis", "deal flow", "seeking opportunities",
                    "family office", "single family office", "capital partner",
                    "co-invest", "co-investment", "allocation", "investment committee"],
    },
}

# ── LinkedIn Queries (per vertical) ──────────────────────────────────────────

LINKEDIN_KEYWORDS = [
    # Tech Projects
    "just closed our Series A",
    "thrilled to announce Series B",
    "we raised Series A",
    "closed seed round",
    "accelerator program accepted",
    "YC batch announcement",
    # Real Estate
    "acquired land for development",
    "closed bridge loan real estate",
    "new construction project announced",
    "real estate project financing",
    "distressed property acquisition",
    # Renewables / Data Centers
    "signed power purchase agreement",
    "PPA agreement signed",
    "solar project announcement",
    "data center expansion financing",
    "renewable energy deal closed",
    "DOE grant awarded",
    # Gov Contracts
    "contract award announcement",
    "awarded federal contract",
    "new government contract",
    "IDIQ award",
    "prime contractor award",
    # Startup Founders
    "we are fundraising",
    "looking for investors",
    "new advisor joined",
    "just announced our raise",
    "seeking angel investment",
    # Capital Partners
    "actively deploying capital",
    "investment mandate",
    "looking for deal flow",
    "family office mandate",
    "seeking co-investment",
    "open to co-invest",
]

LINKEDIN_RESULTS_PER_KEYWORD = 5

# ── Twitter / X Queries ───────────────────────────────────────────────────────

TWITTER_KEYWORDS = [
    # Tech
    "just closed Series A",
    "raised Series B",
    "seed round closed",
    "accelerator announcement",
    # Real Estate
    "bridge loan real estate",
    "real estate project financing",
    "distressed asset acquisition",
    # Renewables
    "PPA signed",
    "power purchase agreement",
    "solar project financing",
    "data center deal",
    # Gov Contracts
    "federal contract award",
    "government contract announcement",
    "contract award IDIQ",
    # Founders
    "we are raising",
    "looking for investors startup",
    "new advisor announcement",
    # Capital Partners
    "deploying capital",
    "family office investing",
    "deal flow mandate",
    "co-investment opportunity",
]

TWITTER_RESULTS_PER_KEYWORD = 5

# ── Web Search Queries ────────────────────────────────────────────────────────

WEB_SEARCH_QUERIES = [
    # ── Tech Projects: Crunchbase / TechCrunch / press ───────────────────────
    'site:techcrunch.com "Series A" OR "Series B" raised funding 2026',
    'site:crunchbase.com "Series A" OR "Series B" round closed 2026',
    '"raised" "Series A" OR "Series B" million 2026 -site:reddit.com',
    'site:businesswire.com "Series A" OR "Series B" funding round 2026',
    'site:prnewswire.com "Series A" OR "Series B" funding round 2026',
    'site:techcrunch.com accelerator OR "Y Combinator" OR Techstars batch 2026',

    # ── Real Estate: permits, project debt ───────────────────────────────────
    'site:linkedin.com/posts "bridge loan" OR "construction loan" real estate 2026',
    '"real estate" "project financing" OR "construction financing" announced 2026 -site:reddit.com',
    'site:businesswire.com "real estate" "financing" OR "loan" OR "acquisition" 2026',
    'site:prnewswire.com "real estate" "project" "financing" OR "debt" 2026',
    '"distressed" "real estate" acquisition OR financing 2026 -site:reddit.com',
    'site:linkedin.com/posts "land acquisition" OR "ground-up development" financing',

    # ── Renewables / Data Centers ────────────────────────────────────────────
    'site:prnewswire.com "power purchase agreement" OR "PPA" signed 2026',
    'site:businesswire.com "power purchase agreement" OR "PPA" signed 2026',
    'site:energy.gov "grant" OR "award" solar OR wind OR "data center" 2026',
    '"DOE grant" OR "IRA financing" renewable energy project 2026',
    'site:prnewswire.com "data center" financing OR construction 2026',
    'site:businesswire.com "solar project" OR "wind project" financing 2026',
    '"commercial solar" "PPA" OR "financing" announced 2026 -site:reddit.com',

    # ── Gov Contracts ─────────────────────────────────────────────────────────
    'site:usaspending.gov contract award 2026',
    'site:sam.gov "contract award" 2026',
    'site:businesswire.com "contract award" OR "IDIQ" government 2026',
    'site:prnewswire.com "federal contract" OR "government contract" awarded 2026',
    '"prime contractor" "contract award" OR "IDIQ" 2026 -site:reddit.com',
    '"receivables financing" "government contract" 2026 -site:reddit.com',

    # ── Startup Founders ──────────────────────────────────────────────────────
    'site:linkedin.com/posts "we raised" OR "just closed" OR "thrilled to announce" round 2026',
    'site:linkedin.com/posts "new advisor" OR "joined as advisor" OR "strategic advisor" 2026',
    'site:x.com "we raised" OR "closed our round" startup 2026',
    'site:x.com "new advisor" OR "thrilled to announce" startup funding 2026',
    '"looking for investors" site:linkedin.com OR site:x.com 2026',

    # ── Capital Partners ──────────────────────────────────────────────────────
    'site:linkedin.com/posts "deploying capital" OR "investment mandate" 2026',
    'site:linkedin.com/posts "family office" "looking to invest" OR "deal flow" 2026',
    'site:linkedin.com/posts "co-investment" OR "co-invest" opportunity 2026',
    'site:x.com "family office" "deploying" OR "mandate" OR "deal flow" 2026',
    '"single family office" "investment mandate" OR "deal flow" 2026 -site:reddit.com',
    'site:linkedin.com/posts "capital partner" "seeking" OR "active mandate" 2026',
]

WEB_RESULTS_PER_QUERY = 5
WEB_POLL_INTERVAL_HOURS = 2

# ── Scoring Thresholds ────────────────────────────────────────────────────────

MIN_RELEVANCE_FOR_ALERT = 40
MIN_RELEVANCE_FOR_SHEETS = 40
ENRICH_MIN_SCORE = 70

# ── Google Sheets ─────────────────────────────────────────────────────────────

SHEET_WORKSHEET_NAME = "Deal Signals"

SHEET_COLUMNS = [
    "Timestamp",
    "Vertical",
    "Signal Type",
    "Platform",
    "URL",
    "Author / Company",
    "Headline / Snippet",
    "Deal Size Estimate",
    "Relevance Score",
    "Urgency",
    "Decision Maker",
    "Signal Age (days)",
    "Connection Angle",
    "Pain / Need",
    "Suggested Intro",
    "Should Contact",
    "Claude Reasoning",
    "Status",
    "Contacted Date",
    "Meeting Booked",
    # Enrichment
    "Email",
    "Phone",
    "LinkedIn Profile",
    "Enriched Name",
    "Company",
    "Company Website",
]

# ── Alpha Connectors ICP Context (fed to Claude) ─────────────────────────────

ALPHA_CONNECTORS_CONTEXT = """
Alpha Connectors is a deal origination and capital introduction firm run by Mike Owen.
They connect companies actively seeking capital or deal partnerships with the right capital partners.

Alpha Connectors works across 6 verticals. Score each signal for ONE primary vertical:

1. TECH PROJECTS — Series A/B raises, accelerator graduates, venture activity.
   Ideal signal: company just announced a raise or is in active fundraising mode.

2. REAL ESTATE — Permitting, project debt, bridge loans, distressed assets.
   Ideal signal: developer/operator announcing new project, financing need, or acquisition.

3. RENEWABLES / DATA CENTERS — PPA agreements, commercial-scale solar/wind, federal grants.
   Ideal signal: project company announcing PPA, grant award, or seeking project financing.

4. GOV CONTRACT HOLDERS — New contract awards, IDIQ vehicles, receivables financing.
   Ideal signal: company just awarded a government contract and may need working capital/receivables financing.

5. STARTUP FOUNDERS — Active fundraising posts, advisor changes, growth announcements.
   Ideal signal: founder openly discussing fundraise, new advisor join, or investor search.

6. CAPITAL PARTNERS — Mandate posts, thesis activity, family offices deploying capital.
   Ideal signal: investor or family office announcing active mandate or seeking deal flow.

IMPORTANT scoring rules:
- Only score signals published within the last 7 days. Age reduces score sharply.
- Score HIGHER when the author is a decision-maker (founder, GP, principal, CFO).
- Score HIGHER when a specific dollar amount, deal size, or mandate is mentioned.
- Score LOWER for industry news articles, analyst commentary, or generic thought leadership.
- Provide a CONNECTION ANGLE: one specific reason Alpha Connectors should reach out now.
- The goal is 100-250 qualified leads per month across all 6 verticals.
"""
