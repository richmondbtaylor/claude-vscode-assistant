"""
Central configuration for BrainCX Social Listening Lead Finder.
Target: ANY US service business that handles inbound calls and could benefit
from 24/7 multilingual voice AI — AI receptionist, IVR replacement, call handling.
Goal: 50+ qualified leads per run across 6+ unique channels.
"""

# ── Reddit ────────────────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    # Legal / Immigration
    "legaladvice", "Lawyertalk", "immigration", "ImmigrationLaw",
    "paralegal", "legaltech",
    # Healthcare & Medical
    "medicine", "medicalpractice", "HealthcareWorkers", "Dentistry",
    "Residency", "physicianassistant", "Chiropractic",
    "physicaltherapy", "optometry", "veterinaryprofession",
    # Higher Education
    "highereducation", "college", "university", "admissions",
    "StudentAffairs",
    # Home Services / Trades
    "HVAC", "Plumbing", "HomeImprovement", "electricians",
    "ContractorsOfReddit", "handyman",
    # Hospitality / Auto / Retail Services
    "AutoMechanic", "AutoRepair", "hotels", "restaurantowners",
    # Professional Services / Business
    "smallbusiness", "entrepreneur", "Entrepreneur",
    "financialplanning", "realestate", "Accounting", "consulting",
    # Front desk / reception / scheduling
    "humanresources", "CustomerService", "VirtualAssistants",
    # AI / automation (people exploring solutions)
    "artificial", "ChatGPT", "automation", "nocode", "lowcode",
]

REDDIT_KEYWORDS = [
    # Phone / call volume pain
    "can't keep up with calls", "overwhelmed with calls", "too many calls",
    "phone keeps ringing", "missing calls", "losing leads after hours",
    "calls going to voicemail", "no one answers the phone",
    "front desk overwhelmed", "receptionist overwhelmed",
    "our phones are a nightmare", "drowning in phone calls",
    # Staffing / hiring pain
    "can't afford receptionist", "hard to find receptionist",
    "front desk turnover", "receptionist quit", "need a virtual receptionist",
    "looking for virtual receptionist", "hire a receptionist",
    "staffing shortage", "understaffed front desk", "receptionist called out",
    "can't find reliable front desk",
    # Multilingual / language barrier
    "non-English speaking patients", "language barrier patients",
    "Spanish-speaking clients", "multilingual staff",
    "translation for patients", "interpreter for calls",
    "patients who don't speak English", "non-English speaking clients",
    "bilingual receptionist", "Spanish speaking receptionist",
    # After-hours / 24/7
    "after hours calls", "after-hours scheduling",
    "patients calling after hours", "24/7 answering", "after hours service",
    "calls on weekends", "no coverage after hours", "missed calls after hours",
    # AI / voice / IVR solutions
    "AI receptionist", "AI answering service", "virtual receptionist AI",
    "AI for scheduling", "AI phone system", "voice AI",
    "IVR replacement", "automated answering", "AI for intake",
    "AI for appointment scheduling", "anyone use AI for scheduling",
    # Scheduling specific
    "appointment scheduling software", "missed appointments",
    "no-show problem", "scheduling bottleneck", "patients falling through",
    # Insurance / intake
    "insurance verification calls", "patient intake", "client intake calls",
    # HIPAA / compliance
    "HIPAA compliant scheduling", "HIPAA compliant phone",
]

REDDIT_POST_LIMIT = 25
REDDIT_POLL_INTERVAL_MINUTES = 15

# ── LinkedIn ───────────────────────────────────────────────────────────────────

LINKEDIN_KEYWORDS = [
    "can anyone recommend a virtual receptionist",
    "looking for recommendations answering service",
    "any suggestions for handling call volume",
    "has anyone used AI for scheduling",
    "looking for 24/7 answering solution",
    "can anyone recommend multilingual receptionist",
    "how do you handle non-English speaking clients",
    "anyone used AI receptionist",
    "front desk overwhelmed",
    "can't find good receptionist staff",
    "losing patients after hours",
    "missing calls costing us leads",
    "need to replace our IVR",
    "AI for patient scheduling",
    "bilingual staff hard to find",
]

LINKEDIN_RESULTS_PER_KEYWORD = 5

# ── Facebook / Facebook Groups ─────────────────────────────────────────────────

FACEBOOK_KEYWORDS = [
    "virtual receptionist recommendation",
    "answering service for law firm",
    "AI receptionist",
    "handle after hours calls",
    "multilingual receptionist",
    "front desk overwhelmed",
    "missed patient calls",
    "AI for scheduling",
    "HIPAA compliant phone",
    "IVR replacement",
    "Spanish speaking receptionist",
    "patient intake automation",
    "receptionist keeps quitting",
    "can't afford front desk staff",
]

FACEBOOK_RESULTS_PER_KEYWORD = 15

# ── Twitter / X ────────────────────────────────────────────────────────────────

TWITTER_KEYWORDS = [
    "front desk overwhelmed calls",
    "missing patient calls",
    "can't keep up with calls",
    "need virtual receptionist",
    "losing leads after hours",
    "non-English speaking patients",
    "language barrier clients",
    "AI receptionist",
    "AI for scheduling",
    "voice AI for healthcare",
    "IVR replacement",
    "AI phone system",
    "AI answering service",
    "HIPAA compliant AI",
    "receptionist quit",
    "can't find receptionist",
]

TWITTER_RESULTS_PER_KEYWORD = 5

# ── Job Board Queries (Indeed + LinkedIn Jobs) ────────────────────────────────
# Businesses actively HIRING a receptionist = they have the pain RIGHT NOW.
# These are the hottest possible leads — they're spending money to solve the problem.

JOB_BOARD_QUERIES = [
    # Indeed — medical / dental
    'site:indeed.com "medical receptionist" "full time" USA',
    'site:indeed.com "dental receptionist" "full time"',
    'site:indeed.com "front desk coordinator" (medical OR dental OR clinic)',
    'site:indeed.com "patient coordinator" "front desk"',
    'site:indeed.com "bilingual receptionist" (medical OR legal OR dental)',
    'site:indeed.com "Spanish speaking receptionist"',
    # Indeed — legal
    'site:indeed.com "legal receptionist" OR "law firm receptionist"',
    'site:indeed.com "immigration" "receptionist" OR "intake coordinator"',
    'site:indeed.com "intake coordinator" (legal OR law OR attorney)',
    # Indeed — general service businesses
    'site:indeed.com "veterinary receptionist" "full time"',
    'site:indeed.com "chiropractic receptionist" OR "physical therapy receptionist"',
    'site:indeed.com "front desk receptionist" (HVAC OR plumbing OR contractor)',
    'site:indeed.com "bilingual" "receptionist" OR "customer service" (clinic OR office)',
    # LinkedIn Jobs — medical / dental
    'site:linkedin.com/jobs "medical receptionist" United States',
    'site:linkedin.com/jobs "dental receptionist" United States',
    'site:linkedin.com/jobs "bilingual receptionist" United States',
    'site:linkedin.com/jobs "front desk coordinator" (healthcare OR medical OR clinic)',
    # LinkedIn Jobs — legal
    'site:linkedin.com/jobs "legal receptionist" OR "law firm receptionist" "United States"',
    'site:linkedin.com/jobs "intake coordinator" (law OR legal OR immigration)',
    # LinkedIn Jobs — other service businesses
    'site:linkedin.com/jobs "veterinary receptionist" United States',
    'site:linkedin.com/jobs "bilingual customer service" (clinic OR office OR practice)',
    'site:linkedin.com/jobs "front desk" "Spanish" United States',
]

JOB_BOARD_RESULTS_PER_QUERY = 5

# ── Web Search (Brave / DuckDuckGo) ───────────────────────────────────────────

WEB_SEARCH_QUERIES = [
    # ── Reddit — voice AI / receptionist pain ────────────────────────────────
    'site:reddit.com "front desk overwhelmed" OR "can\'t keep up with calls" (law OR medical OR clinic OR dental OR vet)',
    'site:reddit.com "need a receptionist" OR "virtual receptionist" AI OR automated',
    'site:reddit.com "after hours calls" OR "missing calls" (medical OR law OR dental OR HVAC OR vet)',
    'site:reddit.com "AI receptionist" OR "AI scheduling" recommend OR use OR help',
    'site:reddit.com "non-English speaking" OR "language barrier" (patients OR clients) calls',
    'site:reddit.com "IVR" ("replace" OR "hate" OR "outdated" OR "looking for alternative")',
    'site:reddit.com "HIPAA" "scheduling" OR "phone" (AI OR chatbot OR automated)',
    'site:reddit.com "receptionist quit" OR "can\'t find receptionist" OR "receptionist shortage"',
    'site:reddit.com r/medicalpractice ("calls" OR "front desk" OR "scheduling") (help OR overwhelmed OR AI)',
    'site:reddit.com r/Lawyertalk ("intake" OR "receptionist" OR "calls") (overwhelmed OR help)',
    'site:reddit.com r/smallbusiness ("receptionist" OR "answering service" OR "front desk") help OR recommend',
    'site:reddit.com r/HVAC ("calls" OR "answering service" OR "scheduling") help',
    'site:reddit.com r/Dentistry ("front desk" OR "receptionist" OR "scheduling") help OR overwhelmed',

    # ── LinkedIn — ICP pain ───────────────────────────────────────────────────
    'site:linkedin.com/posts "front desk" ("overwhelmed" OR "can\'t keep up" OR "losing calls")',
    'site:linkedin.com/posts "virtual receptionist" (looking OR need OR recommend)',
    'site:linkedin.com/posts "AI receptionist" OR "AI scheduling" (healthcare OR law OR dental OR vet)',
    'site:linkedin.com/posts "multilingual" ("calls" OR "patients" OR "clients") (staff OR AI)',
    'site:linkedin.com/posts "after hours" (calls OR patients OR leads) (losing OR missing)',
    'site:linkedin.com/posts "IVR" ("replace" OR "outdated" OR "better option")',
    'site:linkedin.com/posts "practice manager" ("calls" OR "scheduling") (struggling OR help)',
    'site:linkedin.com/posts "bilingual" OR "Spanish" (staff OR receptionist) (need OR hire OR hard)',
    'site:linkedin.com/posts "receptionist" ("quit" OR "shortage" OR "can\'t find" OR "turnover")',
    'site:linkedin.com/posts "answering service" (recommend OR looking OR need OR replace)',

    # ── Healthcare forums ─────────────────────────────────────────────────────
    '"medical practice" "front desk" ("overwhelmed" OR "understaffed" OR "missing calls") -site:reddit.com',
    '"dental office" "front desk" ("can\'t keep up" OR "missing calls" OR "after hours") -site:reddit.com',
    '"veterinary" "front desk" ("overwhelmed" OR "missing calls" OR "scheduling") help -site:reddit.com',
    '"chiropractic" ("front desk" OR "receptionist") ("overwhelmed" OR "quit" OR "can\'t find")',
    '"physical therapy" ("receptionist" OR "front desk") ("scheduling" OR "calls") help',

    # ── Legal ─────────────────────────────────────────────────────────────────
    '"immigration attorney" ("intake calls" OR "phone calls") (overwhelmed OR help OR AI)',
    '"law firm" ("virtual receptionist" OR "AI receptionist" OR "answering service") (recommend OR looking)',
    '"small law firm" ("can\'t keep up with calls" OR "need receptionist" OR "front desk")',

    # ── Home Services / Trades ────────────────────────────────────────────────
    '"HVAC" ("answering service" OR "after hours calls" OR "missing calls") help OR recommend',
    '"plumbing" ("after hours" OR "answering service" OR "missing calls") help -site:reddit.com',
    '"contractor" ("after hours calls" OR "answering service" OR "can\'t answer phone")',
    '"home services" ("AI receptionist" OR "virtual receptionist" OR "answering service")',

    # ── Customer complaints = active pain signal ──────────────────────────────
    'site:yelp.com "never answers the phone" OR "can\'t reach them" OR "no one answers" (clinic OR office OR practice)',
    'site:yelp.com "hard to reach" OR "phone always busy" OR "goes to voicemail" (medical OR dental OR law)',
    '"google review" OR "yelp" "never answers" OR "phone issues" (medical practice OR dental OR law firm)',

    # ── Facebook Groups ────────────────────────────────────────────────────────
    'site:facebook.com/groups "front desk" ("overwhelmed" OR "need receptionist") (medical OR law)',
    'site:facebook.com/groups "virtual receptionist" OR "AI receptionist" (recommend OR looking)',
    'site:facebook.com/groups "multilingual" OR "Spanish" (staff OR receptionist) (need OR hire)',
    'site:facebook.com/groups "after hours" (calls OR patients OR leads) (missing OR losing)',

    # ── Twitter / X ───────────────────────────────────────────────────────────
    'site:x.com "front desk" (overwhelmed OR "can\'t keep up") (medical OR law OR clinic)',
    'site:x.com "AI receptionist" OR "AI scheduling" (healthcare OR law OR dental)',
    'site:x.com "missing calls" OR "after hours" (leads OR patients OR clients)',
    'site:x.com "non-English speaking" OR "language barrier" (clients OR patients) calls',
    'site:twitter.com "virtual receptionist" OR "AI phone" (recommend OR looking OR need)',

    # ── Practice management / specialty forums ────────────────────────────────
    '"practice management" ("phone calls" OR "call volume") (overwhelmed OR AI OR help) -site:reddit.com',
    '"office manager" ("calls" OR "receptionist" OR "front desk") (overwhelmed OR quit OR AI)',
    '"dental practice" ("receptionist" OR "front desk") ("shortage" OR "quit" OR "AI") -site:reddit.com',
]

WEB_RESULTS_PER_QUERY = 5
WEB_POLL_INTERVAL_HOURS = 1

# ── Analysis / Scoring ────────────────────────────────────────────────────────

MIN_RELEVANCE_FOR_ALERT = 20
LOG_ALL_TO_SHEETS = False
MIN_RELEVANCE_FOR_SHEETS = 20   # Lower threshold — cast wide net for 50 leads

# ── Google Sheets ─────────────────────────────────────────────────────────────

SHEET_WORKSHEET_NAME = "Leads"

SHEET_COLUMNS = [
    "Timestamp",
    "Platform",
    "Source",
    "URL",
    "Author / Business",
    "Title / Snippet",
    "Relevance Score",
    "Lead Score",
    "ICP Category",
    "Business Type",
    "Pain Point",
    "Why It Fits",
    "Urgency",
    "Decision Maker",
    "Competitor Mentioned",
    "Is Job Posting",
    "Phone",
    "Website",
    "DM Name",
    "DM Title",
    "Email",
    "Claude Reasoning",
    "Status",
]

# ── Company Context (fed to Claude) ──────────────────────────────────────────

BRAINCX_CONTEXT = """
BrainCX builds multilingual voice AI for US service businesses — AI receptionists and IVR replacements
that handle inbound calls 24/7 in any language (English, Spanish, and more). Core use cases:

── CORE PRODUCT ──
- AI receptionist: answers calls, schedules appointments, handles FAQs, 24/7
- IVR replacement: replaces outdated phone trees with natural conversational AI
- Multilingual call handling: serves Spanish-speaking (and other) clients without a bilingual hire
- After-hours coverage: no lead or patient call goes unanswered
- Appointment reminders / patient follow-up: automated outbound calls

── ANY SERVICE BUSINESS IS A FIT if they have:
  1. Inbound call volume they struggle to keep up with, OR
  2. A need for after-hours phone coverage, OR
  3. Non-English speaking clients/patients they can't serve well over the phone, OR
  4. Difficulty hiring or retaining front desk / receptionist staff, OR
  5. An outdated IVR or phone tree they want to replace

── STRONGEST ICP CATEGORIES (score higher) ──
- Immigration attorneys / law firms — multilingual clients, high intake call volume
- Healthcare (medical, dental, chiropractic, physical therapy, veterinary) — scheduling, insurance, patient calls
- Home services (HVAC, plumbing, electrical, contractors) — after-hours emergency calls, high volume
- Higher education (universities, community colleges) — enrollment call volume
- Professional services (financial advisors, title companies, auto dealerships, real estate)

── JOB POSTING SIGNAL ──
If the post is a job listing for "receptionist", "front desk", or "intake coordinator",
this is a HOT lead. The company is actively spending money to solve the exact problem BrainCX solves.
Score these 75-90. Flag as is_job_posting = true.

── REVIEW/COMPLAINT SIGNAL ──
If the post is a customer review or complaint about a business being hard to reach, not answering phones,
or having bad phone service — this is a real pain signal. The business has an active problem.
Score these 60-80 depending on specificity.

── NOT A FIT ──
- Individual consumers (not business owners/operators)
- Pure e-commerce with no phone intake
- B2C personal problems
"""
