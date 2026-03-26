"""
Comment Generator — uses Claude to write contextual, non-generic comments.

Takes the post caption and username, returns a single thoughtful comment
that references the specific AI/automation topic in the post.
"""

import logging
import random
import anthropic
from config import CLAUDE_MODEL, ANTHROPIC_API_KEY, EMOJI_PROBABILITY

logger = logging.getLogger(__name__)

_client = None

# Relevant emojis to occasionally sprinkle in — never more than one per comment
_RELEVANT_EMOJIS = ["🔥", "👀", "💡", "🤔", "👏", "🙌", "✨", "💯", "🚀", "⚡"]


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in .env")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """You are writing a short, casual Instagram comment for a real person in the AI automation space.

Rules — follow ALL of them:
- Maximum 10 words total (count carefully)
- All lowercase — no capital letters anywhere, not even at the start
- Sound like a real person typing fast on their phone, not a brand
- Reference something specific from the post topic — no generic reactions
- End with a question when possible (keeps it conversational)
- NEVER use: "great post", "love this", "so true", "this is fire", "dropped", "banger", or any hype filler
- NEVER include hashtags
- NEVER pitch anything
- No period at the end — keep it casual

Examples of the exact style and length:
- "how are you handling the context limits here?"
- "this approach works until the api starts hallucinating lol"
- "what model are you running this on?"
- "the prompt structure matters more than people think"
- "did you test this on real client data?"
- "curious how long the workflow takes end to end"
- "this is the part most tutorials skip tbh"
"""


def generate_comment(username: str, caption: str) -> str:
    """
    Generate a short, lowercase, human-sounding comment (≤10 words).
    Occasionally appends a single relevant emoji based on EMOJI_PROBABILITY.
    """
    if not caption or len(caption.strip()) < 10:
        caption_context = "The post has no caption — it's likely a visual/image post about AI or automation."
    else:
        caption_context = f'Post caption: "{caption[:600]}"'

    user_message = (
        f"Write one Instagram comment for @{username}'s post.\n\n"
        f"{caption_context}\n\n"
        "Remember: max 10 words, all lowercase, no period. Write only the comment — nothing else."
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=60,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        comment = response.content[0].text.strip().lower()
        # Enforce word cap just in case
        words = comment.split()
        if len(words) > 10:
            comment = " ".join(words[:10])
        # Occasionally add a single emoji
        if random.random() < EMOJI_PROBABILITY:
            comment = comment.rstrip(".!?") + " " + random.choice(_RELEVANT_EMOJIS)
        logger.info(f"Generated comment for @{username}: {comment}")
        return comment
    except Exception as e:
        logger.error(f"Comment generation failed for @{username}: {e}")
        return _fallback_comment(caption)


def _fallback_comment(caption: str) -> str:
    """Lowercase fallback comments if Claude API fails."""
    caption_lower = caption.lower() if caption else ""
    options_by_topic = {
        "prompt": [
            "how are you structuring the prompt chain here?",
            "what model handles this best in your tests?",
        ],
        "automation": [
            "how do you handle errors mid-workflow?",
            "what's your fallback when the api goes down?",
        ],
        "agent": [
            "how are you preventing runaway loops?",
            "what's your memory strategy for this?",
        ],
    }
    for keyword, options in options_by_topic.items():
        if keyword in caption_lower:
            comment = random.choice(options)
            if random.random() < EMOJI_PROBABILITY:
                comment = comment.rstrip("?") + "? " + random.choice(_RELEVANT_EMOJIS)
            return comment
    fallbacks = [
        "what's been the hardest part to get right?",
        "how long did this take to build?",
        "curious what prompted this approach",
    ]
    comment = random.choice(fallbacks)
    if random.random() < EMOJI_PROBABILITY:
        comment += " " + random.choice(_RELEVANT_EMOJIS)
    return comment
