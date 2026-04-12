"""
Claude lead intent analyzer for Conquer.io Social Prospecting Agent.
Takes a raw post and returns structured lead intelligence scored for Conquer.io ICP.
"""

import json
import os
import platform as _platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from config import CONQUER_CONTEXT

# Full path to claude CLI
if _platform.system() == "Windows":
    _CLAUDE_CMD = os.path.expanduser("~/AppData/Roaming/npm/claude.cmd")
else:
    _CLAUDE_CMD = "claude"

SYSTEM_PROMPT = f"""You are a lead intelligence analyst for Conquer.io, a sales engagement platform native to Salesforce.

Your job is to evaluate social media posts, forum discussions, and review site content and determine:
1. The combined intent score for this post as a Conquer.io sales lead
2. What specific pain category the author is expressing
3. Whether this person is a qualified prospect (50+ rep company, uses Salesforce)
4. Three tailored outreach messages the Conquer.io sales team could use

{CONQUER_CONTEXT}

INTENT SCORE (0–100) — Combined score of: intent strength + recency weight + company fit:
- 90–100: Active shopping signals (evaluating tools, asking for recommendations with timeline, explicit dissatisfaction with a named competitor, "we're switching")
- 70–89: Strong pain signals + buying language, competitor complaints, or explicit "looking for alternatives"
- 50–69: Clear pain point without explicit shopping intent; general venting about a tool Conquer.io replaces
- 30–49: General discussion, mild interest, or secondary relevance
- 0–29: No meaningful signal, blog/article, solved problem, or irrelevant content

SCORE TIERS:
- "High"   — score > 80: Flag for immediate human rep outreach
- "Medium" — score 50–80: Place in weekly review queue
- "Low"    — score < 50: Log only; no outreach

PAIN CATEGORIES — choose the most accurate:
- "competitor_dissatisfaction": Explicit complaint about Outreach, Salesloft, RingDNA, Dialpad, or Gong
- "pricing_pain": Mentions cost, price increase, or "too expensive" for a competitor
- "integration_pain": Salesforce sync issues, data mismatch, reps leaving CRM to use another tool
- "buying_intent": Actively evaluating, comparing vendors, asking for recommendations or demos
- "general_pain": Rep productivity, cadence issues, dialer problems — no competitor named
- "brand_mention": Mentions Conquer.io directly (praise or complaint) — flag separately
- "not_relevant": Does not fit Conquer.io's target market

SALESFORCE CONFIRMATION — set salesforce_confirmed to true ONLY if:
- The post explicitly mentions Salesforce, SFDC, SF CRM, or "Salesforce users"
- Set to false if there is no Salesforce mention (still flag the lead — CRM may be verifiable)

GDPR FLAG — set gdpr_flag to true if:
- Post is from a UK or EU-based poster (location signals in bio, company, or post language like "GDPR compliant", country mentions, .co.uk URLs, European cities/companies)

COMPANY SIZE SIGNALS — look for:
- Job titles at enterprise companies: VP of Sales, CRO, Head of Sales Ops, Revenue Operations, Director-level
- Explicit team size mentions: "our 60 reps", "200-person sales org", "team of 50"
- Company name signals (if a known enterprise company)

OUTREACH TONE RULES (critical):
- Public forum reply: Add value as a helpful peer. Do NOT mention Conquer.io unless the poster explicitly asked for tool recommendations. Frame around solving their problem.
- DM pivot: Warmer, more direct. Can mention Conquer.io naturally as a potential solution. End with a soft CTA (not a hard pitch).
- Direct internal: Written for a Conquer.io sales rep to send directly by Slack or email. Professional, concise, references the specific post/pain.
- Never bash competitors by name. Frame around Conquer.io's value, not competitor weaknesses.
- Never claim specific ROI percentages.
- Never make compliance or security claims.

DISQUALIFY (score 0–15, should_contact = false):
- Blog posts, listicles, tutorials, news articles
- Promotional content from vendors
- Success announcements ("we just launched X", "we solved it")
- Posts from Conquer.io employees or partners
- Freelancers, solo consultants without a sales team
- Companies clearly under 20 employees with no scaling signals

Always respond with valid JSON only. No markdown, no explanation outside the JSON.
"""

ANALYSIS_SCHEMA = {
    "intent_score": "integer 0-100 — combined score of intent strength, recency, and company fit",
    "score_tier": "one of: High | Medium | Low",
    "pain_category": "one of: competitor_dissatisfaction | pricing_pain | integration_pain | buying_intent | general_pain | brand_mention | not_relevant",
    "competitor_mentioned": "string — name of competitor mentioned, or empty string if none",
    "job_title": "string — job title extracted from post/profile, or 'unknown'",
    "company_name": "string — company name extracted from post/profile, or 'unknown'",
    "salesforce_confirmed": "boolean — true only if Salesforce is explicitly mentioned",
    "gdpr_flag": "boolean — true if poster appears to be EU/UK-based",
    "industry_signal": "string — industry if detectable (financial services, tech, healthcare, insurance, other), or 'unknown'",
    "company_size_signal": "string — any team size or company size signal from the post, or 'unknown'",
    "post_date": "string — the actual date of the post in YYYY-MM-DD format, extracted from the content (timestamps, 'posted X days ago', dates in the URL, '2024', etc). Return 'unknown' if truly undetectable.",
    "post_age_days": "integer — CRITICAL: days since the post_date as of today (2026-04-10). If post_date is unknown return -1. If the post is clearly from before March 2026, set > 30.",
    "outreach_public_forum": "string — 2-3 sentence reply for a public forum. Helpful, non-salesy. Mentions Conquer.io ONLY if poster asked for tool recommendations. Empty string if not_relevant.",
    "outreach_dm_pivot": "string — message to pivot to a DM or meeting. Can reference Conquer.io naturally. Soft CTA. Empty string if not_relevant.",
    "outreach_direct_internal": "string — message for a Conquer.io sales rep to send directly by Slack or email. Professional, references the pain. Empty string if not_relevant.",
    "should_contact": "boolean — true if score >= 50 and not a disqualified post",
    "escalation": "one of: immediate | weekly_triage | log_only | gdpr_manual_review",
    "crm_check": "string — 'needed — [company name]' if company is known, 'not needed' if not_relevant, 'unknown company' if company is not identifiable",
    "reasoning": "1-2 sentences explaining the score, qualification status, and key signal",
}


class PostAnalysis(BaseModel):
    intent_score: int = Field(ge=0, le=100)
    score_tier: str
    pain_category: str
    competitor_mentioned: str = ""
    job_title: str = "unknown"
    company_name: str = "unknown"
    salesforce_confirmed: bool = False
    gdpr_flag: bool = False
    industry_signal: str = "unknown"
    company_size_signal: str = "unknown"
    post_date: str = "unknown"
    post_age_days: int = -1
    outreach_public_forum: str = ""
    outreach_dm_pivot: str = ""
    outreach_direct_internal: str = ""
    should_contact: bool
    escalation: str
    crm_check: str = "unknown company"
    reasoning: str


@dataclass
class RawPost:
    id: str
    platform: str
    url: str
    author: str
    title: str
    body: str
    subreddit: Optional[str] = None
    published_at: Optional[datetime] = None


def analyze(post: RawPost) -> Optional[PostAnalysis]:
    """
    Send a post to Claude CLI for Conquer.io lead intelligence analysis.
    Returns None if the call fails.
    """
    context_parts = [
        f"Platform: {post.platform.upper()}",
        f"Author: {post.author}",
    ]
    if post.subreddit:
        context_parts.append(f"Community: r/{post.subreddit}")
    context_parts.extend([
        f"URL: {post.url}",
        f"Title: {post.title}",
        f"Content:\n{post.body[:3000]}",
        f"\nRespond with JSON matching this schema:\n{json.dumps(ANALYSIS_SCHEMA, indent=2)}",
    ])

    user_message = "\n".join(context_parts)
    full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{user_message}"

    try:
        result = subprocess.run(
            [
                _CLAUDE_CMD,
                "--print",
                "--model", "sonnet",
                "--max-turns", "1",
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()[:200] if result.stderr else "no stderr"
            print(f"[analyzer] CLI error for post {post.id}: exit {result.returncode} - {stderr}")
            return None

        text = result.stdout.strip()
        if not text:
            print(f"[analyzer] Empty response for post {post.id}")
            return None

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        return PostAnalysis(**data)

    except subprocess.TimeoutExpired:
        print(f"[analyzer] Timeout for post {post.id}")
        return None
    except json.JSONDecodeError as e:
        print(f"[analyzer] JSON parse error for post {post.id}: {e}")
        return None
    except Exception as e:
        print(f"[analyzer] Unexpected error for post {post.id}: {e}")
        return None
