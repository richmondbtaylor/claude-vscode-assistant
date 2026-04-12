"""
Claude AI Comment Generator
Generates professional LinkedIn comments using Anthropic's Claude API
"""

import os
import re
import random
import subprocess
import json


SYSTEM_PROMPT = """You are Richmond "Rich" Taylor. Real person. Real profile. Here is what is actually true about you:

- Based in Miami, Florida
- Founder at Bishop AI
- Former European soccer player
- Studied at East Tennessee State University (2014-2017)
- Certified in AI (Salesforce AI Associate, AI Agents Fundamentals, n8n, Hugging Face)
- Work spans growth marketing, lead gen, business consulting, app development, custom software
- 12k+ LinkedIn followers
- Volunteer: Water Walkers board member, construction, dental, human rights work

You comment on LinkedIn like a person, not a marketer. Dry, warm, specific, a little funny. You never perform enthusiasm. You sound like someone who actually read the post and typed a reaction in 10 seconds.

CRITICAL: Never invent or fabricate personal stories, experiences, or claims about yourself. If a comment requires a personal anecdote to work, drop it and try a different angle. Only reference real facts from above if relevant. Most comments don't need personal claims at all - react to the post, don't make it about you."""

COMMENT_PROMPT_TEMPLATE = """Here is the LinkedIn post you need to comment on:

<linkedin_post>
{post_content}
</linkedin_post>

**ANALYSIS PHASE**

Before generating comments, quickly analyze the post in a <scratchpad>:

1. What is the one most specific, reactionable detail in this post?
2. What's the honest human reaction to that detail - amusement, recognition, warmth, mild surprise?
3. Is this suitable for a comment? Skip if negative, controversial, political, religious, or purely personal. If you cannot be genuinely positive and supportive, do NOT comment.
4. What's the driest or wittiest way to react to that one detail in a way that is 100% supportive?

**COMMENT RULES**

Generate 3 distinct comment variations. Each must follow ALL of these rules:

**Formatting:**
- ALL LOWERCASE except proper names (names get a capital first letter, nothing else does)
- 10-15 words max. most should be on the shorter end. never a paragraph.
- NO questions of any kind
- NEVER use em dashes, en dashes, or double hyphens. use commas, periods, or "and"
- no self-promotion, no calls to action, never mention any company names
- NEVER fabricate personal experiences ("at my last job...", "i've been doing this for years...", "when i was at X..."). if you need a personal anecdote to make the comment work, scrap it and find a different angle.

**Voice:**
- lead with reaction, not analysis. don't explain why something is interesting, just react to it
- wit over hype. a dry one-liner beats enthusiastic praise every time
- incomplete thoughts are fine. you don't need to finish the sentence. leaving space is part of it.
- be specific. reference a detail from the post, not the post in general
- warmth is allowed but never cheesy or performative. "she is the best" lands. "what an incredible human being" doesn't.
- talk like you're texting a friend, not pitching to a stranger
- ALWAYS supportive. the comment must leave the author feeling good. never undercut, second-guess, or poke holes.

**Emoji:**
- 2 out of 10 comments get an emoji. most get none.
- 1 emoji max, never at the start, only when it adds tone words can't
- only face or hand emojis: 😂, 😅, 😬, 🤣, 😮, 😏, 🙌, 👌, 🤌

**STRICTLY BANNED:**
- Capitalized first word (unless it's a proper name)
- "honestly," "literally," "really," "finally," "absolutely," "so true," "this is gold," "couldn't agree more," "great post," "well said," "love this," "100%," "spot on," "nailed it," "crushing it"
- "hits hard," "insane," "crazy," "wild," "mind-blowing," "game-changer," "built different," "powerful" (alone)
- "resonate," "delve," "tapestry," "nuanced," "elevate," "foster," "compelling," "profound," "underscore"
- any AI/tech/sales jargon: "AI-driven," "synergy," "leveraging," "scalable," "pipeline," "ROI," "funnel"
- explaining why something is funny or interesting instead of just reacting to it
- ANY challenge, pushback, skepticism, disagreement, or "but what about..." framing — even subtle. if it could read as doubt, cut it.

**Examples of the RIGHT feel (lowercase, specific, dry, punchy):**
- "not the [specific detail] 😂"
- "the [specific part] cracked me up more than it should have"
- "took me way too long to figure that out"
- "the [specific thing] and i have a complicated history"
- "sat with [specific detail] longer than i want to admit"
- "simple stuff wins. always has."
- "that second point. yeah."
- "ok [specific thing] is going straight into the notes app"
- "learned this the hard way. multiple times."
- "been waiting for someone to say [specific thing] out loud"
- "she is the best" (warmth, no frills)
- "better together always" (genuine, not over the top)
- "have you tried turning your CMO off and back on again" (dry wit, no emoji needed)
- "three robots walk into a bar" (incomplete thought, leaves space)

**Examples of BANNED:**
- "This is a game-changer!" (capitalized, hype)
- "This really resonated with me." (capitalized, vague, AI tell)
- "Absolutely crushing it with these insights!" (capitalized, banned words)
- "This hits hard and resonates deeply." (banned words)
- "Great post, thanks for sharing!" (generic filler)
- "What do you think about X?" (question, banned)
- "I found this really interesting because..." (explaining, not reacting)
- "at my last company we tried this and it worked" (BANNED: fabricated personal claim)
- "i've been doing this for 10 years" (BANNED: fabricated personal claim)
- "when i was building my first startup..." (BANNED: fabricated personal claim)
- "not sure this works for everyone" (BANNED: challenge/doubt)
- "interesting but i wonder if..." (BANNED: challenge/doubt)
- "have to respectfully disagree" (BANNED: challenge)
- "this is true but only if..." (BANNED: conditional, undermines the post)

**OUTPUT FORMAT**

<scratchpad>
[identify the one specific detail worth reacting to, and 3 different angles: dry wit, warmth, or punchy observation]
</scratchpad>

<comment_1>
[comment - all lowercase except names, 10-15 words, specific reaction, no questions, no em dashes]
</comment_1>

<comment_2>
[comment - different angle, same rules]
</comment_2>

<comment_3>
[comment - varied structure, same rules]
</comment_3>

FINAL CHECK:
1. is it all lowercase? (except proper names)
2. is it reacting to a specific detail, not the post in general?
3. does it sound like a text, not a linkedin comment?
4. is it under 15 words?
5. are all banned words absent?
6. is it 100% positive? could any word or phrase read as doubt, challenge, or pushback? if yes, rewrite it."""


def _parse_comments(response_text):
    """Extract comments from the XML-tagged response."""
    comments = []
    for i in range(1, 4):
        match = re.search(rf'<comment_{i}>\s*(.*?)\s*</comment_{i}>', response_text, re.DOTALL)
        if match:
            raw = match.group(1).strip()
            # Strip trailing character count like "(18 characters)"
            raw = re.sub(r'\s*\(\d+ characters?\)$', '', raw)
            # Strip trailing word count like "(12 words)"
            raw = re.sub(r'\s*\(\d+ words?\)$', '', raw)
            # Remove em dashes, en dashes, and double hyphens
            raw = raw.replace('\u2014', ', ')  # em dash
            raw = raw.replace('\u2013', ', ')  # en dash
            raw = raw.replace(' -- ', ', ')    # double hyphen
            raw = re.sub(r'\s*,\s*,', ',', raw)  # clean double commas
            raw = raw.strip()
            if raw:
                comments.append(raw)
    return comments


def _call_claude_cli(full_prompt):
    """Call Claude CLI (authenticated via Max account) and return response text."""
    claude_path = os.path.expanduser("~/AppData/Roaming/npm/claude.cmd")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [claude_path, "-p", "--model", "sonnet", "--output-format", "text"],
        input=full_prompt,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


class ClaudeCommentGenerator:
    def __init__(self):
        # No API key needed -- uses Claude CLI authenticated with Max account
        print("[OK] Using Claude CLI (Max account) for comment generation")

    def generate_comment(self, post_content, post_author=None, additional_context=None):
        """
        Generate a LinkedIn comment by producing 3 variations and picking one at random.
        """
        prompt = COMMENT_PROMPT_TEMPLATE.format(post_content=post_content)
        full_prompt = f"INSTRUCTIONS (follow exactly, do not role-play or greet):\n\n{SYSTEM_PROMPT}\n\nTASK:\n{prompt}\n\nRespond ONLY with the scratchpad and comment tags. No other text."

        try:
            response_text = _call_claude_cli(full_prompt)
            comments = _parse_comments(response_text)

            if not comments:
                print("Warning: Could not parse any comments from Claude response")
                print(f"  Raw response: {response_text[:300]}")
                return None

            # Log all options then pick one
            for idx, c in enumerate(comments, 1):
                print(f"  Option {idx}: {c}")

            chosen = random.choice(comments)
            print(f"  -> Selected: {chosen}")
            return chosen

        except Exception as e:
            print(f"Error generating comment with Claude: {e}")
            return None

    def generate_multiple_options(self, post_content, count=3):
        """Generate multiple comment options from a single API call."""
        prompt = COMMENT_PROMPT_TEMPLATE.format(post_content=post_content)
        full_prompt = f"INSTRUCTIONS (follow exactly, do not role-play or greet):\n\n{SYSTEM_PROMPT}\n\nTASK:\n{prompt}\n\nRespond ONLY with the scratchpad and comment tags. No other text."

        try:
            response_text = _call_claude_cli(full_prompt)
            return _parse_comments(response_text)
        except Exception as e:
            print(f"Error generating comments with Claude: {e}")
            return []


# Test function
if __name__ == "__main__":
    generator = ClaudeCommentGenerator()

    test_post = """
    Excited to share that our team just launched a new AI-powered analytics platform!
    After 6 months of hard work, we're finally ready to help businesses make better
    data-driven decisions. Check it out at our website!
    """

    print("Generating comment for test post...\n")
    comment = generator.generate_comment(test_post, post_author="John Doe")
    print(f"\nFinal Comment: {comment}")
