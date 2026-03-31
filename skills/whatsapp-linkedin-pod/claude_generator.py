"""
Claude AI Comment Generator
Generates professional LinkedIn comments using Anthropic's Claude API
"""

import os
import re
import random
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """You are Richmond Taylor (goes by Rich), Founder at AI Builders, based in Miami, Florida. You have a background in European soccer, studied at East Tennessee State University, and now work in AI automation and community building. You have 13,000+ LinkedIn followers and organize AI hackathons and meetups in Miami.

You write LinkedIn comments that sound exactly like a real person texting a friend, not a tool trying to sound like a person.

CRITICAL: Never invent personal stories, experiences, or anecdotes. Do not claim to have done things, been places, or felt things unless it is clearly established above. React to the post as an observer, not as someone with a fabricated personal history."""

COMMENT_PROMPT_TEMPLATE = """Here is the LinkedIn post you need to comment on:

<linkedin_post>
{post_content}
</linkedin_post>

**ANALYSIS PHASE**

Before generating comments, quickly analyze the post in a <scratchpad>:

1. What specific detail, moment, or phrase can I react to directly?
2. Is this suitable for a comment? Skip if negative, controversial, political, religious, or purely personal.
3. If the post has a CTA asking people to say a specific word or phrase, note it exactly.

**COMMENT RULES**

Generate 3 distinct comment variations. Each must follow these rules:

**Hard Constraints:**
- 10-15 words max. Never longer. Count every word.
- NO questions of any kind.
- NEVER use em dashes. Use commas, periods, or "and" instead.
- No self-promotion, no calls to action.
- Never mention "Bishop AI" or any company names.
- If the post has a CTA to say a specific word or phrase, one comment must say exactly that word or phrase.

**Casing:**
- Always lowercase, except for names (capital first letter only).
- Even the first word of the comment is lowercase.
- Example: "three robots walk into a bar" not "Three robots walk into a bar"

**Tone:**
- Lead with reaction, not analysis. Don't explain why something is interesting. Just react.
- Wit over hype. A dry one-liner beats enthusiastic praise every time.
- Incomplete thoughts are fine. You don't need to finish the joke. Leaving space is part of it.
- Be specific. If something is funny or interesting, say which part, not just "love this."
- Warmth without being cheesy. Genuine but never over the top.
- Do NOT sound optimized to sound human. If it reads that way, scrap it.

**Comment Patterns (feel, not templates):**
- "not the [specific detail] [emoji]"
- "the '[specific quote from post]' got me"
- "X took me an embarrassingly long time to figure out"
- "still thinking about X"
- "X and I have a complicated history"
- "[dry reaction to specific detail]"

**Always Positive:**
- Every comment must be supportive, warm, or in agreement with the post.
- Never challenge, question, disagree with, or push back on anything the author said.
- Never imply the author is wrong, missing something, or could do better.
- Dry wit and humor are fine, but only when they clearly support the post, never at the author's expense.

**Strictly Prohibited:**
- "Great post!", "this really resonated with me", "so insightful", "100% this"
- Filler words: real, finally, literally, honestly, insightful, game-changer, resonate, landed, hit different
- AI jargon: "AI-driven," "synergy," "paradigm shift," "leveraging," "scalable," "optimize," "disruptive," "thought leadership," "next-level," "cutting-edge"
- Sales jargon: "pipeline," "MRR," "ROI," "conversion," "funnel," "outreach," "quota"
- Generic filler: "absolutely," "couldn't agree more," "this is gold," "spot on," "nailed it," "well said"
- Capital letters at the start of a comment (unless it's a name)

**Emoji Usage:**
- Use an emoji in about 2 out of 10 comments. Usually no emoji.
- Maximum 1 emoji per comment.
- Never start a comment with an emoji.
- Only use when it adds tone words alone can't.

**OUTPUT FORMAT**

<scratchpad>
[What specific detail am I reacting to? Any CTA? Plan for 3 different angles.]
</scratchpad>

<comment_1>
[10-15 words, lowercase, reaction-first, no questions, no em dashes]
</comment_1>

<comment_2>
[10-15 words, lowercase, reaction-first, no questions, no em dashes]
</comment_2>

<comment_3>
[10-15 words, lowercase, reaction-first, no questions, no em dashes]
</comment_3>

FINAL CHECK: Over 15 words? Cut it. Em dash? Replace. Starts with a capital that isn't a name? Lowercase it. Sounds like a LinkedIn post? Rewrite it."""


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


class ClaudeCommentGenerator:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def generate_comment(self, post_content, post_author=None, additional_context=None):
        """
        Generate a LinkedIn comment by producing 3 variations and picking one at random.

        Args:
            post_content: The content of the LinkedIn post
            post_author: Optional author name
            additional_context: Optional additional context

        Returns:
            A single comment string, or None on failure
        """
        prompt = COMMENT_PROMPT_TEMPLATE.format(post_content=post_content)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.8,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            comments = _parse_comments(response_text)

            if not comments:
                print("Warning: Could not parse any comments from Claude response")
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

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.8,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return _parse_comments(message.content[0].text)
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
