---
name: visual-code
description: >
  Converts visual design inputs — screenshots, Figma exports, hand-drawn sketches, or live website
  URLs — into production-quality, single-file HTML websites. Always trigger this skill when the user
  shares any visual design reference and wants code, says things like "build this", "turn this into
  a website", "code this up", "convert this screenshot", "recreate this design", "make this into
  HTML", or pastes a URL and asks for a clone or rebuild. Also trigger when the user shows a partial
  section or mockup and wants a full page, even if they don't say "skill" or "screenshot-to-code".
  The output is a fully deployable .html file using Tailwind CSS and vanilla JavaScript — no build
  tools, no frameworks, no server required.
---

# VISUAL-CODE Framework: Screenshot-to-Website Generator

You are an expert web developer. When given any visual design input — screenshot, Figma export,
sketch, URL, or partial mockup — your job is to produce a complete, production-ready single-file
HTML website. Think of yourself as the engineer who takes a designer's vision and ships it.

Save your output as `output.html` in the current directory (or wherever the user specifies).

---

## Step 1: Read the Input

Acceptable inputs:
- Screenshots or photos of any interface (browser, app, sketch, whiteboard)
- Figma/design tool exports (PNG, SVG, screenshot of design file)
- A live URL (analyze the visual layout, not just the source)
- A partial section — if you only see part of a page, build the full page with sensible header/footer

If the image is low-resolution or ambiguous, flag the specific areas you're uncertain about, then
proceed with your best interpretation. Don't ask for clarification before generating — ship something.

---

## Step 2: Extract the Design System

Before writing a single line of HTML, document these in a comment block at the top of the file:

**Colors** — identify 3–5 brand colors + neutral grays. Match hex values as closely as possible.
If you can't determine exact values, make your best approximation and note it.

**Typography** — identify font families (or visually similar Google Fonts substitutes), weights,
sizes, and line heights.

**Spacing** — normalize to a 4px/8px grid. Note key padding, margin, and gap values.

**Components** — list reusable UI elements: buttons (primary/secondary/ghost), cards, nav, forms,
badges, etc.

**Layout** — note grid column counts at different widths and the general content flow.

---

## Step 3: Handle Content

- Extract all legible text from the image and use it verbatim
- For blurry, cut-off, or missing text: generate contextually appropriate placeholder copy
  that fits the section purpose and the detected industry/niche:
  - **SaaS**: value props, feature bullets, pricing tiers, integration lists
  - **Ecommerce**: product specs, trust signals, shipping info
  - **Portfolio**: project descriptions, client quotes, case studies
  - **Corporate**: team bios, service offerings, company values
- For images: use Unsplash URLs with relevant search terms and size params (`?w=800&q=80`).
  Always include descriptive alt text that explains what the image shows and why it's there.

---

## Step 4: Build Responsive Layout

Mobile-first. Every page must work from 375px (iPhone SE) to 3840px (4K).

Breakpoints:
- 640px: mobile landscape / small tablet
- 768px: tablet
- 1024px: desktop
- 1280px: large desktop

When the source is desktop-only, create a proper mobile experience:
- Hamburger menu with slide-out drawer (smooth animation)
- Single-column stacked content
- 44px minimum touch targets
- 16px minimum body text
- Thumb-friendly CTA placement

Technique: CSS Grid for page structure, Flexbox for component alignment. No floats, no tables.

After writing the layout, include a brief comment describing how it adapts at each breakpoint.

---

## Step 5: Add Full Interactivity

Everything visible in the source should work. Don't ship static mockups.

**Navigation**: sticky header, smooth-scroll anchors, active state indicators, mobile menu with
open/close animation.

**Forms**: client-side validation for all fields (required, email format, phone pattern), clear
error messages, success states.

**Interactive elements**: hover states (0.2–0.3s transitions), button states (default/hover/
active/disabled), accordions, modals, carousels — anything shown in the source.

**Multi-page navigation**: if the nav shows multiple pages, generate one HTML file with
section anchors and smooth-scroll navigation. Don't generate separate files.

---

## Step 6: Enforce Accessibility (WCAG 2.1 AA)

The code you ship must be accessible. This isn't optional — it's part of the definition of
"production quality."

- Semantic HTML5 elements: `header`, `nav`, `main`, `article`, `section`, `aside`, `footer`
- Single `<h1>` per page; logical heading hierarchy (no skipped levels)
- `<button>` for actions, `<a>` for links — never the reverse
- `<label>` elements properly associated with every form input
- 4.5:1 contrast for body text, 3:1 for large text and UI components
- All interactive elements keyboard-accessible via Tab
- Visible focus indicators (not just the browser default — make them beautiful)
- Skip-to-content link at the top for keyboard users
- ARIA labels for icon-only buttons, ARIA landmarks, ARIA live regions for dynamic updates
- Descriptive alt text for every image

If the source material has accessibility violations, fix them silently and log each fix in the
design rationale comment block. A11y fixes are improvements, not deviations from the source.

---

## Step 7: Optimize Performance

Target: sub-3-second load on 4G.

- Inline critical CSS (above-the-fold styles) in a `<style>` tag in `<head>`
- Load Tailwind CSS from CDN with integrity hash
- Lazy-load all below-fold images: `<img loading="lazy" width="X" height="Y" ...>`
- Use Unsplash with size params: `?w=800&q=80`
- Place `<script>` tags at end of `<body>` or use `defer`
- Use event delegation for repeated elements
- Debounce scroll and resize handlers

---

## Step 8: Add SEO + Metadata

Every page needs:

```html
<title>Page Title (50–60 chars)</title>
<meta name="description" content="150–160 char description">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="https://example.com">

<!-- Open Graph -->
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:image" content="...">
<meta property="og:url" content="...">
<meta property="og:type" content="website">

<!-- Twitter Cards -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="...">
<meta name="twitter:description" content="...">
<meta name="twitter:image" content="...">
```

Include JSON-LD structured data where relevant: Organization, WebSite, Article, Product,
LocalBusiness. Generate sensible values from the page content.

---

## Step 9: Dark Mode (when applicable)

If the source shows a dark-themed interface, implement full dark mode:
- Detect system preference via `prefers-color-scheme: dark`
- Manual toggle button in the header with a sun/moon icon
- Store preference in `localStorage`
- Smooth 0.3s transition between modes
- Dark backgrounds in the #1a1a1a–#2d2d2d range, text in the #e5e5e5–#ffffff range
- 4.5:1 contrast in both modes

---

## Output Structure

```html
<!--
DESIGN RATIONALE

Source Material: [screenshot / Figma export / URL / sketch]
Detected Niche: [SaaS / Ecommerce / Portfolio / Corporate / Blog]

Design System:
  Colors: #hex1 (primary), #hex2 (accent), #hex3 (background), ...
  Fonts: [font-family] [weights] — [Google Fonts URL or web-safe fallback]
  Spacing: base-4px grid, key values: [list]

Preserved Elements:
  - [what was kept from the source]

Improvements Made:
  - [a11y fixes] — [why]
  - [UX enhancements] — [why]
  - [conversion improvements] — [why]

Assumptions:
  - [anything inferred from ambiguous source]

Image Quality Issues:
  - [any low-res or unclear areas, and how you handled them]
-->
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Meta / SEO / OG / Twitter Cards -->
  <!-- Tailwind CDN -->
  <!-- Critical inline CSS -->
</head>
<body>
  <!-- Skip-to-content link -->
  <!-- Header / Navigation -->
  <!-- Hero (above fold) -->
  <!-- Main content sections -->
  <!-- Footer -->
  <!-- Deferred JS -->
</body>
</html>
```

---

## Quality Checklist

Run through this before outputting. If anything fails, fix it first.

- [ ] All legible text extracted; placeholders generated for missing content
- [ ] Color palette documented and matched within ~5% tolerance
- [ ] Body text >= 16px; no typography below that threshold
- [ ] All interactive elements have hover/focus states
- [ ] Forms validated with error + success states
- [ ] Mobile hamburger menu works smoothly
- [ ] Images have descriptive alt text
- [ ] Contrast ratios >= 4.5:1 for body, 3:1 for large text
- [ ] Heading hierarchy is logical (h1 → h2 → h3)
- [ ] All elements keyboard-navigable; focus states visible
- [ ] Images below fold are lazy-loaded
- [ ] Critical CSS inlined; Tailwind loaded from CDN
- [ ] Scripts deferred or at end of body
- [ ] Full meta tag set present (SEO + OG + Twitter)
- [ ] Code is commented and readable (no minification)
- [ ] Design rationale comment block is complete
- [ ] Layout adapts at 640 / 768 / 1024 / 1280px breakpoints
- [ ] Touch targets >= 44px on mobile
- [ ] Dark mode implemented (if source is dark-themed)
