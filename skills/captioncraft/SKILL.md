---
name: captioncraft
description: "Generates platform-specific, near-ready-to-post social media captions from a video transcript using the CAPTAIN Framework. Produces outputs for YouTube, Instagram, LinkedIn, TikTok, and Twitter/X — each adapted to the platform's tone, format, and character limits — using Rich's (Richmond Taylor's) personal copywriting voice: conversational, educational, hook-first, minimal hard-sell. Use this skill whenever the user pastes a video transcript and asks for captions, social posts, or multi-platform content. Trigger on: 'write captions for this', 'make posts from this video', 'caption this transcript', 'generate social content', 'create captions', 'turn this transcript into posts', 'I need social media posts from this', 'make this into LinkedIn content', 'post this to TikTok'. Also trigger if the user shares a transcript with no explicit instruction — they almost certainly want captions from it."
---

# CaptionCraft

Turn any video transcript into platform-specific, near-ready-to-post social media captions in Rich's voice — hook-first, educational, minimal hard sell, all five platforms covered in one pass.

## Rich's Copywriting Voice

Rich (Richmond Taylor) writes the way a smart friend explains something — not a marketer pitching you. His posts:

- **Open with a hook**: a relatable question, a bold claim, or a surprising observation that makes you stop scrolling
- **Teach, don't sell**: the content itself is the value. Readers should feel smarter after reading, not sold to
- **Stay conversational**: natural contractions, direct address ("you"), accessible language — no buzzword soup
- **Acknowledge the reader's reality**: "you've probably felt this too" — positions ideas within shared experience
- **Keep CTAs soft**: "link in bio", "full video below", "worth a watch" — not "BUY NOW" energy
- **Use emojis sparingly**: one or two max on casual platforms, zero on LinkedIn unless it's a bullet point situation
- **Niche**: AI automation, business productivity, go-to-market strategy, sales AI, thought leadership

## CAPTAIN Framework

Process every transcript through these lenses before writing a single word:

### [C] Context
The primary goal is always to **drive traffic back to the full YouTube video**. Every caption is a teaser, not the full meal. Hook fast, deliver a taste of value, then direct viewers to the source. Brand voice is informative + approachable + enthusiastic. Never hype, never cringe.

### [A] Audience (per platform)
- **YouTube**: already engaged viewers who want depth — reward them with keywords and structure
- **LinkedIn**: working professionals, founders, GTM leaders — they want professional insight and practical takeaways
- **Instagram**: aspiration + lifestyle — they respond to visuals and punchy ideas, not bullet lists
- **TikTok**: fast-moving, trend-aware, younger/casual — they'll swipe in a second; the first line is everything
- **Twitter/X**: broad + fast — needs to stand alone in 280 chars or less, punchy enough to stop the scroll

### [P] Platform Requirements
- **YouTube**: 2-sentence hook at the top (keyword-rich) + full description with timestamps if identifiable + CTA to like/subscribe
- **LinkedIn**: 150–250 words, hook line, 3–5 key insights or a short story, soft CTA, 3–5 hashtags at the bottom
- **Instagram**: 1–3 punchy sentences, visual hook angle, 5–10 hashtags inline or at bottom
- **TikTok**: 1–2 casual lines (under 150 chars), trending sound suggestion, 3–5 hashtags
- **Twitter/X**: single tweet under 280 chars OR a 3-tweet thread if the content warrants it

### [T] Tone (per platform)
- **YouTube**: warm, informative, inviting
- **LinkedIn**: professional, insightful, subtly enthusiastic
- **Instagram**: lifestyle, aspirational, visually suggestive
- **TikTok**: casual, punchy, trend-aware
- **Twitter/X**: bold, direct, slightly provocative

### [I] Input Processing
When you receive a transcript:
1. Scan for the 3–5 most shareable moments: surprising stats, strong opinions, actionable frameworks, or relatable pain points
2. Identify the single best hook — the one line that would make someone stop scrolling
3. Note any timestamps where key moments occur (for YouTube descriptions)
4. Extract the core value proposition: what does someone get from watching the full video?

### [O] Output Format
Always deliver all five platforms, grouped and clearly labeled. Use this exact structure:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUTUBE DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[hook line 1]
[hook line 2]

[full description — 100-150 words, keyword-rich]

TIMESTAMPS (if identifiable):
00:00 — [topic]
...

[CTA — e.g., "Like and subscribe if this was useful."]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LINKEDIN POST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[hook line]

[body — insight-led, 150-250 words, line breaks for readability]

[soft CTA — e.g., "Full video in the comments."]

#hashtag1 #hashtag2 #hashtag3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTAGRAM CAPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1-3 punchy sentences]

[5-10 hashtags]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIKTOK CAPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1-2 casual lines, under 150 chars]

Trending sound suggestion: [suggest a relevant sound type, e.g., "lo-fi study beat", "viral explainer tone", "trending audio from @creator"]

#hashtag1 #hashtag2 #hashtag3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TWITTER / X
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[single tweet under 280 chars — OR — 3-tweet thread labeled 1/, 2/, 3/]
```

### [N] Niche & Brand Safety

**Always include (rotate as appropriate):**
`#AIAutomation` `#BusinessAutomation` `#Productivity` `#FutureOfWork` `#AutomationNation` `#AITools` `#WorkSmarter` `#GTM` `#SalesAI` `#AIForBusiness`

**Always avoid:**
- Competitor brand names (no naming tools, platforms, or people we don't endorse)
- Controversial AI ethics debates (keep it practical, not political)
- Anything that sounds like fear-mongering or hype ("AI will replace all jobs", "this changes EVERYTHING")
- Hard-sell language ("buy now", "limited time", "don't miss out")

## Google Drive Upload

After generating all captions, **always** upload them to Google Drive automatically by running `scripts/upload_to_drive.py`. Do not ask — just do it.

```python
python scripts/upload_to_drive.py "<Video Title>" <<EOF
[full caption output]
EOF
```

The script POSTs to the n8n webhook, which saves a `.txt` file named `[VideoTitle]_Captions_[Date].txt` into the Google Drive folder. It returns a confirmation link — include it in your reply to Rich so he can find the file instantly.

If the upload fails, show the captions in chat as normal and note the upload error.

## Quality Check Before Delivering

Before outputting, ask yourself:
- Does every platform have a distinct hook, not just the same opening reworded?
- Does LinkedIn read like a professional insight, not a YouTube ad?
- Is the TikTok caption genuinely casual — like something a real person would type?
- Is the Twitter/X post punchy enough to stand alone without context?
- Does the YouTube description have keywords a real searcher would use?
- Would Rich be proud to post this, or does it feel generic?

If something feels generic or cookie-cutter, rewrite it. The goal is posts Rich could copy-paste with only minor edits.


## Banned Language

Before delivering any output, check all copy against `~/.claude/skills/references/banned-phrases.md`.

Never use: game-changer, transformative, cutting-edge, seamless, revolutionize, innovative, robust, scalable (vague), synergy, circle back, actionable insights, deep dive, leverage (verb), crushing it, skyrocket, dominate your niche, thought leader, pain points, humbled and honored, let that sink in, hot take, I'm excited to share, certainly!, great question!, in today's digital landscape, delve into, holistic, multifaceted, foster, empower, utilize, unprecedented, groundbreaking, paradigm shift, disruptive, at the forefront, frictionless, unlock (vague), streamline, no-brainer, secret sauce, go viral (empty goal), low-hanging fruit, move the needle.
