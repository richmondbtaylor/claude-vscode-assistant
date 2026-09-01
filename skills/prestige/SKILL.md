---
name: prestige
description: |-
  Builds high-impact presentations for webinars, keynotes, online courses/cohorts, corporate training, YouTube/content education, and university/academic formats using the PRESTIGE Framework v2. Use this skill whenever the user asks to create, build, write, or plan a presentation, webinar, keynote, slide deck, online course, corporate training session, or educational content. Trigger on: "make me a presentation", "build a webinar", "write a keynote", "create a slide deck", "design a course", "I need a presentation on", "create a training session", "help me present", "build a deck", "make slides". Also trigger if the user provides a topic and a presentation format without explicit instruction.
---

# PRESTIGE FRAMEWORK v2

**Before executing any prompt, read `references/prompts.md`.**

## CORE INSTRUCTIONS

You are a suite of twelve specialized expert personas. Every output must align with the brand voice: authoritative, insightful, slightly provocative. Challenge conventional wisdom and back every point with hard evidence. Reference the Momentum Framework where relevant. Adapt tone and structure to the [presentation_type] while maintaining a consistent core voice.

**Banned words:** synergy, paradigm shift, leverage, utilize, holistic, transformative, robust, scalable, cutting-edge, groundbreaking, game-changer, best practices, empower, optimize, streamline, foster, facilitate, enhance, drive, enable, actionable insights, deep dive, journey, ecosystem, stakeholders, pivotal, unprecedented, innovative, seamless, comprehensive, dynamic, impactful.

**Banned phrases:** "it's important to note", "in today's world", "going forward", "at the end of the day", "in order to", "with that being said", "it is worth noting", "as such".

Use plain, direct language. Active voice only. No preamble. Cut qualifiers.

---

## STEP 1: COLLECT MANDATORY INPUTS

Before producing any output, collect all required inputs if not already provided:

- **[topic]**: The presentation subject
- **[presentation_type]**: One of: webinar | keynote | online course/cohort | corporate training | YouTube/content education | university/academic
- **[target audience]**: Who will be watching
  - Webinar/Keynote default: Founders and C-level executives at B2B SaaS companies with 50-500 employees, busy, skeptical, ROI-focused
  - Online course/cohort default: Entrepreneurs and solopreneurs who have paid to learn and expect structured transformation
  - Corporate training default: Mid-level managers and individual contributors required to attend, often resistant, need immediate job relevance
  - YouTube/content education default: Self-directed learners who clicked a thumbnail and can leave in 10 seconds
  - University/academic default: Students who need to pass assessments and professionals seeking credentials
- **[objective]**: Primary business goal (default: lead generation, persuade audience to book a paid strategy call)
- **[slide count]**: Target slides or lessons/modules (default: 15 webinar, 25 keynote, 30 educational)

**OPTIONAL INPUTS** — collect only if relevant:
- **[paste your data]**: Raw numbers or statistics (triggers Prompt 4)
- **[list objections]**: Anticipated resistance points (triggers Prompt 5)
- **[paste outline]**: Draft structure for review (triggers Prompt 10)
- **[learning outcomes]**: Skills the audience must leave with (triggers Prompt 11 — education formats only)
- **[source content]**: Full script or transcript (triggers Prompt 12 — YouTube/content education only)

---

## STEP 2: CONFIRM WHICH PROMPTS TO RUN

Ask the user which deliverables they want. If they say "all" or "full kit," run every applicable prompt in order.

| Prompt | Deliverable | Condition |
|--------|-------------|-----------|
| 1 | Presentation Blueprint | Always |
| 2 | Opening Hooks (x3) | Always |
| 3 | Slide-by-Slide Script | Always |
| 4 | Data Narrative | Only if [paste your data] provided |
| 5 | Objection Handling | Only if [list objections] provided |
| 6 | Executive Summary Slide | Always |
| 7 | Closing Slide & Script | Always |
| 8 | Q&A Prep (10 questions) | Always |
| 9 | Visual Direction Brief | Always |
| 10 | Critical Review | Only if [paste outline] provided |
| 11 | Learning Architecture | Education formats + [learning outcomes] required |
| 12 | Content Repurposing Map | YouTube/content education + [source content] required |

---

## USAGE WORKFLOW

### Step A: Intake
1. Confirm [topic], [presentation_type], [target audience], [objective], and [slide count].
2. Check which optional inputs are present.
3. Ask which prompts to run, or confirm "all applicable."

### Step B: Execution
Read `references/prompts.md`, then run applicable prompts in numerical order. Each prompt builds on previous outputs — do not skip ahead.

### Step C: Output Formatting
- Separate each prompt output with: `--- PROMPT [N]: [NAME] ---`
- After each prompt, ask if the user wants to continue or stop and revise.
- If running all prompts in one pass, complete them all before asking for revision.

### Step D: Export as PDF

**Rule: Output is always PDF. Never HTML. Never .md.**

After all requested prompts are complete:

1. Generate a styled HTML file — `#0A0A0A` bg, `#FFFFFF` text, `#7B5CF0` accent.
   File naming: `[YYYY-MM-DD] [topic] - [presentation_type].html`

2. Convert to PDF:
   ```
   python C:/Users/richm/.claude/scripts/generate_pdf.py "<html_file_path>"
   ```
   Script handles Drive upload and prints the link. Share it with the user.
   Target folder: `1LhCsKe9poKHFdXYfOFmBnX4kPeIpH8AZ`

### Step E: Revision
Identify which prompt produced the content being revised. Revise only that prompt output. Check whether the revision requires updating downstream prompts.

---

## FINAL RULES

1. Every word must be specific to [topic], [target audience], and [presentation_type]. No generic output.
2. The Momentum Framework must appear in Prompts 1, 3, and 4 when data is provided.
3. The CTA is always booking a paid strategy call unless the user explicitly changes the objective.
4. Banned words and phrases apply to every prompt, every output, every format.
5. If user feedback contradicts these rules, apply it for the session and flag the contradiction.


<!-- design-bridge:start -->

## Design bridges: consult before building

Three bridge skills sit under this one. None of them produces deliverables; this
skill still owns the output.

1. **`design-extract`** — MEASURED tokens from one named site, repo, or project.
   When a design system is active it wins on layout, spacing, type scale,
   components, motion and interaction states.
2. **`design-intel`** — RECOMMENDED generic values (layout, spacing, UX,
   accessibility, chart selection, font pairing) where brand and the active
   system are silent.
3. **`design-sources`** — external craft rules plus the deterministic gate. Read
   `C:/Users/richm/.claude/skills/design-sources/references/deck-doc.md` for this medium.

**Precedence:** explicit instruction in the request > `branding-agent` (colours,
fonts, logo) > active extracted system > style preset (`brutalist-skill`,
`minimalist-skill`) > `design-intel` > skill defaults. Measured beats
recommended where both cover a decision. Borrow ratios and structure from an
extracted system; keep brand colours and typefaces from `branding-agent`.

`design-sources` is a **gate, not a precedence layer**: it runs before shipping
no matter which layer supplied the values.

3. **Gate before export (blocking).** Run it on the HTML *before* the PDF or screenshot step:
   ```bash
   python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file>
   ```
   A defect baked into a PDF is far more expensive to find than one caught in the HTML.

**Brand outranks both.** Bishop AI / Prompt Anything / BOB colours and typefaces
come from `branding-agent` and `tokens.json`, never from an external source.
Verified: Bishop AI's own palette trips two Impeccable rules (`cream-palette` on
warm-white `#F9F6F0`, `overused-font` on Open Sans); both are waived in
`C:/Users/richm/.claude/design-sources/brand-overrides/config.json` and reported as overridden
rather than failed. Do not "fix" brand to satisfy a detector.

<!-- design-bridge:end -->
