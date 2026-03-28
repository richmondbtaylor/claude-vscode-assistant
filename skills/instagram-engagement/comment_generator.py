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
- 8–15 words total
- All lowercase — no capitals anywhere, not even at the start
- Sound like a smart person texting, not a brand account
- Reference something specific from the post — no generic reactions
- Half your comments should be statements, half should be questions — don't default to questions every time
- Be occasionally funny — dry wit, light banter, clever observations. Never cringe, never forced
- Show genuine insight — say something that reveals you actually understand the topic
- NEVER use: "great post", "love this", "so true", "fire", "dropped", "banger", "this is amazing", "keep it up", or any hype filler
- NEVER include hashtags, @ mentions, or periods at the end
- NEVER pitch anything or self-promote

Statement examples (say something real):
- "honestly the hardest part is keeping the prompt from drifting after iteration 3"
- "people underestimate how much token cost compounds at scale"
- "most devs skip the output validation step and then wonder why it breaks in prod"
- "the context window thing is less of a problem once you stop trying to stuff everything in"
- "that's a weird edge case that'll bite you eventually"

Question examples (genuine curiosity, not just 'how did you do this'):
- "does this hold up when the data is messy or only on clean inputs?"
- "what happens when the model decides to hallucinate a field name?"
- "curious if you benchmarked this against just using gpt-4o directly"
- "does the latency get painful at like 1000 requests a day?"

Banter/funny examples (subtle, never try-hard):
- "bold of you to trust the model not to go rogue here lol"
- "someone's definitely going to use this to automate their boss"
- "claude reading this comment right now: 👀"
- "this is the slide nobody puts in their ai pitch deck"

Write only the comment — no quotes, no labels, nothing else.
"""


def generate_comment(username: str, caption: str) -> str:
    """
    Generate a short, lowercase, human-sounding comment (8–15 words).
    Occasionally appends a single relevant emoji based on EMOJI_PROBABILITY.
    """
    if not caption or len(caption.strip()) < 10:
        caption_context = "The post has no caption — it's likely a visual/image post about AI or automation."
    else:
        caption_context = f'Post caption: "{caption[:600]}"'

    # Randomly nudge toward statement or question to enforce 50/50 balance
    style_nudge = random.choice([
        "Write a statement this time — not a question.",
        "Write a question this time — genuine curiosity, not generic.",
    ])

    user_message = (
        f"Write one Instagram comment for @{username}'s post.\n\n"
        f"{caption_context}\n\n"
        f"{style_nudge} 8–15 words, all lowercase, no period."
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=80,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        comment = response.content[0].text.strip().lower()
        # Strip any quotes the model might wrap around the comment
        comment = comment.strip('"\'')
        # Enforce word cap just in case
        words = comment.split()
        if len(words) > 15:
            comment = " ".join(words[:15])
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
