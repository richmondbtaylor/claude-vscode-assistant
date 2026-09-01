---
name: slideforge
description: |-
  Build branded HTML slide decks for the Bishop AI × SalesDaily.co online course, screenshot each slide at 1280×720px with Playwright, and upload to Google Drive. Use this skill whenever the user provides raw lesson content in the format "LESSON X.Y / [Title] / Target runtime: X minutes / SLIDE CONTENT..." or says things like "make slides for this", "new ones:", "now for this:", "build slides for", or pastes structured slide content with numbered slides. Also trigger when the user asks to redo or fix a specific lesson's slides. Always use this skill for any course slide creation task — do not attempt to build slides without it.
---

# SLIDEFORGE

Build branded slide decks for the **AI Sales Workflows** course (Bishop AI × SalesDaily.co). Each lesson gets 5 slides: 1 title + 4 content. Build the HTML, screenshot with Playwright, upload to Drive.

## Drive Folder

All uploads go to: `1LhCsKe9poKHFdXYfOFmBnX4kPeIpH8AZ`

Upload script: `python scripts/upload_gdrive.py "presentations/<filename>" <folder_id>`

## File Naming

- HTML: `C:\Users\richm\.claude\presentations\<YYYY-MM-DD> <Lesson Title> - online course.html`
- PNGs: `lesson-X-Y-slide-N.png` (e.g. `lesson-6-4-slide-1.png`)
- Use today's date for the HTML filename.

---

## The Build Process

1. Write the HTML to the presentations folder
2. Screenshot with Playwright (5 slides per lesson)
3. Upload all 5 PNGs to Drive
4. Return all 5 Drive links

Run screenshot + upload in one chained Bash command to keep it fast.

---

## Brand System

### Colors
```
--white:     #FAFBFA
--off-white: #E6E2DE
--deep-navy: #000813
--dark-navy: #1D2333
--gold:      #E0B848
--blue:      #1894C9
--red:       #E05252
```

### Fonts (Google Fonts)
- **Poppins 800/900** — H1 on title slide, H2 on dark slides, watermark
- **Montserrat 400–700** — labels, breadcrumbs, section tags, lesson bar
- **Open Sans 400–600** — body copy everywhere

---

## Visual Variety Pattern

Every deck follows this sequence:
- **Slide 1**: Title (deep navy)
- **Slide 2**: Dark split (deep navy, two-column)
- **Slide 3**: White (#FAFBFA)
- **Slide 4**: Off-white (#E6E2DE)
- **Slide 5**: Dark (deep navy, full-width)

---

## HTML Template

Use this boilerplate exactly. Swap in lesson-specific content and CSS per slide.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1280">
<title>Lesson X.Y — [Title]</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800;900&family=Montserrat:wght@400;500;600;700&family=Open+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --white: #FAFBFA; --off-white: #E6E2DE; --deep-navy: #000813;
    --dark-navy: #1D2333; --gold: #E0B848; --blue: #1894C9; --red: #E05252;
  }
  body { font-family: 'Open Sans', sans-serif; background: #888; width: 1280px; }
  .slide { width: 1280px; height: 720px; position: relative; overflow: hidden; display: flex; }

  /* FOOTER */
  .slide-footer { position: absolute; bottom: 26px; left: 60px; right: 60px; display: flex; align-items: center; justify-content: space-between; }
  .footer-brand { display: flex; align-items: center; gap: 8px; font-family: 'Montserrat', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; }
  .footer-brand .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--gold); }
  .slide-num { font-family: 'Montserrat', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 0.1em; }
  .on-light .footer-brand { color: rgba(29,35,51,0.3); }
  .on-light .slide-num   { color: rgba(29,35,51,0.25); }
  .on-dark  .footer-brand { color: rgba(255,255,255,0.25); }
  .on-dark  .slide-num   { color: rgba(255,255,255,0.2); }

  /* LABELS */
  .section-tag { font-family: 'Montserrat', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; }
  .section-tag.gold    { color: var(--gold); }
  .section-tag.gold-lt { color: rgba(224,184,72,0.7); }
  .section-tag.blue    { color: var(--blue); }
  .section-tag.red     { color: var(--red); }
  .lesson-crumb { font-family: 'Montserrat', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; }
  .crumb-light { color: rgba(29,35,51,0.3); }
  .crumb-dark  { color: rgba(255,255,255,0.25); }

  /* SLIDE 1 — TITLE */
  #slide-1 { background: var(--deep-navy); flex-direction: column; padding: 44px 72px 0; }
  #slide-1 .stripe { position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, var(--gold) 0%, rgba(224,184,72,0.15) 100%); }
  #slide-1 .watermark { position: absolute; right: -20px; top: -40px; font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 420px; line-height: 1; color: var(--gold); opacity: 0.04; letter-spacing: -20px; user-select: none; pointer-events: none; }
  .logo-row { display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }
  .bishop-logo { display: flex; align-items: center; gap: 10px; }
  .bishop-logo .icon { width: 36px; height: 36px; }
  .bishop-logo .bname { font-family: 'Montserrat', sans-serif; font-size: 18px; font-weight: 700; color: var(--white); letter-spacing: -0.01em; }
  .lx { font-family: 'Montserrat', sans-serif; font-size: 20px; font-weight: 700; color: rgba(255,255,255,0.35); }
  .salesdaily { display: flex; flex-direction: column; line-height: 1; }
  .salesdaily .sdn { font-family: 'Montserrat', sans-serif; font-size: 18px; font-weight: 700; color: var(--red); }
  .salesdaily .sds { font-family: 'Montserrat', sans-serif; font-size: 9px; font-weight: 600; letter-spacing: 0.22em; text-transform: uppercase; color: rgba(255,255,255,0.3); }
  .breadcrumb { font-family: 'Montserrat', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.22em; text-transform: uppercase; color: var(--gold); margin-bottom: 18px; opacity: 0.8; }
  .breadcrumb .sep { color: rgba(255,255,255,0.18); margin: 0 6px; }
  #slide-1 h1 { font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 52px; line-height: 1.05; color: var(--white); margin-bottom: 16px; max-width: 820px; }
  .title-rule { width: 56px; height: 4px; background: var(--gold); border-radius: 2px; margin-bottom: 16px; }
  #slide-1 .subtitle { font-family: 'Open Sans', sans-serif; font-size: 17px; font-weight: 400; color: rgba(250,251,250,0.55); line-height: 1.55; max-width: 760px; margin-bottom: 24px; }
  .runtime-badge { display: inline-flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 10px 22px; font-family: 'Montserrat', sans-serif; font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.65); }
  .runtime-badge .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--gold); flex-shrink: 0; }
  .lesson-bar { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(255,255,255,0.035); border-top: 1px solid rgba(255,255,255,0.06); display: flex; align-items: stretch; height: 112px; }
  .bar-label { flex-shrink: 0; width: 156px; display: flex; align-items: center; justify-content: center; border-right: 1px solid rgba(255,255,255,0.06); padding: 0 20px; font-family: 'Montserrat', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; color: var(--gold); text-align: center; line-height: 1.4; }
  .bar-items { flex: 1; display: flex; align-items: stretch; }
  .bar-item { flex: 1; display: flex; align-items: center; gap: 12px; padding: 0 22px; border-right: 1px solid rgba(255,255,255,0.06); }
  .bar-item:last-child { border-right: none; }
  .bar-item svg { flex-shrink: 0; width: 18px; height: 18px; }
  .bar-item span { font-family: 'Open Sans', sans-serif; font-size: 12px; color: rgba(250,251,250,0.6); line-height: 1.4; }
</style>
</head>
<body>

<!-- SLIDE 1: TITLE -->
<section class="slide" id="slide-1">
  <div class="stripe"></div>
  <div class="watermark">X.Y</div>
  <div class="logo-row">
    <div class="bishop-logo">
      <svg class="icon" viewBox="0 0 36 36" fill="none">
        <circle cx="18" cy="7" r="4.5" fill="#FAFBFA"/>
        <ellipse cx="18" cy="7" rx="2" ry="2" fill="#E0B848"/>
        <path d="M11 28 C11 18 13 14 18 12 C23 14 25 18 25 28Z" fill="#FAFBFA"/>
        <rect x="9" y="28" width="18" height="3" rx="1.5" fill="#FAFBFA"/>
        <rect x="7" y="31" width="22" height="3" rx="1.5" fill="#FAFBFA"/>
      </svg>
      <span class="bname">Bishop AI</span>
    </div>
    <div class="lx">×</div>
    <div class="salesdaily">
      <span class="sdn">SalesDaily.co</span>
      <span class="sds">Newsletter</span>
    </div>
  </div>
  <div class="breadcrumb">AI Sales Workflows <span class="sep">·</span> Module X <span class="sep">·</span> Lesson X.Y</div>
  <h1>[LESSON TITLE]</h1>
  <div class="title-rule"></div>
  <p class="subtitle">[SUBTITLE]</p>
  <div class="runtime-badge"><div class="dot"></div><span>Runtime: X Minutes</span></div>
  <div class="lesson-bar">
    <div class="bar-label">In This<br>Lesson</div>
    <div class="bar-items">
      <!-- 4 bar-items, one per key point from the lesson content -->
      <div class="bar-item">
        <svg viewBox="0 0 22 22" fill="none"><circle cx="11" cy="11" r="10" stroke="#E0B848" stroke-width="1.5"/><circle cx="11" cy="11" r="6.5" stroke="#E0B848" stroke-width="1.5"/><circle cx="11" cy="11" r="3" fill="#E0B848"/></svg>
        <span>[Point 1]</span>
      </div>
      <!-- repeat for points 2, 3, 4 -->
    </div>
  </div>
</section>

<!-- SLIDES 2–5: design based on content, following the dark/white/off-white/dark pattern -->
<!-- See layout patterns below -->

</body>
</html>
```

---

## Content Slide Layout Patterns

Design each slide to best fit the content. Common patterns:

### Dark Split (Slide 2)
Two columns: left panel (~400px, border-right) with heading + framing text + a highlighted bar; right panel with rows or cards. Both on `background: var(--deep-navy)`.

```html
<section class="slide" id="slide-2">
  <div style="width:400px;flex-shrink:0;display:flex;flex-direction:column;justify-content:center;padding:56px 44px;border-right:1px solid rgba(255,255,255,0.06);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <div class="section-tag gold">[Tag]</div>
      <div class="lesson-crumb crumb-dark">Module X · Lesson X.Y</div>
    </div>
    <h2 style="font-family:'Poppins',sans-serif;font-weight:800;font-size:34px;line-height:1.1;color:var(--white);margin-bottom:18px;">[Heading]</h2>
    <p style="font-family:'Open Sans',sans-serif;font-size:14px;color:rgba(250,251,250,0.6);line-height:1.7;margin-bottom:20px;">[Body]</p>
    <!-- highlight bar: gold, blue, or red tint depending on tone -->
  </div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:13px;padding:56px 46px;">
    <!-- rows, cards, or list items -->
  </div>
  <div class="slide-footer on-dark">
    <div class="footer-brand"><div class="dot"></div>Bishop AI</div>
    <div class="slide-num">2 / 5</div>
  </div>
</section>
```

### White Card Grid (Slide 3)
Full-width on `background: var(--white)`. Use 2×2 grids, compare columns, or vertical rows depending on content count.

```html
<section class="slide" id="slide-3">
  <div style="width:100%;height:100%;display:flex;flex-direction:column;padding:44px 72px 52px;background:var(--white);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <div class="section-tag gold">[Tag]</div>
      <div class="lesson-crumb crumb-light">Module X · Lesson X.Y</div>
    </div>
    <h2 style="font-family:'Montserrat',sans-serif;font-weight:700;font-size:34px;line-height:1.1;color:var(--deep-navy);margin-bottom:20px;">[Heading]</h2>
    <!-- cards/grid -->
    <div class="slide-footer on-light">
      <div class="footer-brand"><div class="dot"></div>Bishop AI</div>
      <div class="slide-num">3 / 5</div>
    </div>
  </div>
</section>
```

### Off-White Rows (Slide 4)
Same structure as white but `background: var(--off-white)`. Works well for numbered steps, lists with left-border accents.

### Dark Full-Width (Slide 5)
Full-width dark slide with gold stripe at top. Good for 2-column grids, outcome cards, closing statements.

```html
<section class="slide" id="slide-5">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--gold) 0%,rgba(224,184,72,0.15) 100%);"></div>
  <div style="width:100%;height:100%;display:flex;flex-direction:column;padding:44px 72px 52px;position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
      <div class="section-tag gold-lt">[Tag]</div>
      <div class="lesson-crumb crumb-dark">Module X · Lesson X.Y</div>
    </div>
    <h2 style="font-family:'Poppins',sans-serif;font-weight:800;font-size:36px;line-height:1.1;color:var(--white);margin-bottom:22px;">[Heading]</h2>
    <!-- 2×2 unlock grid or column layout -->
  </div>
  <div class="slide-footer on-dark">
    <div class="footer-brand"><div class="dot"></div>Bishop AI</div>
    <div class="slide-num">5 / 5</div>
  </div>
</section>
```

---

## Reusable Components

### Highlight bars (use tint to match tone)
```html
<!-- Gold: tips, rules, key points -->
<div style="background:rgba(224,184,72,0.07);border:1px solid rgba(224,184,72,0.18);border-radius:8px;padding:13px 16px;font-family:'Open Sans',sans-serif;font-size:13px;color:rgba(250,251,250,0.7);line-height:1.5;">[text]</div>

<!-- Red: warnings, costs, problems -->
<div style="background:rgba(224,82,82,0.08);border:1px solid rgba(224,82,82,0.2);border-radius:8px;padding:13px 16px;font-family:'Open Sans',sans-serif;font-size:13px;color:rgba(250,251,250,0.7);line-height:1.45;">[text]</div>

<!-- Blue: tools, inputs, neutral info -->
<div style="background:rgba(24,148,201,0.08);border:1px solid rgba(24,148,201,0.2);border-radius:8px;padding:13px 16px;font-family:'Open Sans',sans-serif;font-size:13px;color:rgba(250,251,250,0.7);line-height:1.45;">[text]</div>
```

### Numbered step row (off-white slides)
```html
<div style="display:flex;align-items:flex-start;gap:16px;background:var(--white);border-radius:10px;padding:13px 20px;">
  <div style="width:32px;height:32px;border-radius:50%;background:var(--deep-navy);display:flex;align-items:center;justify-content:center;font-family:'Poppins',sans-serif;font-weight:900;font-size:13px;color:var(--gold);flex-shrink:0;margin-top:1px;">[N]</div>
  <div>
    <div style="font-family:'Montserrat',sans-serif;font-weight:700;font-size:13.5px;color:var(--deep-navy);margin-bottom:3px;">[Label]</div>
    <div style="font-family:'Open Sans',sans-serif;font-size:12.5px;color:rgba(29,35,51,0.6);line-height:1.5;">[Description]</div>
  </div>
</div>
```

### Left-border accent row
```html
<div style="display:flex;align-items:flex-start;gap:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-left:3px solid rgba(224,82,82,0.5);border-radius:8px;padding:15px 18px;">
  <div>
    <div style="font-family:'Montserrat',sans-serif;font-weight:700;font-size:12px;color:var(--red);margin-bottom:4px;letter-spacing:0.05em;">[Scenario label]</div>
    <p style="font-family:'Open Sans',sans-serif;font-size:13px;color:rgba(250,251,250,0.6);line-height:1.5;">[Body]</p>
  </div>
</div>
```

### 2×2 unlock grid (dark slide)
```html
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;flex:1;">
  <div style="background:rgba(224,184,72,0.05);border:1px solid rgba(224,184,72,0.22);border-radius:12px;padding:22px 24px;display:flex;flex-direction:column;gap:10px;">
    <div style="font-family:'Montserrat',sans-serif;font-weight:700;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:var(--gold);">[Label]</div>
    <h3 style="font-family:'Montserrat',sans-serif;font-weight:700;font-size:15px;color:var(--white);line-height:1.3;">[Title]</h3>
    <p style="font-family:'Open Sans',sans-serif;font-size:12.5px;color:rgba(250,251,250,0.55);line-height:1.6;">[Body]</p>
  </div>
  <!-- repeat for other 3 cards with dimmer label color: rgba(224,184,72,0.5) -->
</div>
```

---

## Playwright Screenshot Script

```python
from playwright.sync_api import sync_playwright
from pathlib import Path
HTML = Path(r'C:\Users\richm\.claude\presentations\[filename].html')
OUT  = Path(r'C:\Users\richm\.claude\presentations')
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    page.goto(HTML.as_uri(), wait_until='networkidle')
    for i in range(1, 6):
        el = page.query_selector(f'#slide-{i}')
        if el:
            el.screenshot(path=str(OUT / f'lesson-X-Y-slide-{i}.png'))
    browser.close()
```

Run inline as a one-liner via `python -c "..."`.

## Upload Command

```bash
for i in 1 2 3 4 5; do
  python scripts/upload_gdrive.py "presentations/lesson-X-Y-slide-$i.png" 1LhCsKe9poKHFdXYfOFmBnX4kPeIpH8AZ
done
```

Chain this after the Playwright command with `&&`.

---

## Design Principles

- **Density**: Pack content tightly — slides are read, not presented live. Every pixel matters.
- **No overflow**: If content doesn't fit at the planned font sizes, reduce font size or trim copy — never let content clip outside the 720px height.
- **Gold accents on dark**: Gold (#E0B848) is the primary accent on all dark slides. Use sparingly — headings, icons, borders at low opacity.
- **Montserrat for labels, Open Sans for body**: Never use Poppins for body copy.
- **Lesson crumb always present**: Every content slide has `Module X · Lesson X.Y` in the top-right corner.
- **Footer always present**: Every content slide (2–5) has the slide-footer with "Bishop AI" brand + slide number.
- **Title slide has no footer**: The lesson-bar sits at the bottom instead.
- **Slide 5 always has the gold stripe**: `position:absolute;top:0;left:0;right:0;height:4px;`.

---

## Output Format

After uploading, return links in this format:

```
Lesson X.Y done.

- Slide 1: [Drive link]
- Slide 2: [Drive link]
- Slide 3: [Drive link]
- Slide 4: [Drive link]
- Slide 5: [Drive link]

Ready for X.Z.
```


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

**This skill emits images or decks.** Read `screens/` and `references/VISUAL_GUIDE.md` to describe the visual language in prompts, and `tokens/` for palette bounds.

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
<!-- /design-extract:connector v1 -->
