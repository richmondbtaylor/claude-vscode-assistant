"""
Claude reply generator — uses claude CLI (Max subscription) with Anthropic API fallback.
All replies: all lowercase, max 15 words, ~1 emoji per 10 replies.
"""

import os
import re
import random
import subprocess

# Tracks replies this session to control emoji frequency
_reply_counter = 0
_next_emoji_at = random.randint(8, 12)

SYSTEM_PROMPT = """You write short LinkedIn comment replies on behalf of Rich Taylor (Bishop AI).

Rules — follow every one:
- All lowercase, no capital letters anywhere
- Hard limit of 15 words — count carefully, never go over
- Conversational and slightly witty — never corporate or stiff
- Reply only to what the commenter said — never mention their job title or company
- Simple reactions ("great post", fire emoji, "100%"): give a warm quick acknowledgment
- Questions needing depth: brief answer within 15 words, end with "feel free to dm if you'd like to dive deeper!"
- No em dashes
- Output only the reply text — no quotes, no labels, no explanation"""

BUYING_SIGNALS = [
    "how do", "how can", "interested", "looking for", "need help",
    "we use", "we have", "our team", "struggling", "pain point",
    "automate", "automation", "workflow", "efficiency", "save time",
    "hours", "manual", "repetitive", "scale", "process", "grow",
    "can you", "could you", "do you offer", "tell me more",
    "love to chat", "dm me", "reach out", "contact",
]

SPAM_SIGNALS = [
    "click here", "follow me", "check out my", "buy now", "limited offer",
    "make money", "work from home", "subscribe", "link in bio",
]


def _enforce_15_words(text: str) -> str:
    words = text.strip().split()
    if len(words) > 15:
        text = " ".join(words[:15])
    return text.lower()


def _should_use_emoji() -> bool:
    global _reply_counter, _next_emoji_at
    _reply_counter += 1
    if _reply_counter >= _next_emoji_at:
        _next_emoji_at = _reply_counter + random.randint(8, 13)
        return True
    return False


def generate_reply(comment_text: str, post_context: str = "") -> str:
    """Generate a reply for the given comment. Returns a <=15 word lowercase string."""
    use_emoji = _should_use_emoji()

    prompt = (
        f"Post context (for reference, don't quote directly): {post_context[:200] if post_context else 'n/a'}\n\n"
        f"Comment: {comment_text}\n\n"
        f"Write the reply. Max 15 words. All lowercase."
        + (" One emoji is allowed." if use_emoji else " No emojis.")
    )

    # 1. Try claude CLI (Max subscription — no API key needed)
    reply = _call_claude_cli(SYSTEM_PROMPT + "\n\n" + prompt)

    # 2. Fallback: Anthropic API
    if not reply:
        reply = _call_anthropic_api(prompt)

    # 3. Last resort: canned fallbacks
    if not reply:
        reply = random.choice([
            "glad this resonated",
            "appreciate you sharing that",
            "this is the way",
            "100% — thanks for jumping in",
            "really appreciate this perspective",
        ])

    return _enforce_15_words(reply)


def score_comment(comment_text: str) -> str:
    """Hot / Warm / Cold based on buying signals in comment text."""
    text = comment_text.lower()

    if any(s in text for s in SPAM_SIGNALS):
        return "SPAM"

    signal_count = sum(1 for s in BUYING_SIGNALS if s in text)
    has_question = "?" in text

    if signal_count >= 2 or (signal_count >= 1 and has_question):
        return "HOT"
    elif signal_count == 1 or has_question:
        return "WARM"
    else:
        return "COLD"


def is_spam(comment_text: str) -> bool:
    text = comment_text.lower()
    return sum(1 for s in SPAM_SIGNALS if s in text) >= 2


# --- Backend implementations ---

def _call_claude_cli(full_prompt: str) -> str | None:
    try:
        result = subprocess.run(
            ["claude", "-p"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            out = result.stdout.strip().strip('"').strip("'")
            if out:
                return out
    except FileNotFoundError:
        pass  # claude CLI not installed
    except Exception as e:
        print(f"  Claude CLI error: {e}")
    return None


def _call_anthropic_api(prompt: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=80,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        out = response.content[0].text.strip().strip('"').strip("'")
        return out if out else None
    except Exception as e:
        print(f"  Anthropic API error: {e}")
    return None
