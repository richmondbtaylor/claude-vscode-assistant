"""
Central configuration for Bishop AI Research Agent.
Edit these lists to tune what the agent monitors and how sensitive it is.
"""

# ── Reddit ────────────────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    # AI / Automation focused
    "artificial", "AIAutomation", "n8n", "zapier", "automation",
    "nocode", "lowcode", "ChatGPT", "PromptEngineering",
    "AutoGPT", "LangChain", "LocalLLaMA", "ClaudeAI",
    "OpenAI", "AIAssistants", "mcp",
    # Business / Entrepreneur
    "entrepreneur", "Entrepreneur", "smallbusiness", "startups",
    "SaaS", "agency", "consulting", "business",
    "EntrepreneurRideAlong", "microsaas", "Bootstrapped",
    # Marketing / Sales / Ops
    "marketing", "DigitalMarketing", "PPC", "SEO",
    "sales", "socialmedia", "content_marketing", "copywriting",
    "customerservice", "CustomerSuccess", "Operations",
    # E-commerce / Professional services
    "ecommerce", "FulfillmentByAmazon", "Shopify",
    "realtors", "legaltech", "Accounting", "Bookkeeping",
    "humanresources", "projectmanagement",
    # Freelance / Remote / Hiring
    "forhire", "hiring", "WorkOnline", "freelance",
    "digitalnomad", "VirtualAssistants", "webdev",
    # Adjacent
    "productivity", "Notion", "zapier", "MakeApp",
]

REDDIT_KEYWORDS = [
    # Direct buying intent
    "AI automation", "automate with AI", "AI workflow",
    "need help automating", "looking for AI", "hire AI",
    "AI agency", "AI consultant", "AI freelancer",
    "automate my business", "AI implementation",
    "need someone to build", "looking to hire",
    "recommend an AI", "AI expert for hire",
    # Tool-specific (in-market signals)
    "workflow automation", "business automation", "ChatGPT automation",
    "GPT workflow", "n8n help", "zapier alternative", "Make automation",
    "GoHighLevel AI", "HubSpot automation", "AI for CRM",
    "AI agent for my business", "build me an AI",
    # Pain points Bishop AI solves
    "AI for my business", "AI tools recommendation",
    "automate repetitive", "save time with AI", "AI strategy",
    "AI chatbot for business", "AI for customer service",
    "AI for marketing", "AI for sales", "AI for operations",
    "drowning in manual", "too much manual work",
    "overwhelmed with tasks", "need to scale",
    # Education / Training signals
    "learn AI automation", "AI training", "AI course",
    "AI workshop", "implement AI", "AI onboarding",
    "teach my team AI", "AI for my team",
    # Prompt Anything signals — people struggling with prompting
    "prompt engineering", "better prompts", "ChatGPT not working",
    "AI giving bad results", "how to prompt", "prompt help",
    "ChatGPT useless", "AI outputs are bad", "get better results from AI",
    "prompt template", "AI not understanding me", "ChatGPT keeps getting it wrong",
    "Claude not giving", "Gemini not helpful", "AI prompt tips",
]

REDDIT_POST_LIMIT = 25
REDDIT_POLL_INTERVAL_MINUTES = 15

# ── LinkedIn ───────────────────────────────────────────────────────────────────
# These are phrased to surface PERSONAL posts, not thought-leadership articles.
# "can anyone recommend", "has anyone used", "any suggestions" only appear in
# real posts — not in blog posts or agency marketing content.

LINKEDIN_KEYWORDS = [
    # Personal help requests — automation/AI
    "can anyone recommend AI automation",
    "can anyone recommend n8n OR zapier OR make.com",
    "looking for recommendations AI workflow",
    "any suggestions for automating",
    "has anyone used n8n for",
    "has anyone tried automating",
    "anyone know a good AI consultant",
    "anyone else struggling with automation",
    "need help automating",
    "what do you recommend for AI automation",
    # Personal help requests — AI tools/prompting
    "can anyone recommend a prompt",
    "ChatGPT keeps giving me",
    "AI keeps giving me wrong",
    "why does ChatGPT keep",
    "how do I get better results from ChatGPT",
    "my prompts aren't working",
    "anyone else frustrated with ChatGPT",
    "AI outputs are terrible",
    "how to get ChatGPT to",
    # Hiring / looking for help
    "looking to hire someone to build",
    "looking for a freelancer AI",
    "need someone who knows n8n",
    "need someone who knows zapier",
    "anyone available to help build",
]

LINKEDIN_RESULTS_PER_KEYWORD = 5

# ── Facebook / Facebook Groups ─────────────────────────────────────────────────
# Public groups scraped via Playwright — DDG cannot index private group content.

FACEBOOK_GROUPS = [
    "https://www.facebook.com/groups/aiautomationagency",
    "https://www.facebook.com/groups/n8ncommunity",
    "https://www.facebook.com/groups/makecommunity",
    "https://www.facebook.com/groups/chatgptusers",
    "https://www.facebook.com/groups/artificialintelligenceai",
    "https://www.facebook.com/groups/automationrockstars",
    "https://www.facebook.com/groups/zapierautomation",
    "https://www.facebook.com/groups/aiforsmallbusiness",
    "https://www.facebook.com/groups/promptengineering",
    "https://www.facebook.com/groups/gohighlevelcommunity",
]

FACEBOOK_POSTS_PER_GROUP = 20   # How many recent posts to scan per group

FACEBOOK_KEYWORDS = [
    "help", "need", "recommend", "looking for", "struggling",
    "automate", "AI", "ChatGPT", "n8n", "zapier", "make",
    "workflow", "automation", "prompt", "consultant", "hire",
]

# ── Twitter / X ────────────────────────────────────────────────────────────────

TWITTER_KEYWORDS = [
    # Direct buying intent
    "need AI automation help",
    "looking for AI consultant",
    "AI workflow help",
    "automate my business AI",
    "AI chatbot for business",
    "hire AI developer",
    "AI agency",
    "AI for my business",
    "automate repetitive tasks",
    "AI implementation help",
    "need someone to build AI",
    # Prompt Anything
    "ChatGPT not working",
    "better prompts",
    "AI giving bad results",
    "how to prompt ChatGPT",
    "prompt engineering help",
    "Claude giving bad results",
    "AI outputs generic",
]

TWITTER_RESULTS_PER_KEYWORD = 5

# ── Web Search (DuckDuckGo — covers LinkedIn, Quora, Twitter, forums, etc.) ───

WEB_SEARCH_QUERIES = [
    # ── OpenAI Community (real people asking for help) ────────────────────────
    'site:community.openai.com "looking for" AI automation consultant OR developer OR agency',
    'site:community.openai.com "need help" automate OR workflow OR business',
    'site:community.openai.com "hire" OR "recommend" AI developer OR consultant OR expert',
    'site:community.openai.com "I need" AI agent OR automation OR workflow built',
    'site:community.openai.com "my business" automate OR AI workflow OR chatbot',

    # ── n8n Community ─────────────────────────────────────────────────────────
    'site:community.n8n.io "need help" OR "looking for" workflow OR automation OR client',
    'site:community.n8n.io "hire" OR "freelancer" OR "consultant" build workflow',
    'site:community.n8n.io "my business" OR "our company" automation help',

    # ── Make (Integromat) Community ───────────────────────────────────────────
    'site:community.make.com "need help" OR "looking for" automation OR AI',
    'site:community.make.com "hire" OR "consultant" OR "freelancer" build',

    # ── Zapier Community ──────────────────────────────────────────────────────
    'site:community.zapier.com "need help" OR "looking for" automation OR AI workflow',
    'site:community.zapier.com "hire" OR "consultant" build zap OR automation',

    # ── Indie Hackers ─────────────────────────────────────────────────────────
    'site:indiehackers.com "AI automation" OR "automate" need help OR looking for OR hire',
    'site:indiehackers.com "AI consultant" OR "AI agency" recommend OR need OR hire',
    'site:indiehackers.com "automate my" OR "AI workflow" struggling OR help',

    # ── Hacker News (Ask HN / hiring threads) ─────────────────────────────────
    'site:news.ycombinator.com "Ask HN" AI automation OR workflow help OR hire',
    'site:news.ycombinator.com "who wants to be hired" AI automation OR workflow OR agent',
    'site:news.ycombinator.com "looking for" AI consultant OR automation expert OR AI agency',

    # ── Stack Exchange / Stack Overflow ───────────────────────────────────────
    'site:stackoverflow.com "looking for" OR "hire" AI automation consultant OR workflow expert',
    'site:softwareengineering.stackexchange.com "AI automation" OR "AI workflow" help business',

    # ── Facebook Groups (some are indexed) ───────────────────────────────────
    'site:facebook.com/groups "AI automation" "need help" OR "looking for" OR "can anyone"',
    'site:facebook.com "AI agent" OR "AI consultant" "looking for" OR "need someone" OR "hire"',
    'site:facebook.com/groups "automate my business" OR "AI workflow" help',

    # ── GoHighLevel / CRM communities ─────────────────────────────────────────
    'site:community.gohighlevel.com "AI" OR "automation" need help OR looking for OR hire',
    '"GoHighLevel" "AI" "need help" OR "looking for" OR "hire" -site:reddit.com',

    # ── Prompt Anything — people struggling with AI prompting ────────────────
    '"how do I get better results" ChatGPT OR Claude OR Gemini -site:reddit.com',
    '"ChatGPT keeps" giving bad OR wrong OR useless OR generic results -site:reddit.com',
    '"my prompts" "not working" OR "not good" OR "AI ignores" -site:reddit.com',
    '"how to write better prompts" help OR frustrated -site:reddit.com',
    '"AI outputs" "not good" OR "generic" OR "off" help improve -site:reddit.com',
    'site:community.openai.com "my prompts" OR "better prompts" help OR struggling OR frustrated',
    'site:community.openai.com "getting bad results" OR "not understanding" OR "ignoring my instructions"',
    '"prompt engineering" "where to start" OR "need help" OR "how do I" -site:reddit.com',
    '"AI not giving me" what I want OR need help prompting -site:reddit.com',

    # ── General high-intent forum posts ──────────────────────────────────────
    '"need help with AI automation" -site:reddit.com -site:linkedin.com',
    '"looking for AI automation" consultant OR agency OR expert -site:reddit.com',
    '"hire AI automation" expert OR agency OR freelancer -site:reddit.com',
    '"need someone to build" AI workflow OR agent OR chatbot -site:reddit.com',
    '"AI chatbot" "help me build" OR "need someone to build" -site:reddit.com',
    '"automate my business" "need help" OR "looking for" AI -site:reddit.com',
    '"AI implementation" "need help" OR "struggling" -site:reddit.com',
    '"AI for my business" "where to start" OR "need help" -site:reddit.com',
    '"wasting time" "manual" automate AI -site:reddit.com',
    '"overwhelmed" automate AI business help -site:reddit.com',
    '"AI agent" "my business" help OR build OR hire -site:reddit.com',

    # ── LinkedIn — high-intent posts ──────────────────────────────────────────
    'site:linkedin.com/posts "AI automation" "need help" OR "looking for" OR "hire"',
    'site:linkedin.com/posts "automate my business" OR "AI workflow" help OR struggling',
    'site:linkedin.com/posts "AI consultant" OR "AI agency" looking for OR recommend',
    'site:linkedin.com/posts "n8n" OR "zapier" OR "make.com" help OR struggling OR need',
    'site:linkedin.com/posts "AI chatbot" "need" OR "build" OR "help" business',
    'site:linkedin.com/posts "prompt engineering" frustrated OR help OR struggling',
    'site:linkedin.com/posts "ChatGPT" "not working" OR "bad results" OR "generic"',
    'site:linkedin.com/posts "AI for my team" OR "AI training" OR "AI workshop" help',
    'site:linkedin.com/posts "automate" "manual tasks" OR "repetitive" help OR need',
    'site:linkedin.com/posts "AI agent" "my business" OR "our company" help OR need',

    # ── Facebook Groups — public indexed content ───────────────────────────────
    'site:facebook.com/groups "AI automation" "need help" OR "can anyone" OR "recommend"',
    'site:facebook.com/groups "automate my business" AI help OR struggling',
    'site:facebook.com/groups "AI chatbot" "help me build" OR "need someone"',
    'site:facebook.com/groups "n8n" OR "zapier" OR "make.com" help OR looking for',
    'site:facebook.com/groups "prompt engineering" OR "better prompts" help OR frustrated',
    'site:facebook.com/groups "ChatGPT" "not working" OR "bad results" OR "generic output"',
    'site:facebook.com/groups "AI workflow" "need help" OR "looking for" OR "hire"',
    'site:facebook.com/groups "AI for my business" OR "AI tools" recommend OR help',
    'site:facebook.com/groups "automate" "manual" OR "repetitive" AI help OR need',
    'site:facebook.com/groups "AI consultant" OR "AI expert" hire OR recommend OR need',

    # ── Twitter / X — public posts ────────────────────────────────────────────
    'site:x.com "AI automation" "need help" OR "looking for" OR "anyone know"',
    'site:x.com "automate my business" AI help OR struggling OR need',
    'site:x.com "AI consultant" OR "AI agency" looking for OR hire OR recommend',
    'site:x.com "ChatGPT" "not working" OR "bad results" OR "useless" OR "generic"',
    'site:x.com "better prompts" OR "prompt engineering" help OR frustrated OR anyone',
    'site:x.com "n8n" OR "zapier" help OR struggling OR "need someone"',
    'site:x.com "AI chatbot" "my business" OR "for my" help OR build OR need',
    'site:x.com "AI giving" "bad" OR "wrong" OR "generic" results help',
    'site:twitter.com "AI automation" "need help" OR "looking for" OR "hire"',
    'site:twitter.com "automate" "my business" AI help OR struggling',
]

WEB_RESULTS_PER_QUERY = 5
WEB_POLL_INTERVAL_HOURS = 1

# ── Analysis / Scoring ────────────────────────────────────────────────────────

MIN_RELEVANCE_FOR_ALERT = 50  # Send to Slack for anything scoring 50+
LOG_ALL_TO_SHEETS = False
MIN_RELEVANCE_FOR_SHEETS = 50  # Only log confirmed leads to Sheets

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

BISHOP_AI_CONTEXT = """
Bishop AI has two revenue streams. Score leads for EITHER one:

── SERVICE: AI Automation & Education Agency ──
We help businesses:
- Automate repetitive workflows using AI tools (n8n, Zapier, Make, custom GPT pipelines)
- Build internal AI tools, AI agents, and chatbots for customer service, sales, and operations
- Train teams to use AI effectively (workshops, courses, 1:1 coaching)
- Develop AI strategy and implementation roadmaps

Ideal service clients: Small to mid-size businesses (5-200 employees), entrepreneurs, agency owners,
e-commerce brands, marketing agencies, professional services firms.
NOT a software dev agency — no SaaS builds, no mobile apps.

── PRODUCT: Prompt Anything (promptanything.io) ──
A $15.99/month AI prompt engineering tool that helps people write better prompts for ChatGPT, Claude, and Gemini.
It applies frameworks (CRISPE, CLEAR, SOPS, STAR) to transform vague ideas into optimized prompts.

Ideal Prompt Anything customers:
- Anyone frustrated that AI isn't giving them good results
- People who feel their ChatGPT/Claude outputs are generic, unhelpful, or off-target
- Professionals, solopreneurs, marketers, writers, students who use AI daily but struggle with prompting
- People asking "how do I get better results from ChatGPT" or "why does AI keep giving me bad answers"
- Anyone asking for prompt templates, prompt help, or "how to prompt" advice
- Price-sensitive individuals (not businesses) who just need to use AI better themselves

IMPORTANT: Score ai_prompting_help leads as valid contacts (50+) even if they're individuals, not businesses.
"""
