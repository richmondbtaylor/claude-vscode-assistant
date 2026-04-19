"""
Claude Sonnet 4.6 intent analyzer.
Takes a raw post and returns structured lead intelligence for Radley.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import anthropic
from pydantic import BaseModel, Field

from config import RADLEY_CONTEXT
from claude_auth import get_anthropic_client

client = get_anthropic_client()

SYSTEM_PROMPT = f"""You are a lead intelligence analyst for Radley (radley.tax), a SaaS platform that automates R&D tax credit claims for US companies.

Your job is to evaluate social media posts (Reddit, LinkedIn, Twitter, forums) and determine:
1. How relevant this post is as a potential lead for Radley
2. What SPECIFIC R&D tax credit pain the author has (be precise)
3. Whether the problem is CURRENTLY UNSOLVED (they still need help right now)
4. Whether Radley should reach out

{RADLEY_CONTEXT}

SCORING GUIDE for relevance_score (0-100):
- 90-100: Real person explicitly asking about R&D tax credit software, complaining about documentation burden, or actively seeking a tool/vendor RIGHT NOW
- 70-89:  Real person discussing R&D tax credit pain points, asking for CPA/advisor recommendations for R&D credits, or comparing R&D study options
- 50-69:  Real person tangentially related — founder/CFO discussing R&D work or tax planning but not specifically about R&D credits yet
- 30-49:  Real person with general tax or startup questions, not clearly about R&D credits
- 0-15:   Marketing article, blog post, tutorial, news piece, promotional content, competitor ad, already-solved problem, or NOT a real person seeking help

When in doubt, score LOW. Only score 50+ if you are CONFIDENT this is a real human with an active R&D tax credit need.

INTENT TYPES — be specific, choose the most accurate one:
- "rd_credit_help":      Needs help understanding, claiming, or maximizing their R&D tax credit.
                         Includes questions about qualifying, calculating QREs, or filing Form 6765.
- "documentation_pain":  Struggling with R&D documentation — manual tracking, time allocation,
                         substantiation for audits. This is Radley's primary pain point to solve.
- "tool_seeking":        Actively looking for R&D tax credit software, tools, or automated solutions.
                         Highest intent — they already know they need a product like Radley.
- "advisor_seeking":     Looking for a CPA, accountant, or consultant who specializes in R&D credits.
                         Radley can position as a complement to or replacement for manual R&D studies.
- "audit_anxiety":       Worried about IRS audits of their R&D credit claims, or has been audited.
                         Radley's audit-ready documentation directly addresses this fear.
- "cost_comparing":      Comparing costs of R&D study firms, evaluating ROI of claiming the credit,
                         or frustrated with how expensive manual R&D studies are.
- "general_tax":         General tax question that touches on R&D but isn't specifically about the credit.
- "competitor":          Post is FROM a competing R&D tax credit firm or software vendor.
- "not_relevant":        Doesn't relate to R&D tax credits at all.

URGENCY LEVELS:
- "high":   Tax deadline approaching, audit notice received, actively evaluating vendors, or has been losing money by not claiming
- "medium": No explicit urgency but the R&D credit pain is currently active
- "low":    Exploratory, future-tense, or just learning about R&D credits

DISQUALIFYING CONTENT — CRITICAL:
Set "already_solved" to true AND score 0-10 AND should_contact to false for ANY of the following:
- MARKETING ARTICLES or BLOG POSTS about R&D tax credits (content written to attract readers)
- PROMOTIONAL content from R&D tax firms or competitors ("our R&D study services", product announcements)
- TUTORIALS or HOW-TO guides about R&D credits (author is sharing knowledge, not seeking help)
- SUCCESS STORIES: "we saved $X with R&D credits", "here's how we claimed" — problem already solved
- PAST TENSE problems: "we used to struggle with R&D documentation" — no longer active
- NEWS articles about R&D tax credit legislation changes (informational, not personal need)
- DIRECTORY or AGGREGATOR pages listing R&D tax credit firms
- ACADEMIC or POLICY discussion about R&D incentives (not a person with a business need)

REAL LEAD SIGNALS (what you ARE looking for):
- A REAL PERSON posting in first person about a current, unsolved R&D tax credit problem
- Someone actively ASKING for help with R&D documentation, claiming the credit, or finding a tool/advisor
- Clear "I need", "looking for", "can anyone help", "how do I" language about R&D tax credits
- Founders/CTOs asking if their software/engineering work qualifies for R&D credits
- CFOs frustrated with manual R&D tracking processes
- Accountants looking for tools to scale their R&D credit practice

If you cannot confirm this is a real person with a current, active, unsolved R&D tax credit need — score it 0-15 and do NOT contact.

DECISION MAKER DETECTION:
Set "is_decision_maker" to true if the author appears to have buying authority:
- Founder, co-founder, CEO, CTO, CFO, COO, owner, partner, VP of Finance/Tax
- CPA or tax advisor who makes tool purchasing decisions for their practice
- "my company", "my startup", "our R&D", "we need" language indicating ownership
- Default to true if uncertain — most people posting about R&D credits have authority

AFFORDABILITY ASSESSMENT:
Set "budget_tier" based on all available signals:
- "can_afford":      Has a company doing R&D, mentions employees, revenue, or existing R&D study costs
- "budget_limited":  Very early startup with no revenue, explicitly mentions tight budget
- "uncertain":       No meaningful signals either way

Always respond with valid JSON only. No markdown, no explanation outside the JSON.
"""

ANALYSIS_SCHEMA = {
    "relevance_score": "integer 0-100",
    "intent_type": "one of: rd_credit_help | documentation_pain | tool_seeking | advisor_seeking | audit_anxiety | cost_comparing | general_tax | competitor | not_relevant",
    "urgency": "one of: high | medium | low",
    "already_solved": "boolean — true if the author already solved their problem and is NOT currently seeking help",
    "is_decision_maker": "boolean — true if the author appears to have buying authority",
    "budget_tier": "one of: can_afford | uncertain | budget_limited",
    "pain_points": "array of short strings describing the author's specific R&D tax credit problems (empty if already_solved)",
    "budget_signals": "array of specific phrases or signals that informed your budget_tier assessment (can be empty)",
    "intent_score": "integer 0-100 measuring BUYING intent only — how likely this person is to adopt an R&D tax credit tool in the next 30 days. 90-100=actively seeking software/tool right now, 70-89=strong pain signals and solution-seeking, 50-69=real pain but early stage, 30-49=mild interest, 0-29=no buying signals",
    "suggested_reply": "A direct, helpful reply Radley could post. 2-3 sentences max. Acknowledge the SPECIFIC R&D tax credit problem they described, then explain concisely how Radley solves exactly that (e.g. 'Radley connects to your GitHub repos and automatically identifies qualifying R&D activities — no more manual documentation'). End with the booking link on its own line: https://radley.tax/demo — No generic phrases like 'great question' or 'I understand'. Be specific to THEIR situation. Empty string '' if already_solved is true.",
    "should_contact": "boolean — true if this is worth outreach (must be false if already_solved is true)",
    "reasoning": "1-2 sentences explaining your score, decision maker status, and budget assessment",
}


class PostAnalysis(BaseModel):
    relevance_score: int = Field(ge=0, le=100)
    intent_score: int = Field(ge=0, le=100, default=0)
    intent_type: str
    urgency: str
    already_solved: bool = False
    is_decision_maker: bool = True
    budget_tier: str = "uncertain"
    pain_points: list[str] = []
    budget_signals: list[str] = []
    suggested_reply: str = ""
    should_contact: bool = False
    reasoning: str = ""


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
    Send a post to Claude Sonnet 4.6 for lead intelligence analysis.
    Returns None if the API call fails.
    """
    context_parts = [
        f"Platform: {post.platform.upper()}",
        f"Author: {post.author}",
    ]
    if post.subreddit:
        context_parts.append(f"Subreddit: r/{post.subreddit}")
    context_parts.extend([
        f"URL: {post.url}",
        f"Title: {post.title}",
        f"Content:\n{post.body[:3000]}",
        f"\nRespond with JSON matching this schema:\n{json.dumps(ANALYSIS_SCHEMA, indent=2)}",
    ])

    user_message = "\n".join(context_parts)

    import time as _time

    for attempt in range(4):
        try:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()

            text = next(
                (block.text for block in response.content if block.type == "text"),
                None,
            )
            if not text:
                print(f"[analyzer] No text block in response for post {post.id}")
                return None

            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            data = json.loads(text)
            return PostAnalysis(**data)

        except anthropic.RateLimitError:
            wait = 10 * (attempt + 1)
            print(f"[analyzer] Rate limited — waiting {wait}s (attempt {attempt + 1}/4)")
            _time.sleep(wait)
            continue
        except json.JSONDecodeError as e:
            print(f"[analyzer] JSON parse error for post {post.id}: {e}")
            return None
        except anthropic.APIError as e:
            print(f"[analyzer] Anthropic API error for post {post.id}: {e}")
            return None
        except Exception as e:
            print(f"[analyzer] Unexpected error for post {post.id}: {e}")
            return None

    print(f"[analyzer] Exhausted retries for post {post.id}")
    return None
