---
name: radley-research-agent
description: Manage, run, troubleshoot, or modify the Radley Lead Finder — a Node.js agent that monitors Reddit (keyword search + subreddit feeds) and Hacker News for founders, CFOs, and tax professionals actively expressing pain around R&D tax credit documentation, compliance, and audit risk. Claude scores each post against 3 ICPs and outputs a ranked CSV of up to 50 qualified leads. Use this skill when the user asks to run the Radley agent, add keywords, change subreddits, adjust scoring, view leads, fix errors, or modify how the agent finds or scores leads for radley.tax.
---

# Radley Lead Finder

A social listening agent that monitors Reddit keyword search, Reddit subreddit new-post feeds, and Hacker News (via the Algolia API) for US founders, CFOs, and tax professionals actively expressing pain around R&D tax credits. Claude Sonnet scores each post against 3 ICPs, assigns an intent score (1-10), infers role/company/pain signal, and suggests an outreach angle. Output is a ranked CSV of up to 50 qualified leads. Google dork URLs for LinkedIn, Twitter/X, and Facebook are printed at the end for manual follow-up.

---

## Project Location

```
C:\Users\richm\.claude\skills\Client Skills\radley-research-agent\
```

---

## How to Run

```bash
cd "/c/Users/richm/.claude/skills/Client Skills/radley-research-agent"

# First time only
npm install

# Run the agent
node radley-lead-finder.js
```

Output: `radley_leads.csv` in the same directory, sorted by intent score descending.

**Setup (first time):**
1. Ensure `ANTHROPIC_API_KEY` is set in environment (or add to a `.env` file and load it manually)
2. Run `npm install` to install `@anthropic-ai/sdk`
3. Run `node radley-lead-finder.js` to test

---

## Architecture

```
radley-lead-finder.js    Single-file Node.js agent — fetches, filters, scores, and exports
radley_leads.csv         Output file (created/overwritten on each run)
package.json             npm manifest — depends on @anthropic-ai/sdk
node_modules/            Installed dependencies
```

---

## Target ICPs

| ICP | Key Pain Signals |
|---|---|
| Founders / CTOs at US tech startups | R&D documentation burden, qualifying research expenses, startup R&D audit risk |
| CFOs / Finance teams | R&D payroll allocation, compliance cost, Section 41 credit complexity |
| Accountants / Tax advisors | Filing R&D credit claims for clients, documentation standards, audit exposure |

---

## Data Sources

| Source | Method |
|---|---|
| Reddit keyword search | Public RSS feed (`search.rss?q=...&sort=new&t=week`) — no API key needed |
| Reddit subreddits | New-post RSS feed per subreddit, filtered in-process for keyword relevance |
| Hacker News | Algolia search API (`hn.algolia.com/api/v1/search`) — no API key needed |
| LinkedIn / Twitter / Facebook | Not scraped — Google dork URLs printed at end of run for manual search |

---

## Keywords Monitored

```
R&D tax credit
research and development tax credit
qualifying research expenses
R&D documentation
R&D tax software
R&D payroll allocation
section 41 credit
R&D compliance startup
R&D tax claim
R&D audit risk
R&D tax accountant
engineering tax credits
```

---

## Subreddits Monitored

```
taxpros · smallbusiness · startups · Entrepreneur · accounting
tax · SaaS · techstartups · CFO · fintech · YCombinator
```

---

## Claude Scoring System

Each post is scored by `claude-sonnet-4-20250514` and returns a JSON object:

### Intent Score (1-10)
- **9-10** — Actively asking for an R&D tax tool / complaining about documentation burden
- **7-8** — Discussing R&D tax pain or asking for advisor recommendations
- **5-6** — In ICP, mentions R&D work, might be receptive
- **1-4** — Not relevant or not in ICP

### Buyer Persona
- `Founder/CTO`
- `CFO/Finance`
- `Accountant/Advisor`
- `Unknown`

### Lead Qualification Threshold
- `isLead: true` AND `intentScore >= 5` required to qualify
- Up to 50 qualified leads collected, then scoring stops

### Output Fields per Lead

| Field | Description |
|---|---|
| `isLead` | true/false |
| `intentScore` | 1–10 |
| `buyerPersona` | Founder/CTO, CFO/Finance, Accountant/Advisor, Unknown |
| `inferredRole` | Likely job title or null |
| `inferredCompany` | Company name if mentioned or null |
| `painSignal` | One sentence describing their exact pain point |
| `outreachAngle` | How Radley should approach this person |
| `contactHint` | Visible email, LinkedIn URL, or Twitter handle — or null |

---

## CSV Output — 14 Columns

| Column | Description |
|---|---|
| Rank | 1–50, sorted by intent score descending |
| Intent Score | 1–10 |
| Platform | Reddit or Hacker News |
| Buyer Persona | ICP category |
| Inferred Role | Likely job title |
| Company | Company name if visible |
| Author / Handle | Reddit username or HN handle |
| Profile URL | Reddit or HN profile link |
| Post URL | Link to original post |
| Date Posted | MM/DD/YYYY |
| Pain Signal | Their specific R&D tax pain |
| Outreach Angle | Recommended approach for Radley |
| Contact Hint | Any visible contact info |
| Post Title | Title of the post |

---

## Google Dork URLs (Manual)

After each run the script prints Google dork search URLs for LinkedIn, Twitter/X, Facebook, Reddit, and Quora — filtered to the past week (`&tbs=qdr:w`). Open in browser and add promising results to the lead sheet manually.

Example dorks generated:
```
site:linkedin.com/posts "R&D tax credit" startup
site:twitter.com "R&D tax software" OR "R&D compliance"
site:facebook.com/groups "R&D tax credit" help
"R&D tax credit" "software company" (help OR advice OR recommend) site:quora.com
```

---

## Key Configuration (inside radley-lead-finder.js)

| Constant | Default | What it controls |
|---|---|---|
| `DAYS_BACK` | 7 | How far back to pull posts |
| `TARGET_LEADS` | 50 | Stop scoring once this many qualified leads are found |
| `MIN_INTENT_SCORE` | 5 | Minimum intent score to qualify a lead |
| `SCORE_DELAY_MS` | 250 | Delay between Claude scoring calls (rate limit buffer) |
| `FETCH_DELAY_MS` | 1000 | Delay between source fetch calls |
| `KEYWORDS` | 12 entries | R&D tax credit pain signal keywords |
| `SUBREDDITS` | 11 entries | Subreddits to scan for relevant new posts |
| `MANUAL_DORKS` | 9 entries | Google dork queries printed for LinkedIn/Twitter/Facebook |

---

## Environment Variables

```
ANTHROPIC_API_KEY=your_key    # Required — used for Claude scoring
```

No other API keys required. Reddit and Hacker News are accessed via public endpoints.

---

## Common Tasks

### Run the agent
```bash
cd "/c/Users/richm/.claude/skills/Client Skills/radley-research-agent" && node radley-lead-finder.js
```

### Add a keyword
Edit the `KEYWORDS` array near the top of `radley-lead-finder.js`.

### Add a subreddit
Edit the `SUBREDDITS` array near the top of `radley-lead-finder.js`.

### Add a Google dork
Edit the `MANUAL_DORKS` array near the top of `radley-lead-finder.js`.

### Change the intent score threshold
Change `MIN_INTENT_SCORE` at the top of `radley-lead-finder.js` (default: 5).

### Change the lookback window
Change `DAYS_BACK` at the top of `radley-lead-finder.js` (default: 7 days).

### Change the lead target
Change `TARGET_LEADS` at the top of `radley-lead-finder.js` (default: 50).

### View leads
Open `radley_leads.csv` in Excel or Google Sheets. Sort by Intent Score column descending.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ANTHROPIC_API_KEY` not set | Export it in terminal before running: `export ANTHROPIC_API_KEY=your_key` |
| 0 posts found | Reddit may be rate-limiting the RSS feed — wait 2-3 minutes and retry |
| `Cannot find module '@anthropic-ai/sdk'` | Run `npm install` in the skill directory |
| JSON parse error from Claude | Handled automatically — failed scores return `isLead: false, intentScore: 0` |
| All posts filtered out | Reduce `MIN_INTENT_SCORE` to 4, or expand `KEYWORDS` / `SUBREDDITS` |
| HN returns 0 results | Check the Algolia API directly: `hn.algolia.com` — public, no key needed |
| `radley_leads.csv` is empty | No posts scored above threshold — check console for "Total unique posts" count |

---

## Radley Context (for scoring calibration)

Radley (radley.tax) is a US-focused SaaS platform that automates R&D tax credit claims. It connects to code repos, payroll systems, and project management tools to auto-generate IRS-audit-ready R&D documentation. Target customers are:

- **Founders/CTOs** at software, hardware, biotech, and medtech startups doing qualified research
- **CFOs and finance teams** managing R&D tax compliance, payroll allocation, and audit exposure
- **Accountants and tax advisors** who file R&D credit claims on behalf of startup clients

Pain signals that matter most: documentation burden, audit risk, qualifying expense calculation, payroll allocation complexity, manual R&D tracking, IRS Section 41 compliance.

---

## File Map

- `radley-lead-finder.js` — Single-file agent: fetch + filter + score + CSV export
- `radley_leads.csv` — Output (overwritten each run)
- `package.json` — npm manifest
- `node_modules/` — Dependencies (after `npm install`)
