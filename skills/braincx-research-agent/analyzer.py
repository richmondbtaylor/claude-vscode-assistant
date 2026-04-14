"""
Claude lead intent analyzer for BrainCX Social Listening Agent.
Data-focused output — no outreach suggestions. Just clean lead intelligence.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from config import BRAINCX_CONTEXT

import os as _os
import platform as _platform
if _platform.system() == "Windows":
    _CLAUDE_CMD = _os.path.expanduser("~/AppData/Roaming/npm/claude.cmd")
else:
    _CLAUDE_CMD = "claude"

SYSTEM_PROMPT = f"""You are a B2B lead intelligence analyst for BrainCX, a multilingual voice AI company
that builds AI receptionists and IVR replacements for US service businesses.

Your job: evaluate a post or listing and extract structured lead data. No fluff — just accurate fields.

{BRAINCX_CONTEXT}

SCORING GUIDE for relevance_score (0-100):
- 85-100: Job listing for receptionist/front desk (company is ACTIVELY spending to solve the problem BrainCX solves), OR a decision-maker explicitly asking for a voice AI / answering service solution right now
- 70-84:  Real person expressing current, unsolved pain about call volume, staffing, multilingual needs, or after-hours coverage
- 50-69:  Customer review/complaint about a business being hard to reach by phone — active pain signal about that business
- 30-49:  Person in a relevant service industry discussing related challenges without explicitly seeking help
- 20-29:  Tangential signal — in the right ICP but pain is indirect or unclear
- 0-19:   Not relevant — individual consumer problem, unrelated industry, already-solved issue, marketing content

BUSINESS TYPE — be specific. Examples: "immigration law firm", "dental practice", "HVAC company",
"medical group", "chiropractic office", "veterinary clinic", "home services contractor",
"university admissions office", "financial advisory firm", "auto dealership", "title company".
Use "unknown" if not determinable.

ICP CATEGORY — pick the most accurate:
- "healthcare"            Medical, dental, chiropractic, physical therapy, veterinary, optometry
- "immigration_law"       Immigration attorneys and law firms
- "general_legal"         Other law firms and legal services
- "home_services"         HVAC, plumbing, electrical, contractors, home repair
- "higher_education"      Universities, community colleges, enrollment offices
- "professional_services" Financial, insurance, real estate, auto dealerships, title companies
- "hospitality"           Hotels, restaurants, event venues
- "not_relevant"          Doesn't fit

PAIN POINT TYPES:
- "call_volume_overflow"    Can't keep up with inbound calls
- "after_hours_coverage"    Missing calls outside business hours
- "multilingual_barrier"    Can't serve non-English-speaking clients
- "receptionist_staffing"   Hiring/retaining front desk staff is a problem
- "outdated_ivr"            Complaints about old phone trees
- "scheduling_bottleneck"   Appointment scheduling is breaking down
- "intake_inefficiency"     Client/patient intake is slow or leaking leads
- "lead_leakage"            Losing clients because calls go unanswered
- "job_posting"             Business is hiring for the exact role BrainCX replaces
- "customer_complaint"      Review/complaint about a business's phone accessibility
- "solution_seeking"        Actively asking for a tool/service recommendation
- "not_relevant"            No relevant pain

LEAD SCORE:
- "Hot"  — Job posting for receptionist/front desk, OR explicitly seeking a voice AI/answering service solution, OR decision-maker with active urgent need
- "Warm" — Clear pain in target ICP, not yet actively seeking a solution
- "Cold" — Tangential signal, weak ICP fit, or low urgency

IS_JOB_POSTING: true if this is a job listing for receptionist, front desk, intake coordinator, or similar role.

COMPETITOR: name any competitor mentioned (Ruby Receptionists, Smith.ai, Air AI, Bland AI, Vapi,
Retell AI, RingCentral, Twilio, Vonage, Grasshopper, Zocdoc, NexHealth, Calendly). Empty string if none.

DISQUALIFYING CONTENT (score 0-15):
- Individual consumer asking about their own personal problem
- Marketing/blog/tutorial content
- Already-solved problems
- Unrelated industries

Always respond with valid JSON only. No markdown.
"""

ANALYSIS_SCHEMA = {
    "relevance_score": "integer 0-100",
    "lead_score": "Hot | Warm | Cold",
    "icp_category": "healthcare | immigration_law | general_legal | home_services | higher_education | professional_services | hospitality | not_relevant",
    "business_type": "specific business type string, e.g. 'dental practice', 'HVAC company', 'immigration law firm'. Use 'unknown' if unclear.",
    "pain_point_type": "call_volume_overflow | after_hours_coverage | multilingual_barrier | receptionist_staffing | outdated_ivr | scheduling_bottleneck | intake_inefficiency | lead_leakage | job_posting | customer_complaint | solution_seeking | not_relevant",
    "pain_point_description": "1-2 sentences describing the specific pain or signal expressed",
    "why_it_fits": "1-2 sentences explaining how BrainCX voice AI solves this specific situation",
    "urgency": "high | medium | low",
    "is_decision_maker": "boolean — true if author appears to have buying authority (owner, manager, operator)",
    "is_job_posting": "boolean — true if this is a job listing for receptionist/front desk/intake role",
    "competitor_mentioned": "competitor name or empty string",
    "reasoning": "1-2 sentences explaining the score and ICP fit",
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
    is_job_posting: bool = False
    competitor_mentioned: str = ""
    reasoning: str

    # Shims so notifier.py works without changes
    @property
    def intent_type(self) -> str:
        return self.icp_category

    @property
    def pain_points(self) -> list[str]:
        return [self.pain_point_description] if self.pain_point_description else []

    @property
    def budget_signals(self) -> list[str]:
        return [f"competitor: {self.competitor_mentioned}"] if self.competitor_mentioned else []

    @property
    def suggested_reply(self) -> str:
        return ""

    @property
    def should_contact(self) -> bool:
        return self.lead_score in ("Hot", "Warm")

    @property
    def intent_score(self) -> int:
        return self.relevance_score

    @property
    def already_solved(self) -> bool:
        return False

    @property
    def budget_tier(self) -> str:
        return "uncertain"


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

    _RETRY_DELAYS = [5, 15, 30]  # seconds to wait before each retry

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
                stdout = result.stdout.strip()[:100] if result.stdout else "no stdout"
                print(f"[analyzer] CLI exit {result.returncode} for {post.id} | stderr: {stderr} | stdout: {stdout}")
                continue  # retry

            text = result.stdout.strip()
            if not text:
                continue  # retry

            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            data = json.loads(text)
            return PostAnalysis(**data)

        except subprocess.TimeoutExpired:
            print(f"[analyzer] Timeout for post {post.id}")
            continue  # retry
        except json.JSONDecodeError as e:
            print(f"[analyzer] JSON parse error for post {post.id}: {e}")
            return None  # bad output, no point retrying
        except Exception as e:
            print(f"[analyzer] Unexpected error for post {post.id}: {e}")
            return None

    print(f"[analyzer] Gave up on post {post.id} after {len(_RETRY_DELAYS) + 1} attempts")
    return None
