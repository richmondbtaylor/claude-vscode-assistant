# config.py — HubSpot SMB Lead Research Agent

# ── Reddit ────────────────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    "CRM", "RevOps",
    "smallbusiness", "Entrepreneur",
    "sales", "marketing",
    "b2b", "SaaS",
    "salesforce", "zoho", "pipedrive",
    "startups", "agency", "freelance",
    "consulting", "realestate",
    "InsuranceAgent", "msp",
    "recruiting", "digitalnomad",
]

REDDIT_KEYWORDS = [
    # Direct CRM need / no CRM yet
    "need a CRM", "looking for a CRM", "recommend a CRM", "what CRM",
    "which CRM", "best CRM", "CRM for small business", "CRM for startup",
    "CRM recommendation", "CRM suggestions", "trying to find a CRM",
    "do I need a CRM", "should I use a CRM", "first CRM",
    "we don't have a CRM", "no CRM", "using spreadsheets for sales",
    "using google sheets for clients", "tracking clients in excel",

    # CRM switching intent
    "switching CRM", "replacing CRM", "looking for a new CRM",
    "migrating from CRM", "outgrown our CRM", "changing CRM",
    "CRM migration", "moving away from", "leaving our CRM",

    # CRM pain / frustration
    "CRM too expensive", "CRM too complicated", "CRM too complex",
    "hate our CRM", "frustrated with CRM", "CRM not working",
    "CRM adoption", "team not using CRM", "nobody uses our CRM",
    "sales team ignores CRM", "reps not logging in CRM",

    # Salesforce pain
    "salesforce too expensive", "salesforce too complex", "leaving salesforce",
    "salesforce alternative", "replace salesforce", "salesforce overkill",
    "salesforce small business", "salesforce too big", "dropping salesforce",
    "cancel salesforce", "salesforce pricing", "salesforce overwhelming",

    # Zoho pain
    "zoho crm", "zoho alternative", "leaving zoho", "zoho problems",
    "zoho support", "zoho confusing", "zoho pricing",

    # Pipedrive pain
    "pipedrive alternative", "leaving pipedrive", "pipedrive missing",
    "pipedrive limitations", "outgrown pipedrive", "pipedrive problems",

    # Other CRM pain
    "monday crm", "copper crm", "keap alternative", "keap problems",
    "activecampaign alternative", "freshsales", "insightly alternative",
    "close crm alternative", "streak crm",

    # Industry-specific CRM needs
    "CRM for real estate", "CRM for insurance", "CRM for agency",
    "CRM for consulting", "CRM for recruiting", "CRM for freelancers",
    "CRM for MSP", "CRM for marketing agency", "CRM for IT company",
    "affordable CRM", "easy to use CRM", "simple CRM",
    "CRM with marketing automation", "all in one CRM",
]

# ── LinkedIn ──────────────────────────────────────────────────────────────────

LINKEDIN_KEYWORDS = [
    "switching CRM recommendation small business",
    "Salesforce too expensive looking for alternative",
    "CRM that actually gets adopted by sales team",
    "outgrown our current CRM need upgrade",
    "leaving Zoho CRM what do you recommend",
    "best CRM for SMB team under 50 people",
    "CRM migration tips small business",
    "sales team not using CRM adoption problem",
    "affordable CRM alternative to Salesforce",
    "what CRM do you use for your small business",
]

LINKEDIN_RESULTS_PER_KEYWORD = 5

# ── Facebook / Facebook Groups ────────────────────────────────────────────────

FACEBOOK_KEYWORDS = [
    "CRM recommendation small business",
    "switching from Salesforce too expensive",
    "best CRM for small team",
    "CRM alternative affordable",
    "leaving Zoho need new CRM",
]

FACEBOOK_RESULTS_PER_KEYWORD = 5

# ── Twitter / X ───────────────────────────────────────────────────────────────

TWITTER_KEYWORDS = [
    "switching CRM",
    "Salesforce too expensive",
    "CRM recommendation small business",
    "hate our CRM",
    "Zoho CRM alternative",
    "Pipedrive alternative",
]

TWITTER_RESULTS_PER_KEYWORD = 5

# ── Web Search (Brave / DuckDuckGo) ──────────────────────────────────────────

WEB_SEARCH_QUERIES = [
    # Indie Hackers — founders evaluating CRMs
    'CRM recommendation startup site:indiehackers.com',
    'switching CRM small team site:indiehackers.com',
    'salesforce alternative site:indiehackers.com',
    'what CRM do you use site:indiehackers.com',

    # Quora — broader queries (no exact-phrase wrapping)
    'what CRM small business recommendation site:quora.com',
    'salesforce too expensive alternative site:quora.com',
    'zoho crm alternative recommendation site:quora.com',
    'best CRM startup site:quora.com',

    # General web — people actively switching or seeking
    '"need a CRM" small business -site:reddit.com -site:hubspot.com',
    '"switching from salesforce" small business CRM -site:reddit.com',
    '"salesforce too expensive" CRM alternative -site:reddit.com',
    '"looking for a CRM" small business team -site:reddit.com',
    '"what CRM" recommendation "small business" -site:reddit.com -site:hubspot.com',
    'salesforce alternative small business "switching" -site:reddit.com',
    'zoho CRM problems alternative -site:reddit.com',
    'pipedrive alternative small business -site:reddit.com',
    '"outgrown" CRM small business -site:reddit.com',
    'CRM for agency recommendation -site:reddit.com',
    'CRM for MSP managed service -site:reddit.com',
    '"CRM migration" small business team -site:reddit.com',
    'leaving salesforce CRM recommendation small business -site:reddit.com',
]

WEB_RESULTS_PER_QUERY = 8

# ── Analysis / Scoring ────────────────────────────────────────────────────────

MIN_RELEVANCE_FOR_SHEETS = 25
LOG_ALL_TO_SHEETS = False

REDDIT_POLL_INTERVAL_MINUTES = 15
WEB_POLL_INTERVAL_HOURS = 1

# ── Google Sheets ─────────────────────────────────────────────────────────────

SHEET_WORKSHEET_NAME = "Leads"

SHEET_COLUMNS = [
    "Timestamp",
    "Post Date",
    "Platform",
    "Source",
    "URL",
    "Author",
    "Title / Snippet",
    "Relevance Score",
    "Lead Score",
    "ICP Category",
    "Business Type",
    "Pain Point Type",
    "Pain Point Description",
    "Why HubSpot Fits",
    "Urgency",
    "Decision Maker",
    "Current CRM",
    "Cross Platform",
    "Claude Reasoning",
    "Status",
]

# ── Company Context (fed to Claude) ──────────────────────────────────────────

HUBSPOT_SMB_CONTEXT = """
We are finding leads FOR HubSpot — specifically SMBs (under $10M revenue) that do NOT currently use
HubSpot and are experiencing pain with their existing CRM or actively looking for a new CRM.

THE GOAL:
Find small and mid-size businesses (typically 5-200 employees, under $10M revenue) who are:
- Unhappy with their current CRM (Salesforce, Zoho, Pipedrive, Monday, Copper, Keap, etc.)
- Actively looking to switch or replace their CRM
- Asking for CRM recommendations
- Expressing frustration with the cost/complexity of their current CRM
- Starting fresh and evaluating CRM options for the first time

WHY HUBSPOT IS THE SOLUTION:
- All-in-one CRM: sales, marketing, and service in one platform
- Easy to adopt — sales teams actually use it (unlike Salesforce)
- Free tier available, scales with the business
- Strong automation and marketing tools built in
- Much more affordable than Salesforce for SMBs
- Better UX than Zoho, more features than Pipedrive

TARGET CUSTOMERS (ICPs):
- SMB founders/owners frustrated with Salesforce costs or complexity
- Sales managers whose team ignores the current CRM
- RevOps leads evaluating CRM replacements
- Startups outgrowing spreadsheets or a basic CRM
- Businesses leaving Salesforce, Zoho, Pipedrive, or other mid-tier CRMs

PERFECT SIGNAL — someone is an ideal lead if they:
- Complain Salesforce is too expensive or overkill for their size
- Say their team doesn't use or adopt their current CRM
- Ask for a CRM recommendation for a small business/startup
- Say they're switching or migrating away from a CRM
- Complain about Zoho's UI/support, Pipedrive's missing features, etc.
- Are evaluating CRMs and comparing options

NOT a lead (disqualify):
- People who already use HubSpot (they're already a customer)
- Enterprise companies (500+ employees, clearly >$10M revenue)
- HubSpot consultants or implementation agencies
- People asking how to use HubSpot (already a user)
- Individual consumers (not B2B)

CURRENT CRMs TO WATCH (sources of dissatisfied users):
- Salesforce — too expensive and complex for SMBs
- Zoho CRM — clunky UI, poor support, confusing pricing
- Pipedrive — missing marketing automation and advanced features
- Monday.com CRM — not a true CRM, limited sales features
- Copper — Google Workspace-only, limited features
- Keap / Infusionsoft — overly complex, dated
- ActiveCampaign — email-first, weak CRM features
- Freshsales — less mature ecosystem
- Insightly, Streak, Close.io — niche tools with limitations
"""
