---
name: course-builder
description: |-
  Build complete, fully-written multi-page course websites in the Bishop AI HTML design system. Use this skill whenever anyone wants to create, build, or generate a course website — whether they say "make me a course on X", "build a course site", "turn this outline into a course website", "I want to set up a course for [topic]", "create lesson pages for my program", or any variation of turning educational content into a deployable HTML site. Works for any topic — cooking, fitness, business, coding, marketing, creative skills, anything. Also trigger when someone shares a curriculum, session breakdown, or course outline and asks to convert it into a website. Produces a complete deployable site ready for Netlify: student hub, teacher hub, all session pages, and reference pages.
---

# Course Builder

**This skill is content-agnostic.** The HTML template, design system, and page structure are fixed. The course topic, content, and structure come entirely from you.

The output is a complete multi-page course website using the Bishop AI design system (navy/gold/cream). Every page is fully written — actual content, real activities, specific timing, genuine instructor notes. No placeholders.

**Reference implementation:** `C:\Users\richm\.claude\presentations\email-marketing\`
Read `index.html`, `session-01.html`, and `teacher-index.html` from that folder before generating anything — those files show the exact patterns to follow. Also read `references/patterns.md` in this skill directory for annotated HTML templates.

---

## Step 1 — Get the Course Content

### Option A: You have an outline or doc
Paste it. Extract the structure, confirm your understanding, then generate. Ask any gaps before starting.

### Option B: No outline — interview mode
Ask these two passes. Don't ask everything at once.

**Pass 1 — Core shape (ask all at once):**
- What is the course about, and who is it for?
- What do students walk away with? (The core promise in one sentence)
- How many sessions/lessons, and how long is each?
- What tools or platforms will students use?
- Does the course have a named workflow or framework? (e.g. a multi-stage process you want visualized) — yes/no

**Pass 2 — Session content (ask session by session if needed):**
For each session: title, the goal in one sentence, 2 teaching blocks (what concept is taught + the key point to land), 2–4 activities with timing, any prompts or exercises students run, and what they produce by the end.

Also ask: Does this course use Claude Projects or any persistent AI workspace where students save outputs as files? This determines whether `.callout-save` TXT instructions appear.

Don't start generating until you have enough to write real content. Vague inputs = generic pages. Push for specifics.

---

## Step 2 — File Structure

Output goes to: `C:\Users\richm\.claude\presentations\[course-slug]\`

Slug = lowercase, hyphens (e.g. `instagram-growth`, `sourdough-fundamentals`, `python-for-beginners`).

```
[course-slug]/
├── assets/
│   ├── colors_and_type.css    ← copy from email-marketing reference
│   └── course.css             ← copy from email-marketing reference
├── index.html                 ← student hub
├── teacher-index.html         ← teacher hub
├── session-01.html            ← one per session, zero-padded
├── session-0N.html
├── deliverables.html
├── assignments.html           ← skip if no between-session work
├── 00-tools.html
├── 00-framework.html          ← skip if no named workflow/framework
└── netlify.toml
```

Copy CSS first:
```bash
mkdir -p "C:/Users/richm/.claude/presentations/[slug]/assets"
cp "C:/Users/richm/.claude/presentations/email-marketing/assets/colors_and_type.css" "C:/Users/richm/.claude/presentations/[slug]/assets/"
cp "C:/Users/richm/.claude/presentations/email-marketing/assets/course.css" "C:/Users/richm/.claude/presentations/[slug]/assets/"
```

---

## Step 3 — Generate In This Order

1. `netlify.toml` (one line: `publish = "."`)
2. `index.html` — student hub
3. `teacher-index.html` — teacher hub
4. Session pages — one at a time, in order
5. `deliverables.html`
6. `assignments.html` (if applicable)
7. `00-tools.html`
8. `00-framework.html` (if applicable)

---

## The Four Page Types

### 1. Student Hub — index.html

Landing page feel, not a syllabus. Beginner-friendly and visual.

Sections (in order):
1. **Hero** — outcome h1, lede, stats row (sessions / hours / deliverables / key tool or cost), two CTA buttons, optional workflow visual strip if course has a named framework
2. **Who Is This For** — dark navy card, two columns: "Great fit if you..." / "You don't need to..."
3. **What You'll Build** — 3-col deliverables grid, each card: icon + name + description + session tag
4. **Tools** — 3-col tools grid, each card: icon + role label + name + description + cost
5. **Journey Timeline** — vertical, one item per session with colored number, title, description, outcome chip
6. **Session Quick-Nav** — clickable session cards with icon, number, title, description, stage badge
7. **Resources** — 2-col grid linking to reference pages

### 2. Teacher Hub — teacher-index.html

Run-of-show for the instructor. Dense and practical.

Structure:
- Sticky jump nav at top linking to each `#session-NN`
- 6 core teaching rules (non-negotiable principles for this course)
- One `session-block` per session with:
  - Dark navy header (number, title, time, tools, link to session page)
  - Color-coded timeline rows:
    - **Yellow** `row-teach` — teaching block
    - **Blue** `row-hands` — hands-on activity
    - **Purple** `row-group` — group discussion
    - **Green** `row-setup` — setup / pre-session
  - Each row: time badge, title, description, instructor note (orange), watch-for (red), done-when (green)
  - Deliverables strip at the bottom

### 3. Session Pages — session-NN.html

Fully written. Every element present.

Required elements:
- **Doc header** — eyebrow (session N · duration · hands-on time), title, 2–3 lede paragraphs (why this session, what it unlocks, what breaks if skipped), meta row (stage / tools / deliverables / format)
- **Workflow strip** — if course has a framework, show all stages with active ones highlighted
- **Timetable** — every activity listed, minute totals that actually add up
- **Teaching blocks** — eyebrow, title, sub (what to cover)
- **Activities** — eyebrow, title, sub, instructor bullets, pill row (tool/output), prompt blocks with real prompt text, callouts
- **Page nav** — ← Previous / Next →

### 4. Reference Pages

- **deliverables.html** — every deliverable from all sessions, grouped by session
- **assignments.html** — between-session work per session (what, why, what to bring next)
- **00-tools.html** — one section per tool: what it is, setup steps, cost, role in this course
- **00-framework.html** — if applicable: each stage of the workflow explained

---

## Optional Components (include when relevant)

**Workflow visual strip on index.html** — only if the course has a named multi-stage framework. Shows each stage with an emoji, label, and which sessions cover it.

**`.workflow` strip on session pages** — same framework shown per-session with active stages highlighted.

**`.callout-save` blocks** — only if the course uses Claude Projects or a persistent AI workspace where students upload files. Add immediately after any prompt that produces a Google Doc:
```html
<div class="callout callout-save"><div class="callout-mark"></div><div>
  <div class="callout-label">Save to Your Project</div>
  <div class="callout-body"><p>Download as Plain Text: <strong>File → Download → Plain Text (.txt)</strong>. Upload to your Project files. Name it <code>S01-Document-Name.txt</code>.</p></div>
</div></div>
```
First occurrence in the course gets a full walkthrough (see `references/patterns.md`).

---

## Content Standards

- No `[placeholder]` brackets in final output
- Prompt blocks contain real prompt text students can copy and paste — not a description of what the prompt does
- Timetable minutes add up correctly
- Instructor notes explain the *why*, not just the what
- "Done when" criteria are specific and observable, not vague
- Lede paragraphs on session pages explain downstream consequences — what breaks in later sessions if this one is skipped

---

## Naming Conventions

- Course folder: `[course-slug]` (lowercase, hyphens)
- Session files: `session-01.html` … `session-NN.html` (zero-padded)
- `data-screen-label` on `<body>`: `"Student Hub"`, `"01 Session 01"`, `"Teacher Hub"`, etc.
- All `href` values: relative paths only
- TXT file names (if used): `S0N-Document-Name.txt`

---

## Quality Check Before Done

- [ ] All session files exist and are linked from both hubs
- [ ] Timetable totals are correct on every session page
- [ ] No placeholder brackets remain
- [ ] All internal links resolve correctly
- [ ] Teacher hub covers every session
- [ ] Journey timeline has one entry per session
- [ ] Page nav (← / →) is correct on every session page
- [ ] CSS files are in `assets/`
- [ ] `netlify.toml` exists at root


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
<!-- design-extract:connector v1 -->

---

## Extracted Design System

**First, scan the request for the literal phrase "full <name> system"** (e.g. "full linear
system"). Near-miss phrasings — "use Linear's colors", "make it look like Linear", "match
Linear's branding" — do NOT count. Only the literal phrase.

- **Phrase present** -> that extracted system supersedes `branding-agent` for this one
  deliverable. Read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`, and use its
  colors and font families directly.
- **Phrase absent** -> resolve the active system the normal way:
  1. A system named in the request ("in the linear system", "build this like Stripe"), or a
     `.design-system` marker file in the working folder.
  2. If found, read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`.
  3. **BORROW** from it: layout, spacing grid, type scale ratios, component patterns,
     motion, easing, interaction states.
     **KEEP from `branding-agent`:** Bishop AI / Prompt Anything colors, font families, logo
     treatment.
  4. Nothing active -> proceed exactly as normal. This block adds no default behavior.

Measured beats recommended: where an active system covers a decision, it outranks
`design-intel`. Where it is silent — accessibility, chart choice, breakpoints —
`design-intel` is still the answer.

**This skill emits code.** Read `tokens/colors.json`, `tokens/typography.json`, `tokens/spacing.json`, and `fonts/`. Use those values exactly as written — do not round them or substitute a close-enough value.

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
<!-- /design-extract:connector v1 -->
