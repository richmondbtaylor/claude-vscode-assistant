# Plan: Get 25 Real Leads for MyTaxHack

## Context
The user wants a real agent run (not demo data) producing 25+ qualifying leads (score ≥70) for mytaxhack.com. Current config was built generically — comparing the live site to config.py reveals gaps in verticals, services, and web search coverage. Fixing these maximizes the hit rate before running `--once`.

## What's Wrong With Current Config

### Missing verticals (on site, not in ICP)
- IoT / manufacturing / DevOps / MarTech — explicitly listed on mytaxhack.com
- Startup/seed-stage companies (409A valuations offered)

### Missing services in analyzer prompt
- 409A valuations → hot signal: startup with employees doing equity
- Sales tax compliance → nexus questions = ICP hit
- IRS audit representation → audit fear = high urgency
- Bookkeeping/automation setup → earlier-stage entry point

### Web search coverage gaps (currently only 9 queries)
- No IndieHackers queries (bootstrapped SaaS founders = core ICP)
- No Hacker News "Ask HN" queries (YC/tech founders)
- No additional LinkedIn/Twitter queries via Brave
- Missing manufacturing, DevOps, IoT community forums
- Only 2 Shopify queries, 1 Nomad List, 1 ConvertKit

## Implementation Steps

### Step 1 — Update `config.py`

**Add subreddits** (3 new):
- `manufacturing`, `devops`, `hardware`

**Add keywords** (4 new):
- `"409A valuation"`, `"sales tax nexus"`, `"IRS audit"`, `"need a bookkeeper"`

**Expand `WEB_SEARCH_QUERIES`** from 9 → 18 queries (add):
```python
# IndieHackers
'site:indiehackers.com taxes CPA "small business" OR "SaaS" OR "agency"',
'site:indiehackers.com "R&D tax credit" OR "S-corp" OR "tax strategy"',

# Hacker News
'site:news.ycombinator.com "need a CPA" OR "tax strategy" startup founder',
'site:news.ycombinator.com "R&D credit" OR "sales tax" SaaS startup',

# More Quora
'site:quora.com "sales tax nexus" ecommerce shopify amazon',
'site:quora.com "409A valuation" startup CPA accountant',
'site:quora.com "IRS audit" small business CPA representation',

# LinkedIn (via Brave)
'site:linkedin.com "looking for a CPA" OR "need a tax advisor" "small business" OR "startup"',
'site:linkedin.com "R&D tax credit" OR "S-corp election" founder CEO',
```

**Set `WEB_RESULTS_PER_QUERY = 8`** (up from 5) to increase raw candidate volume.

### Step 2 — Update `analyzer.py` TAX_HACK_CONTEXT

Add to TARGET CLIENTS industries:
```
- IoT / hardware manufacturers
- DevOps / platform engineering companies
- MarTech / AdTech companies
- Seed/Series A startups with employees
```

Add to HOT LEAD SIGNALS (80-100):
```
- Founder asking about 409A valuation or startup equity tax implications
- Business owner panicking about IRS audit notice or audit letter
- Ecommerce business asking about sales tax nexus, multi-state compliance
- Startup with employees concerned about payroll tax or QSB status
```

Add to WARM LEAD SIGNALS (70-79):
```
- Manufacturing or IoT company asking about R&D credits for product development
- DevOps/infrastructure company asking about software capitalization or R&D
```

### Step 3 — Run the Agent

```bash
cd c:/Users/richm/.claude/skills/mytaxhack-research-agent
venv/Scripts/python main.py --once
```

This runs both Reddit + Web cycles. Expected volume:
- Reddit: ~20 subreddits × 25 posts = ~500 posts processed, expect 30-50 qualifying
- Web: 18 queries × 8 results = ~144 posts processed, expect 15-25 qualifying

Results write automatically to the existing **"Leads"** tab in the Google Sheet.

## Critical Files
- `c:/Users/richm/.claude/skills/mytaxhack-research-agent/config.py` — subreddits, keywords, web queries
- `c:/Users/richm/.claude/skills/mytaxhack-research-agent/analyzer.py` — TAX_HACK_CONTEXT (ICP prompt)

## Verification
After `--once` completes, check the "Leads" tab in Google Sheet for:
- ≥25 rows with Relevance Score ≥ 70
- Platform diversity (Reddit + web sources)
- Relevant intent types: `tax_advisor_search`, `rd_credit_inquiry`, `tax_strategy_help`, `entity_structure`
