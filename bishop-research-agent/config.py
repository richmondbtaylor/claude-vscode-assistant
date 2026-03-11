"""
Central configuration for Bishop AI Research Agent.
Edit these lists to tune what the agent monitors and how sensitive it is.
"""

REDDIT_SUBREDDITS = [
    'artificial',
    'AIAutomation',
    'n8n',
    'zapier',
    'automation',
    'nocode',
    'lowcode',
    'ChatGPT',
    'PromptEngineering',
    'AutoGPT',
    'LangChain',
    'LocalLLaMA',
    'ClaudeAI',
    'OpenAI',
    'AIAssistants',
    'mcp',
    'ArtificialIntelligence',
    'MachineLearning',
    'GPT4',
    'perplexity_ai',
    'entrepreneur',
    'Entrepreneur',
    'smallbusiness',
    'startups',
    'SaaS',
    'agency',
    'consulting',
    'business',
    'EntrepreneurRideAlong',
    'microsaas',
    'Bootstrapped',
    'growmybusiness',
    'sweatystartup',
    'passive_income',
    'marketing',
    'DigitalMarketing',
    'PPC',
    'SEO',
    'sales',
    'socialmedia',
    'content_marketing',
    'copywriting',
    'customerservice',
    'CustomerSuccess',
    'Operations',
    'emailmarketing',
    'leadgeneration',
    'growthhacking',
    'ecommerce',
    'FulfillmentByAmazon',
    'Shopify',
    'realtors',
    'legaltech',
    'Accounting',
    'Bookkeeping',
    'humanresources',
    'projectmanagement',
    'recruiting',
    'forhire',
    'hiring',
    'WorkOnline',
    'freelance',
    'digitalnomad',
    'VirtualAssistants',
    'webdev',
    'freelancing',
    'productivity',
    'Notion',
    'MakeApp',
    'hubspot',
    'salesforce',
    'airtable',
]

REDDIT_KEYWORDS = [
    'AI automation',
    'automate with AI',
    'AI workflow',
    'need help automating',
    'looking for AI',
    'hire AI',
    'AI agency',
    'AI consultant',
    'AI freelancer',
    'automate my business',
    'AI implementation',
    'need someone to build',
    'looking to hire',
    'recommend an AI',
    'AI expert for hire',
    'AI developer for hire',
    'AI specialist needed',
    'looking for automation expert',
    'hire n8n developer',
    'hire automation specialist',
    'workflow automation',
    'business automation',
    'ChatGPT automation',
    'GPT workflow',
    'n8n help',
    'zapier alternative',
    'Make automation',
    'GoHighLevel AI',
    'HubSpot automation',
    'AI for CRM',
    'AI agent for my business',
    'build me an AI',
    'Claude API',
    'OpenAI API help',
    'build with Claude',
    'AI for my business',
    'AI tools recommendation',
    'automate repetitive',
    'save time with AI',
    'AI strategy',
    'AI chatbot for business',
    'AI for customer service',
    'AI for marketing',
    'AI for sales',
    'AI for operations',
    'drowning in manual',
    'too much manual work',
    'overwhelmed with tasks',
    'need to scale',
    'wasting hours',
    'manual process',
    'repetitive tasks',
    'learn AI automation',
    'AI training',
    'AI course',
    'AI workshop',
    'implement AI',
    'AI onboarding',
    'teach my team AI',
    'AI for my team',
    'where do I start with AI',
    'getting started with AI',
    'AI bootcamp',
    'AI coaching',
    'learn to use AI',
    'AI education',
    'understand AI for business',
    'prompt engineering',
    'better prompts',
    'ChatGPT not working',
    'AI giving bad results',
    'how to prompt',
    'prompt help',
    'ChatGPT useless',
    'AI outputs are bad',
    'get better results from AI',
    'prompt template',
    'AI not understanding me',
    'ChatGPT keeps getting it wrong',
    'Claude not giving',
    'Gemini not helpful',
    'AI prompt tips',
    'write better prompts',
    'prompt writing',
    'improve my prompts',
]

REDDIT_POST_LIMIT = 25
REDDIT_POLL_INTERVAL_MINUTES = 15

WEB_SEARCH_QUERIES = [
    'site:linkedin.com "looking for" AI automation consultant OR agency OR expert',
    'site:linkedin.com "need help with AI" automation OR workflow OR implementation',
    'site:linkedin.com "hiring" AI automation specialist OR consultant OR developer',
    'site:linkedin.com "I need someone" AI automation OR workflow OR chatbot',
    'site:linkedin.com "can anyone recommend" AI automation OR AI agency OR AI consultant',
    'site:linkedin.com "AI workflow" "need help" OR "struggling" OR "looking for"',
    'site:linkedin.com "automate my business" OR "AI for my team" help OR hire',
    'site:linkedin.com "AI education" OR "learn AI" team OR business OR workshop',
    'site:linkedin.com "AI implementation" "need help" OR "looking for" OR "hire"',
    'site:linkedin.com "AI consultant" OR "AI agency" hire OR need OR recommend',
    'site:linkedin.com "n8n" OR "Zapier" OR "Make" automation help OR consultant',
    'site:linkedin.com "AI training" OR "AI workshop" team OR staff OR business',
    'site:community.openai.com "looking for" AI automation consultant OR developer OR agency',
    'site:community.openai.com "need help" automate OR workflow OR business',
    'site:community.openai.com "hire" OR "recommend" AI developer OR consultant OR expert',
    'site:community.openai.com "I need" AI agent OR automation OR workflow built',
    'site:community.openai.com "my business" automate OR AI workflow OR chatbot',
    'site:community.n8n.io "need help" OR "looking for" workflow OR automation OR client',
    'site:community.n8n.io "hire" OR "freelancer" OR "consultant" build workflow',
    'site:community.n8n.io "my business" OR "our company" automation help',
    'site:community.make.com "need help" OR "looking for" automation OR AI',
    'site:community.make.com "hire" OR "consultant" OR "freelancer" build',
    'site:community.zapier.com "need help" OR "looking for" automation OR AI workflow',
    'site:community.zapier.com "hire" OR "consultant" build zap OR automation',
    'site:indiehackers.com "AI automation" OR "automate" need help OR looking for OR hire',
    'site:indiehackers.com "AI consultant" OR "AI agency" recommend OR need OR hire',
    'site:indiehackers.com "automate my" OR "AI workflow" struggling OR help',
    'site:indiehackers.com "learn AI" OR "AI training" OR "AI education" help',
    'site:news.ycombinator.com "Ask HN" AI automation OR workflow help OR hire',
    'site:news.ycombinator.com "who wants to be hired" AI automation OR workflow OR agent',
    'site:news.ycombinator.com "looking for" AI consultant OR automation expert OR AI agency',
    'site:dev.to "need help" AI automation OR workflow OR n8n OR zapier',
    'site:dev.to "looking for" AI consultant OR automation developer OR AI agency',
    'site:quora.com "best AI automation" agency OR consultant OR tool for business',
    'site:quora.com "how do I automate" business OR workflow using AI',
    'site:quora.com "AI consultant" hire OR find OR recommend',
    'site:quora.com "learn AI" business OR automation where start',
    'site:quora.com "better prompts" ChatGPT OR Claude OR AI help',
    'site:facebook.com/groups "AI automation" "need help" OR "looking for" OR "can anyone"',
    'site:facebook.com/groups "AI consultant" OR "AI agency" looking OR hire OR need',
    'site:facebook.com/groups "automate my business" OR "AI workflow" help',
    'site:facebook.com/groups "learn AI" OR "AI training" business OR team',
    'site:facebook.com/groups "n8n" OR "Zapier" OR "Make" help OR consultant',
    'site:upwork.com "AI automation" workflow OR n8n OR zapier OR agent',
    'site:upwork.com "AI consultant" OR "AI implementation" business',
    'site:upwork.com "chatbot" OR "AI agent" build OR develop business',
    'site:upwork.com "n8n" OR "Make" OR "Zapier" automation expert',
    'site:upwork.com "AI training" OR "AI workshop" team OR staff',
    'site:community.gohighlevel.com "AI" OR "automation" need help OR looking for OR hire',
    '"GoHighLevel" "AI automation" "need help" OR "looking for" OR "hire" -site:reddit.com',
    '"HubSpot" "AI automation" "need help" OR consultant OR hire -site:reddit.com',
    'site:producthunt.com "AI automation" OR "AI workflow" help OR need OR hire',
    'site:producthunt.com "looking for" AI consultant OR automation tool OR agency',
    '"AI training for my team" OR "AI workshop" OR "AI onboarding" business help',
    '"teach my team AI" OR "AI education" company OR staff OR employees',
    '"AI strategy" "need help" OR "consultant" OR "where to start" business',
    '"implement AI" "our business" OR "my company" OR "our team" help',
    '"AI adoption" company OR business help OR consultant OR struggling',
    '"how do I get better results" ChatGPT OR Claude OR Gemini -site:reddit.com',
    '"ChatGPT keeps" giving bad OR wrong OR useless OR generic results -site:reddit.com',
    '"my prompts" "not working" OR "not good" OR "AI ignores" -site:reddit.com',
    '"how to write better prompts" help OR frustrated -site:reddit.com',
    '"AI outputs" "not good" OR "generic" OR "off" help improve -site:reddit.com',
    'site:community.openai.com "my prompts" OR "better prompts" help OR struggling OR frustrated',
    'site:community.openai.com "getting bad results" OR "not understanding" OR "ignoring my instructions"',
    '"prompt engineering" "where to start" OR "need help" OR "how do I" -site:reddit.com',
    '"AI not giving me" what I want OR need help prompting -site:reddit.com',
    '"write better prompts" for ChatGPT OR Claude OR AI -site:reddit.com',
    '"need help with AI automation" -site:reddit.com',
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
    '"n8n" OR "zapier" "can anyone help" OR "looking for" automation -site:reddit.com',
]

WEB_RESULTS_PER_QUERY = 5
WEB_POLL_INTERVAL_HOURS = 1

LINKEDIN_KEYWORDS = [
    'AI automation consultant',
    'AI workflow help',
    'need help automating',
    'looking for AI agency',
    'AI implementation help',
    'automate my business AI',
    'AI chatbot for business',
    'hire AI consultant',
    'build AI workflow',
    'AI for my team',
    'AI training for staff',
    'AI workshop for business',
    'learn AI automation',
    'prompt engineering help',
    'ChatGPT not working for me',
    'AI giving bad results',
    'n8n consultant',
    'zapier expert hire',
]

LINKEDIN_RESULTS_PER_KEYWORD = 5

MIN_RELEVANCE_FOR_ALERT = 50
LOG_ALL_TO_SHEETS = False
MIN_RELEVANCE_FOR_SHEETS = 50

SHEET_WORKSHEET_NAME = 'Leads'

SHEET_COLUMNS = [
    'Timestamp',
    'Platform',
    'Subreddit',
    'URL',
    'Author',
    'Title / Snippet',
    'Relevance Score',
    'Intent Score',
    'Cross Platform',
    'Intent Type',
    'Urgency',
    'Decision Maker',
    'Budget Tier',
    'Already Solved',
    'Pain Points',
    'Budget Signals',
    'Suggested Reply',
    'Should Contact',
    'Claude Reasoning',
    'Status',
]

BISHOP_AI_CONTEXT = """
Bishop AI is a US-based AI Education and Automation Agency. Score leads for EITHER revenue stream:

SERVICE: AI Automation and Education Agency
We help US businesses:
- Automate repetitive workflows using AI tools (n8n, Zapier, Make, Claude Code, custom GPT pipelines)
- Build internal AI tools, AI agents, and chatbots for customer service, sales, and operations
- Train teams to use AI effectively (workshops, courses, 1:1 coaching)
- Develop AI strategy and implementation roadmaps

HOT LEAD signals (score 75+):
- Actively posting that they need help or are hiring for AI automation or education
- Posting a job or request for an AI consultant, agency, or automation expert
- Describing a specific business pain they want AI to solve RIGHT NOW
- Asking who can help or where to find an AI agency or consultant
- Small/mid-size US business owner or decision maker expressing urgency

WARM LEAD signals (score 50-74):
- Asking for AI tool recommendations for their business
- Frustrated with current manual processes and exploring AI
- Wanting to learn AI for themselves or their team
- Asking how to implement AI in a specific business context

Ideal service clients: Small to mid-size US businesses (5-200 employees), entrepreneurs,
agency owners, e-commerce brands, marketing agencies, professional services firms.
NOT a software dev agency -- no SaaS builds, no mobile apps.

PRODUCT: Prompt Anything (promptanything.io)
A 5.99/month AI prompt engineering tool for better ChatGPT, Claude, and Gemini prompts.

HOT Prompt Anything leads (score 70+):
- Directly expressing frustration that AI outputs are bad, generic, or not what they wanted
- Asking how to get better results from ChatGPT/Claude/AI
- Asking for prompt templates or prompt help
- Saying their prompts do not work or AI keeps misunderstanding them

SCORING RULES:
- Score ONLY leads where the person is ACTIVELY SEEKING help -- not just discussing AI generally
- Score 75+ if they are posting a job, asking for a hire, or expressing urgent need
- Score 50-74 if they are frustrated, exploring options, or asking for recommendations
- Score under 40 for: competitors, general AI news/articles, already-solved problems, job seekers
- USA-based leads are preferred -- boost score slightly if US location is evident
- Score ai_prompting_help leads 50+ even if they are individuals, not businesses
"""
