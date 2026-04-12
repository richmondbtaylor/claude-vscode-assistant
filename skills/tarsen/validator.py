"""
TARSEN reply validator. Runs after the AI node and before posting.

A draft that fails ANY check is rejected. Do not retry in the same run.
"""
import re

from config import EM_DASH, MAX_REPLY_WORDS_DEEP


URL_RE = re.compile(r"https?://|www\.|\b\w+\.(com|io|ai|net|org|co)\b", re.IGNORECASE)
AI_DENIAL_RE = re.compile(r"\bI\s*(?:'?m|am)\s+(?:not\s+)?an?\s+AI\b", re.IGNORECASE)


def validate_reply(reply_text: str, banlists: dict) -> tuple[bool, str]:
    """
    Returns (passed, failed_check_name). If passed, failed_check_name is "".
    """
    if not reply_text or not reply_text.strip():
        return False, "empty_reply"

    word_count = len(reply_text.split())
    if word_count > MAX_REPLY_WORDS_DEEP:
        return False, f"word_count_{word_count}_over_{MAX_REPLY_WORDS_DEEP}"

    if len(reply_text) > 280:
        return False, f"char_count_{len(reply_text)}_over_280"

    if EM_DASH in reply_text:
        return False, "contains_em_dash"

    if "#" in reply_text:
        return False, "contains_hashtag"

    if URL_RE.search(reply_text):
        return False, "contains_url"

    if AI_DENIAL_RE.search(reply_text):
        return False, "ai_denial_phrase"

    lower = reply_text.lower()

    for phrase in banlists.get("phrases", []):
        if phrase and phrase in lower:
            return False, f"banned_phrase:{phrase}"

    for competitor in banlists.get("competitors", []):
        if competitor and competitor in lower:
            return False, f"competitor_mention:{competitor}"

    return True, ""


def tweet_is_political(tweet_text: str, banlists: dict) -> tuple[bool, str]:
    """Returns (is_political, matched_keyword)."""
    lower = (tweet_text or "").lower()
    for kw in banlists.get("political", []):
        if kw and kw in lower:
            return True, kw
    return False, ""
