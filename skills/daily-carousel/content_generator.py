"""
Content Generator -- Uses Claude Code CLI (Max subscription) to create carousel content.

Takes topic candidates from the researcher, picks the best one,
generates slide-by-slide content, captions, and hashtags.
Uses the `claude` CLI so it runs on the Max plan, not API credits.
"""

import json
import subprocess
import sys

from config import HANDLE, SLIDE_COUNT_RANGE, STYLE_PRESETS, get_next_cta


def generate_content(topics: list[dict]) -> dict:
    """
    Pick the best topic from candidates and generate full carousel content.
    Returns a dict with slides, captions, hashtags, style, and CTA.
    """
    cta = get_next_cta()

    # Format topics for Claude
    topics_text = ""
    for i, t in enumerate(topics, 1):
        topics_text += f"\n{i}. Title: {t['title']}\n"
        topics_text += f"   Source: {t['source']}\n"
        topics_text += f"   Description: {t.get('description', 'N/A')[:200]}\n"
        topics_text += f"   Carousel Score: {t.get('carousel_score', 0)}\n"

    style_options = "\n".join(
        f"- {name}: bg={s['background']}, text={s['text_color']}, accent={s['accent']} (best for: {s['best_for']})"
        for name, s in STYLE_PRESETS.items()
    )

    min_slides, max_slides = SLIDE_COUNT_RANGE

    prompt = f"""You are an expert social media content strategist for Bishop AI ({HANDLE}).
You create high-performing carousel posts: visually minimal, information-dense, no fluff, punchy clarity.
Brand voice: educational, conversational, confident. Like a smart friend explaining something useful.

Rules:
- Max 3 lines per slide
- Max 8 words per line
- No paragraphs or walls of text
- Slide 1 is always a scroll-stopping hook
- Final slide is always a CTA
- Never use: leverage, synergy, empower, optimize, utilize, facilitate, streamline,
  you won't believe, this one trick, mind-blowing, game-changer, limited time,
  act now, don't miss out, basically, essentially, literally, very, really
- Never use em dashes
- Use specific claims, not vague hype

I have these 3 trending AI topics. Pick the ONE best for a carousel post and generate the full content.

TOPICS:
{topics_text}

CTA FOR FINAL SLIDE: "{cta['slide_text']}"

STYLE PRESETS AVAILABLE:
{style_options}

Generate a JSON response with this exact structure:
{{
  "chosen_topic": {{
    "index": 1,
    "title": "the original topic title",
    "angle": "your specific carousel angle on this topic (not just the title restated)"
  }},
  "style_preset": "one of: clean_editorial, dark_professional, bold_minimal, bishop_ai_brand, notebook_sketch",
  "slides": [
    {{
      "number": 1,
      "type": "hook",
      "headline": "max 8 words, scroll-stopping",
      "subtext": "max 8 words, optional supporting line",
      "visual_notes": "layout and visual cues for image generation"
    }},
    ... (value slides, {min_slides}-{max_slides} total including hook and CTA),
    {{
      "number": N,
      "type": "cta",
      "headline": "{cta['slide_text']}",
      "subtext": "optional supporting line",
      "visual_notes": "centered, bold, clear action"
    }}
  ],
  "instagram_caption": "1-3 punchy sentences. Hook first. End with the CTA: {cta['caption_text']}",
  "linkedin_caption": "150-250 words. Educational tone. List the key insights. End with CTA.",
  "instagram_hashtags": ["10 hashtags without # symbol"],
  "linkedin_hashtags": ["5 hashtags without # symbol"]
}}

Requirements:
- Pick the topic with the highest viral + carousel potential
- Each slide headline: max 8 words, max 3 lines
- Slide 1 must be a genuine scroll-stopper, not generic
- Value slides must teach something real and specific
- Use the numbered-list format if it's tips/tools, step-by-step if it's a process
- Instagram caption: short, punchy, hook-first
- LinkedIn caption: longer, educational, insight-driven
- Return ONLY valid JSON, no markdown code blocks, no explanation text"""

    print("[content] Generating carousel content via Claude Code CLI (Max plan)...")

    # Call claude CLI with --print flag for non-interactive output
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed (exit {result.returncode}): {result.stderr[:500]}")

    raw_output = result.stdout.strip()

    # claude --output-format json wraps the response in a JSON envelope
    # Extract the actual text content
    try:
        cli_response = json.loads(raw_output)
        # The CLI JSON format has a "result" field with the text
        if isinstance(cli_response, dict) and "result" in cli_response:
            response_text = cli_response["result"].strip()
        elif isinstance(cli_response, dict) and "content" in cli_response:
            response_text = cli_response["content"].strip()
        else:
            # Maybe the whole thing is already our carousel JSON
            response_text = raw_output
    except json.JSONDecodeError:
        response_text = raw_output

    # Strip markdown code fences if present
    if "```" in response_text:
        # Find JSON between code fences
        parts = response_text.split("```")
        for part in parts:
            stripped = part.strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
            if stripped.startswith("{"):
                response_text = stripped
                break

    # Find the JSON object in the response
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start >= 0 and end > start:
        response_text = response_text[start:end]

    carousel = json.loads(response_text)
    carousel["cta_used"] = cta

    topic_title = carousel.get("chosen_topic", {}).get("title", "unknown")
    slide_count = len(carousel.get("slides", []))
    print(f"[content] Topic: {topic_title}")
    print(f"[content] Slides: {slide_count}")
    print(f"[content] Style: {carousel.get('style_preset', 'unknown')}")
    print(f"[content] CTA: {cta['slide_text']}")

    return carousel


if __name__ == "__main__":
    # Test with dummy topics
    test_topics = [
        {"title": "5 Claude Code tips nobody talks about", "source": "reddit/r/ClaudeAI", "description": "Great tips for using Claude Code", "carousel_score": 80},
        {"title": "AI agents will replace 50% of SaaS", "source": "brave", "description": "Industry prediction", "carousel_score": 60},
        {"title": "How I automated my entire marketing with AI", "source": "reddit/r/artificial", "description": "Full breakdown", "carousel_score": 70},
    ]
    result = generate_content(test_topics)
    print(json.dumps(result, indent=2))
