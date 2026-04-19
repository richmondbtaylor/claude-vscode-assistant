"""
Claude-powered signal analysis. Classifies each signal into one of 6 verticals
and scores it for relevance to Alpha Connectors' deal origination mission.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import anthropic

from config import ALPHA_CONNECTORS_CONTEXT, MAX_SIGNAL_AGE_DAYS, VERTICALS


@dataclass
class RawSignal:
    id: str
    platform: str
    url: str
    author: str
    title: str
    body: str = ""
    published_at: Optional[datetime] = None
    extra: dict = field(default_factory=dict)


@dataclass
class SignalAnalysis:
    vertical: str
    vertical_label: str
    signal_type: str
    relevance_score: int
    urgency: str
    is_decision_maker: bool
    signal_age_days: int
    deal_size_estimate: str
    connection_angle: str
    pain_points: list[str]
    suggested_intro: str
    should_contact: bool
    reasoning: str


_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _signal_age_days(published_at: Optional[datetime]) -> int:
    if published_at is None:
        return 0
    now = datetime.now(timezone.utc)
    pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    return max(0, (now - pub).days)


def analyze(signal: RawSignal) -> Optional[SignalAnalysis]:
    age_days = _signal_age_days(signal.published_at)
    if age_days > MAX_SIGNAL_AGE_DAYS:
        return None

    vertical_list = "\n".join(
        f"- {k}: {v['label']} (signals: {', '.join(v['signals'][:5])}...)"
        for k, v in VERTICALS.items()
    )

    prompt = f"""
{ALPHA_CONNECTORS_CONTEXT}

Verticals:
{vertical_list}

Analyze this signal and return JSON only — no prose:

Platform: {signal.platform}
Author: {signal.author}
URL: {signal.url}
Published: {signal.published_at.isoformat() if signal.published_at else "unknown"} ({age_days} days ago)
Title: {signal.title}
Body: {signal.body[:800]}

Return this JSON structure:
{{
  "vertical": "<one of: tech_projects | real_estate | renewables_data_centers | gov_contracts | startup_founders | capital_partners | not_relevant>",
  "signal_type": "<2-5 word label for the specific signal, e.g. 'Series B Announcement'>",
  "relevance_score": <0-100>,
  "urgency": "<high | medium | low>",
  "is_decision_maker": <true | false>,
  "deal_size_estimate": "<dollar amount or range if mentioned, else 'unknown'>",
  "connection_angle": "<1 sentence: specific reason to reach out NOW>",
  "pain_points": ["<specific need or gap>"],
  "suggested_intro": "<1-2 sentence outreach opener tailored to this signal>",
  "should_contact": <true | false>,
  "reasoning": "<2-3 sentences explaining the score>"
}}
""".strip()

    try:
        resp = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(raw)

        vertical = data.get("vertical", "not_relevant")
        return SignalAnalysis(
            vertical=vertical,
            vertical_label=VERTICALS.get(vertical, {}).get("label", "Not Relevant"),
            signal_type=data.get("signal_type", ""),
            relevance_score=int(data.get("relevance_score", 0)),
            urgency=data.get("urgency", "low"),
            is_decision_maker=bool(data.get("is_decision_maker", False)),
            signal_age_days=age_days,
            deal_size_estimate=data.get("deal_size_estimate", "unknown"),
            connection_angle=data.get("connection_angle", ""),
            pain_points=data.get("pain_points", []),
            suggested_intro=data.get("suggested_intro", ""),
            should_contact=bool(data.get("should_contact", False)),
            reasoning=data.get("reasoning", ""),
        )
    except Exception as e:
        print(f"[analyzer] Error analyzing signal {signal.id}: {e}")
        return None
