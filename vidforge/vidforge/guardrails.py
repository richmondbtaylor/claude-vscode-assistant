"""The two hard lines.

vidforge deliberately ships **no general NSFW filter** - that is the point of
running open weights locally, and the diffusers backend tears out the safety
checker and the invisible watermarker on load.

Two things are still refused, because they are not "adult content", they are
abuse:

1. Sexual content involving minors.
2. A real, identifiable person's likeness without a consent record on file.

Only the positive prompt is scanned for age signals. Putting ``child`` in a
*negative* prompt is standard practice and must never be penalised.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# --- term tables -----------------------------------------------------------
# Unambiguous abuse-coded terms. Blocked on sight, no context needed.
_HARD_TERMS = (
    "csam",
    "child porn",
    "childporn",
    "child pornography",
    "lolicon",
    "loli",
    "shotacon",
    "shota",
    "jailbait",
    "pedophil",
    "paedophil",
)

# Terms that clearly denote a minor. Blocked only alongside sexual context.
_AGE_TERMS = (
    "child",
    "children",
    "kid",
    "kids",
    "toddler",
    "infant",
    "newborn",
    "baby",
    "babies",
    "minor",
    "underage",
    "under-age",
    "preteen",
    "pre-teen",
    "tween",
    "prepubescent",
    "pre-pubescent",
    "schoolgirl",
    "school girl",
    "schoolboy",
    "school boy",
    "elementary school",
    "middle school",
    "junior high",
    "kindergarten",
    "little girl",
    "little boy",
    "young girl",
    "young boy",
    "small girl",
    "small boy",
    "grade schooler",
)

# Ambiguous in adult work ("teen" is an industry descriptor for 18+ performers).
# These block only when sexual context is present AND nothing in the prompt
# establishes an adult age.
_SOFT_AGE_TERMS = (
    "teen",
    "teens",
    "teenage",
    "teenager",
    "adolescent",
    "youngster",
    "barely legal",
)

_SEXUAL_TERMS = (
    "nude",
    "nudity",
    "naked",
    "nsfw",
    "explicit",
    "sex",
    "sexual",
    "sexy",
    "erotic",
    "erotica",
    "porn",
    "hentai",
    "topless",
    "bottomless",
    "undress",
    "strip",
    "genital",
    "breast",
    "nipple",
    "cleavage",
    "lingerie",
    "aroused",
    "orgasm",
    "intercourse",
    "penetration",
    "masturbat",
    "fetish",
    "bdsm",
    "seductive",
    "provocative",
    "suggestive",
)

# Language that signals intent to reproduce a specific real person.
_IMPERSONATION_TERMS = (
    "deepfake",
    "deep fake",
    "face swap",
    "faceswap",
    "swap her face",
    "swap his face",
    "swap their face",
    "likeness of",
    "looks exactly like",
    "identical to",
    "celebrity",
    "famous actress",
    "famous actor",
    "real person",
    "my ex",
    "my coworker",
    "my co-worker",
    "my neighbor",
    "my neighbour",
    "someone i know",
    "from her instagram",
    "from his instagram",
)

_NUMERIC_AGE = re.compile(
    r"\b(?:age[d]?\s*)?(\d{1,2})\s*[-\s]?\s*(?:yo\b|y/?o\b|yrs?\b|years?[-\s]old)", re.I
)
_UNDER_18 = re.compile(r"\bunder\s*(?:the\s*age\s*of\s*)?(?:18|eighteen)\b", re.I)
_ADULT_AGE = re.compile(
    r"\b(?:1[89]|[2-9]\d)\s*[-\s]?\s*(?:yo\b|y/?o\b|yrs?\b|years?[-\s]old)|"
    r"\b18\+|\bover\s*18\b|\badult\b|\bgrown\s+(?:wo)?man\b|\bin\s+(?:her|his|their)\s+(?:20s|30s|40s|50s)\b",
    re.I,
)


# Stem + a short inflection, so "undress" catches "undressing" while "kid"
# still refuses to fire inside "kidney".
_SUFFIX = r"(?:[bdglmnprt])?(?:e|es|s|ed|ing|ion|ions|er|ers|ly|ia|ic)?"


def _hits(text: str, terms: tuple[str, ...]) -> list[str]:
    """Whole-word-ish stem match against already-lowercased text."""
    found = []
    for term in terms:
        pattern = r"(?<![a-z0-9])" + re.escape(term) + _SUFFIX + r"(?![a-z0-9])"
        if re.search(pattern, text):
            found.append(term)
    return found


def _numeric_minor(text: str) -> bool:
    if _UNDER_18.search(text):
        return True
    return any(int(m.group(1)) < 18 for m in _NUMERIC_AGE.finditer(text))


# --- verdict ---------------------------------------------------------------
@dataclass(slots=True)
class Verdict:
    allowed: bool
    code: str | None = None
    message: str = ""
    matched: list[str] = field(default_factory=list)

    def raise_for_status(self) -> None:
        if not self.allowed:
            raise GuardrailError(self)


class GuardrailError(Exception):
    def __init__(self, verdict: Verdict) -> None:
        super().__init__(verdict.message)
        self.verdict = verdict


ALLOWED = Verdict(allowed=True)


# --- consent register ------------------------------------------------------
@dataclass(slots=True)
class ConsentStore:
    """Signed-off records for generating a named real person's likeness.

    Deliberately dumb: a JSON file the operator maintains. It does not prove
    anything on its own - it makes the attestation explicit, dated and
    auditable instead of implicit.
    """

    path: Path

    def _read(self) -> dict:
        if not self.path.exists():
            return {"records": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"records": []}

    def list(self) -> list[dict]:
        return list(self._read().get("records", []))

    def get(self, consent_id: str) -> dict | None:
        return next((r for r in self.list() if r.get("id") == consent_id), None)

    def add(self, subject: str, attested_by: str, note: str = "") -> dict:
        subject = subject.strip()
        attested_by = attested_by.strip()
        if not subject or not attested_by:
            raise ValueError("consent records need both a subject and an attesting party")
        record = {
            "id": uuid.uuid4().hex[:12],
            "subject": subject,
            "attested_by": attested_by,
            "note": note.strip(),
            "attested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        data = self._read()
        data.setdefault("records", []).append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return record

    def remove(self, consent_id: str) -> bool:
        data = self._read()
        records = data.get("records", [])
        kept = [r for r in records if r.get("id") != consent_id]
        if len(kept) == len(records):
            return False
        data["records"] = kept
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True


# --- the check ------------------------------------------------------------
def check(
    prompt: str,
    *,
    identity_reference: bool = False,
    consent_id: str | None = None,
    consent_store: ConsentStore | None = None,
) -> Verdict:
    """Screen one generation request. ``prompt`` is the positive prompt only."""
    text = (prompt or "").lower()

    hard = _hits(text, _HARD_TERMS)
    if hard:
        return Verdict(
            False,
            "minor_sexual_content",
            "Refused: the prompt uses terms that only describe child sexual abuse material.",
            hard,
        )

    sexual = _hits(text, _SEXUAL_TERMS)
    if sexual:
        age = _hits(text, _AGE_TERMS)
        if _numeric_minor(text):
            age.append("stated age under 18")
        if not age and not _ADULT_AGE.search(text):
            age = _hits(text, _SOFT_AGE_TERMS)
        if age:
            return Verdict(
                False,
                "minor_sexual_content",
                "Refused: this reads as sexual content involving a minor. If the subject is "
                "an adult, state the age explicitly (e.g. '25 year old') and drop the "
                "youth descriptors.",
                sorted(set(age)),
            )

    impersonation = _hits(text, _IMPERSONATION_TERMS)
    if identity_reference or impersonation:
        record = consent_store.get(consent_id) if (consent_store and consent_id) else None
        if record is None:
            trigger = (
                "an identity/face reference image"
                if identity_reference
                else "language aimed at a specific real person"
            )
            return Verdict(
                False,
                "identity_consent_required",
                f"Refused: this request uses {trigger}. Register a consent record for the "
                "subject and resubmit with its consent_id.",
                sorted(set(impersonation)),
            )

    return ALLOWED
