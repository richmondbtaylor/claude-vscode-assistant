"""
Claude lead intent analyzer — uses the `claude` CLI (Max subscription).
Takes a raw post and returns structured lead intelligence for Bishop AI.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from config import BISHOP_AI_CONTEXT

# Full path to claude CLI — npm installs to AppData on Windows.
# subprocess needs the .cmd wrapper on Windows, not the bash script.
import os as _os
import platform as _platform
if _platform.system() == "Windows":
    _CLAUDE_CMD = _os.path.expanduser("~/AppData/Roaming/npm/claude.cmd")
else:
    _CLAUDE_CMD = "claude"

SYSTEM_PROMPT = f"""You are a lead intelligence analyst for Bishop AI, an AI automation and education agency.

Your job is to evaluate social media posts (Reddit, LinkedIn, Quora, forums) and determine:
1. How relevant this post is as a potential lead for Bishop AI
2. What SPECIFIC type of help the author needs (be precise -- don't default to generic categories)
3. Whether the problem is CURRENTLY UNSOLVED (they still need help right now)
4. Whether Bishop AI should reach out

{BISHOP_AI_CONTEXT}

SCORING GUIDE for relevance_score (0-100):
- 90-100: Real person explicitly asking for AI automation help, mentions budget, or actively seeking an agency RIGHT NOW
- 70-89:  Real person struggling with a problem Bishop AI solves, or asking for a tool/service recommendation
- 50-69:  Real person tangentially related -- discussing AI automation but not clearly looking for help yet
- 30-49:  Real person with curious or educational interest, not a near-term buyer
- 0-15:   Marketing article, blog post, tutorial, directory page, aggregator, competitor post, news piece,
           promotional content, already-solved problem, or ANY content NOT written by a real person seeking help

When in doubt, score LOW. Only score 50+ if you are CONFIDENT this is a real human with an active need.

INTENT TYPES -- be specific, choose the most accurate one:
- "ai_automation_help":  Needs help BUILDING, SETTING UP, or MANAGING AI workflows, automations,
                         or integrations (n8n, Zapier, Make, custom GPT pipelines, API connections).
                         Use this when they want someone to do it FOR them or need technical help.
- "ai_education":        Wants TRAINING, workshops, courses, or coaching on HOW to use AI tools.
                         Use this when they want to LEARN themselves, not hire someone to build.
- "ai_prompting_help":   Needs help writing better PROMPTS, getting better results from ChatGPT/Claude/Gemini,
                         or understanding how to talk to AI tools effectively.
                         These are VALID leads for the Prompt Anything product ($15.99/mo).
                         Score 70+ if they're clearly frustrated with AI outputs or asking for prompt help.
                         Can be individuals -- doesn't need to be a business owner.
- "purchase_intent":     Showing CLEAR buying signals -- mentions budget, wants to hire an agency,
                         asking for quotes or proposals, comparing vendors.
- "pain_expressing":     Venting about a workflow or AI problem Bishop AI solves, but NOT yet
                         asking for help. They're frustrated but haven't asked for solutions.
- "competitor":          Post is FROM a competing AI automation agency, freelancer, or educator.
- "not_relevant":        Doesn't fit Bishop AI's services at all.

URGENCY LEVELS:
- "high":   Mentions deadline, has been struggling for a while, or is actively losing time/money
- "medium": No explicit urgency but the problem is currently active
- "low":    Exploratory, future-tense, or just curious

DISQUALIFYING CONTENT -- CRITICAL:
Set "already_solved" to true AND score 0-10 AND should_contact to false for ANY of the following:
- MARKETING ARTICLES or BLOG POSTS: content clearly written to attract readers, not a person seeking help
  (listicles like "Top 10 AI tools", "How to use AI for X", "Best practices for Y")
- PROMOTIONAL content from a company or product ("Introducing our new AI feature", brand announcements)
- TUTORIALS or HOW-TO guides written to teach others (the author is sharing knowledge, not asking for help)
- SUCCESS ANNOUNCEMENTS: "I figured it out", "here's what I did", "launched", "shipped", "solved it"
- PAST TENSE problems: "I had this issue", "I used to struggle with" -- problem is no longer active
- FOLLOW-UP questions about a system that already works fine
- AGGREGATOR or DIRECTORY pages: Product Hunt listings, job boards, freelancer marketplace pages (Fiverr, Upwork, Toptal listings), "hire a consultant" directory pages
- NEWS articles or industry commentary about AI trends (not someone with a personal need)
- ACADEMIC or RESEARCH content

REAL LEAD SIGNALS (what you ARE looking for):
- A REAL PERSON posting in first person about a current, unsolved problem
- Someone actively ASKING for help, a recommendation, or a vendor
- Clear "I need", "looking for", "can anyone help", "how do I" language from someone with the problem RIGHT NOW
- Hiring posts from a business owner or decision maker (not a job board aggregate page)

If you cannot confirm this is a real person with a current, active, unsolved need -- score it 0-15 and do NOT contact.

DECISION MAKER DETECTION:
Set "is_decision_maker" to true if the author appears to have real buying authority:
- Language like "my business", "my company", "I run", "I own", "we need" (as owner)
- Title or role signals: founder, co-founder, CEO, COO, owner, director, head of, manager, partner
- Asking on behalf of a business they clearly control
- Set to false if they're clearly just an employee with no purchasing authority
  ("my boss asked me to find...", "our IT team will decide", no ownership signals at all)
- Default to true if uncertain -- most people posting about business problems have some authority

AFFORDABILITY ASSESSMENT:
Set "budget_tier" based on all available signals:
- "can_afford":      Has a business/team, mentions hiring, references paid tools, revenue signals,
                     or describes problems at a scale that implies real budget
- "budget_limited":  Student, hobbyist, explicitly mentions tight budget, "free only", bootstrapped
                     with no revenue, or the problem is purely personal (not business)
- "uncertain":       No meaningful signals either way

Always respond with valid JSON only. No markdown, no explanation outside the JSON.
"""

ANALYSIS_SCHEMA = {
    "relevance_score": "integer 0-100",
    "intent_type": "one of: ai_automation_help | ai_education | ai_prompting_help | purchase_intent | pain_expressing | competitor | not_relevant",
    "urgency": "one of: high | medium | low",
    "already_solved": "boolean -- true if the author already solved their problem and is NOT currently seeking help",
    "is_decision_maker": "boolean -- true if the author appears to have buying authority (owner, founder, manager, etc.)",
    "budget_tier": "one of: can_afford | uncertain | budget_limited",
    "pain_points": "array of short strings describing the author's specific problems (empty array if already_solved)",
    "budget_signals": "array of specific phrases or signals that informed your budget_tier assessment (can be empty)",
    "intent_score": "integer 0-100 measuring BUYING intent only -- how likely this person is to hire or pay for help in the next 30 days. 90-100=actively seeking to hire/buy right now with budget signals, 70-89=strong buying signals but no explicit budget, 50-69=moderate intent (pain is real, solution-seeking), 30-49=mild interest, 0-29=no buying signals at all",
    "suggested_reply": "A direct, helpful reply Bishop AI could leave on the post. 2-3 sentences max. Acknowledge the SPECIFIC problem they described, then explain concisely how Bishop AI solves exactly that problem (e.g. 'We build n8n workflows that automate exactly this' or 'That's a prompting issue -- Prompt Anything walks you through fixing it'). End with the booking link on its own line: https://cal.com/bishopai.io/15min -- No generic phrases like 'we can help', 'great question', or 'I understand your frustration'. Be specific to THEIR situation. Empty string '' if already_solved is true.",
    "should_contact": "boolean -- true if this is worth a DM or outreach (must be false if already_solved is true)",
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
    pain_points: list[str]
    budget_signals: list[str]
    suggested_reply: str
    should_contact: bool
    reasoning: str


@dataclass
class RawPost:
    id: str
    platform: str          # "reddit" or "linkedin"
    url: str
    author: str
    title: str             # post title or first 100 chars
    body: str              # full text content
    subreddit: Optional[str] = None
    published_at: Optional[datetime] = None   # UTC datetime when post was published


def analyze(post: RawPost) -> Optional[PostAnalysis]:
    """
    Send a post to Claude CLI for lead intelligence analysis.
    Uses the claude CLI which runs on the user's Max subscription.
    Returns None if the call fails.
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
        f"Content:\n{post.body[:3000]}",  # cap at 3000 chars to manage tokens
        f"\nRespond with JSON matching this schema:\n{json.dumps(ANALYSIS_SCHEMA, indent=2)}",
    ])

    user_message = "\n".join(context_parts)

    # Combine system prompt + user message into a single prompt for the CLI
    full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{user_message}"

    try:
        result = subprocess.run(
            [
                _CLAUDE_CMD,
                "--print",           # Output response text only (no interactive UI)
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

        # Strip any accidental markdown code fences
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
