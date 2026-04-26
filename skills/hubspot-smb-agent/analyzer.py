"""
Claude lead intent analyzer for HubSpot SMB Lead Research Agent.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from config import HUBSPOT_SMB_CONTEXT

import os as _os
import platform as _platform
if _platform.system() == "Windows":
    _CLAUDE_CMD = _os.path.expanduser("~/AppData/Roaming/npm/claude.cmd")
else:
    _CLAUDE_CMD = "claude"

SYSTEM_PROMPT = f"""You are a B2B lead intelligence analyst. Your job: find SMBs (under $10M revenue)
that do NOT use HubSpot and are unhappy with their current CRM — these are prospects for HubSpot.

Evaluate each post and extract structured lead data. No fluff — just accurate fields.

{HUBSPOT_SMB_CONTEXT}

SCORING GUIDE for relevance_score (0-100):
- 85-100: Actively switching CRM or asking for a CRM recommendation, AND is clearly SMB-sized
          (e.g. "leaving Salesforce too expensive", "what CRM for 10-person sales team")
- 70-84:  Clear CRM pain or frustration with current tool, SMB context evident
- 50-69:  General CRM dissatisfaction or evaluation — company size unclear but plausible SMB
- 30-49:  Indirect signal — mentions CRM in passing, not clearly switching or in pain
- 20-29:  Tangential — talks about sales/pipeline but no CRM pain expressed
- 0-19:   Already uses HubSpot, enterprise, HubSpot consultant, or unrelated topic

ICP CATEGORY — pick the most accurate:
- "salesforce_refugee"   Leaving or frustrated with Salesforce (cost, complexity, overkill)
- "crm_switcher"         Actively looking to switch from any non-HubSpot CRM
- "crm_complainer"       Using a non-HubSpot CRM and expressing pain but not yet switching
- "crm_seeker"           No CRM yet or starting fresh, asking for recommendations
- "revops_evaluator"     RevOps/SalesOps formally evaluating CRM options
- "not_relevant"         Already uses HubSpot, enterprise (>$10M), agency, or unrelated

PAIN POINT TYPES:
- "crm_too_expensive"    Current CRM costs too much for their size (usually Salesforce)
- "crm_too_complex"      Current CRM too hard to use, team won't adopt it
- "crm_missing_features" Current CRM lacks features needed (automation, marketing, etc.)
- "crm_poor_adoption"    Sales team ignores or avoids current CRM
- "no_crm_yet"           No CRM in place, evaluating options for the first time
- "switching_crm"        Actively mid-migration or just decided to switch
- "crm_bad_support"      Current CRM vendor has poor support or bad reliability
- "not_relevant"         No CRM pain expressed

LEAD SCORE:
- "Hot"  — Actively switching NOW or explicitly asking for a CRM recommendation today
- "Warm" — Clear CRM pain or frustration, not yet actively switching
- "Cold" — Weak or indirect signal, wrong size, or wrong context

CURRENT CRM: name the CRM they currently use if mentioned (Salesforce, Zoho, Pipedrive, Monday,
Copper, Keap, ActiveCampaign, Freshsales, Insightly, Streak, Close.io). Empty string if unknown.

DISQUALIFYING CONTENT (score 0-15):
- Person already uses HubSpot (they are NOT a prospect)
- Enterprise company (500+ employees, clearly >$10M revenue, Fortune 500 context)
- HubSpot consultants, implementation partners, or agencies
- Marketing/blog/tutorial content (not a real person with a problem)
- Individual consumers (not a business)

Always respond with valid JSON only. No markdown.
"""

ANALYSIS_SCHEMA = {
    "relevance_score": "integer 0-100",
    "lead_score": "Hot | Warm | Cold",
    "icp_category": "salesforce_refugee | crm_switcher | crm_complainer | crm_seeker | revops_evaluator | not_relevant",
    "business_type": "specific description e.g. 'B2B SaaS startup ~15 employees', 'SMB services company'. Use 'unknown' if unclear.",
    "pain_point_type": "crm_too_expensive | crm_too_complex | crm_missing_features | crm_poor_adoption | no_crm_yet | switching_crm | crm_bad_support | not_relevant",
    "pain_point_description": "1-2 sentences describing the specific CRM pain or signal expressed",
    "why_it_fits": "1-2 sentences explaining why HubSpot solves this specific pain for this person",
    "urgency": "high | medium | low",
    "is_decision_maker": "boolean — true if author appears to be owner, founder, sales/ops manager",
    "competitor_mentioned": "current CRM name they use/mention, or empty string",
    "reasoning": "1-2 sentences explaining the score and why this is or isn't a HubSpot prospect",
}


class PostAnalysis(BaseModel):
    relevance_score: int = Field(ge=0, le=100)
    lead_score: str
    icp_category: str
    business_type: str = "unknown"
    pain_point_type: str
    pain_point_description: str
    why_it_fits: str
    urgency: str
    is_decision_maker: bool = True
    competitor_mentioned: str = ""
    reasoning: str

    @property
    def intent_type(self) -> str:
        return self.icp_category

    @property
    def should_contact(self) -> bool:
        return self.lead_score in ("Hot", "Warm")

    @property
    def intent_score(self) -> int:
        return self.relevance_score


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
    context_parts = [
        f"Platform: {post.platform.upper()}",
        f"Author: {post.author}",
    ]
    if post.subreddit:
        context_parts.append(f"Subreddit/Source: r/{post.subreddit}")
    context_parts.extend([
        f"URL: {post.url}",
        f"Title: {post.title}",
        f"Content:\n{post.body[:3000]}",
        f"\nRespond with JSON matching this schema:\n{json.dumps(ANALYSIS_SCHEMA, indent=2)}",
    ])

    full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n" + "\n".join(context_parts)

    _RETRY_DELAYS = [5, 15, 30]

    for attempt, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            print(f"[analyzer] Retrying post {post.id} in {delay}s (attempt {attempt + 1})...")
            time.sleep(delay)

        try:
            result = subprocess.run(
                [_CLAUDE_CMD, "--print", "--model", "sonnet", "--max-turns", "1"],
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=90,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()[:300] if result.stderr else "no stderr"
                print(f"[analyzer] CLI exit {result.returncode} for {post.id} | stderr: {stderr}")
                continue

            text = result.stdout.strip()
            if not text:
                continue

            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            data = json.loads(text)
            return PostAnalysis(**data)

        except subprocess.TimeoutExpired:
            print(f"[analyzer] Timeout for post {post.id}")
            continue
        except json.JSONDecodeError as e:
            print(f"[analyzer] JSON parse error for post {post.id}: {e}")
            return None
        except Exception as e:
            print(f"[analyzer] Unexpected error for post {post.id}: {e}")
            return None

    print(f"[analyzer] Gave up on post {post.id} after {len(_RETRY_DELAYS) + 1} attempts")
    return None
