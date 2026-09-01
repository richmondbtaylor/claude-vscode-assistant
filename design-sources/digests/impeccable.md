# Impeccable — distilled digest

Source: `pbakaus/impeccable` v3.6.1, commit `bfafc7d`, Apache-2.0.
Full checkout: `~/.claude/design-sources/impeccable/`.
Read this file by default. Open the checkout only when you need depth this
digest does not carry.

Impeccable is design guidance for AI coding agents. It exists because every
model trained on the same SaaS templates, so ungoverned AI frontend output
converges on the same tells. Its value to us is twofold: a **craft floor** we
read, and a **deterministic detector** we run.

---

## 1. The detector (this is the part that gates)

47 deterministic rule IDs, no LLM, no API key. Verified behaviour:

| | |
|---|---|
| Command | `impeccable detect <file\|dir\|url>` |
| Clean exit | `0` |
| Findings exit | `2` |
| JSON | `--json` |
| Scope to a domain | `--scope type,layout` |
| Mobile pass | `--viewport 390x844` |

**Non-negotiable:** run the globally installed `impeccable` binary. Running the
bare checkout prints `DEGRADED - HTML parser modules unavailable` and silently
undercounts. Verified: the same file yields 1 finding degraded vs 4 installed,
and contrast is not computed at all when degraded. A degraded pass is not a
clean bill of health.

**Advisory rules** are listed but never change the exit code (`em-dash-overuse`
is one). Rich bans em dashes outright, so an advisory hit is still a fix for us.

### The 47 rule IDs

```
ai-color-palette all-caps-body blinking-cursor body-text-viewport-edge
border-accent-on-rounded bounce-easing clipped-overflow-container
codex-grid-background content-hidden-at-rest cramped-padding cream-palette
dark-glow em-dash-overuse extreme-negative-tracking flat-type-hierarchy
gpt-thin-border-wide-shadow gradient-text gray-on-color hero-eyebrow-chip
icon-tile-stack image-hover-transform italic-serif-display justified-text
kicker-above-heading layout-transition line-length low-contrast marquee
monotonous-spacing nested-cards numbered-section-labels oversized-h1
overused-font pulsing-dot radial-halo radial-spotlight-glow
repeated-container-text repeating-stripes-gradient shape-assembled-illustration
side-tab skipped-heading text-overflow theater-slop-phrase tight-leading
tiny-text undersized-ui-text wide-tracking
```

### Rules that overlap Rich's standing rules

These fire on things Rich already bans, so the detector enforces his rules for
free: `em-dash-overuse`, `gray-on-color`, `low-contrast`, `overused-font`
(Inter/Roboto/Fraunces/Geist/Plus Jakarta Sans/Space Grotesk),
`ai-color-palette` (purple→blue gradients and cyan-on-dark).

---

### Known limitation: `clamp()` is invisible to the static scan

Verified at source (`rules/checks.mjs`, the `flat-type-hierarchy` collector) and
reproduced end to end. The static engine reads computed styles through jsdom,
which **cannot resolve `clamp()`**. Any element whose winning `font-size` is a
`clamp()` drops out of the sample entirely.

Consequence: a page with a 58px `clamp()` h1 reports only its small static sizes
and fails `flat-type-hierarchy`, even though the real hierarchy is fine. A
`font-size:58px; font-size:clamp(...)` fallback pair does **not** help, because
the clamp declaration still wins the cascade.

Two honest responses, in order of preference:

1. **Express the type scale with media queries instead of `clamp()`.** Static
   sizes at the desktop default, stepped down in a `@media (max-width:700px)`
   block. Same responsive result, and the scan can see it. This is what the
   smoke-test one-pager does, and it passes desktop and mobile cleanly.
2. If a page must keep `clamp()`, treat a lone `flat-type-hierarchy` finding as
   unverified: confirm the hierarchy by eye, say so explicitly, and do not add a
   blanket override. Waiving the rule outright would hide the real defect class
   it exists to catch.

The rule itself is correct: with static sizes the same page scores 3.9:1 and
passes. Do not disable it.

## 2. The craft floor (read before building UI)

Checks on the **built result**, not intentions.

- **Contrast** — body and placeholder ≥4.5:1, large text ≥3:1. On coloured
  surfaces tint secondary text from that hue. Never gray.
- **Depth** — shadows carry an offset *and* a soft blur. A zero-offset coloured
  halo is decoration, not depth.
- **Spacing** — tight groups, generous separation, more space above a heading
  than below it. Read the computed values.
- **Type** — body measure 65–75ch, display max 6rem, tracking floor -0.04em
  (-0.02 to -0.03em usually reads better), obvious scale and weight steps. Run
  the real copy at every breakpoint and fix what overflows.
- **Motion** — one authored moment, not scattered effects, and not one identical
  entrance on every section. Exponential ease-out from an already-visible
  default. Blur, backdrop-filter, clip-path, mask and shadow are in the palette.
- **States** — hover, disabled, loading, error, empty. Plus real content,
  working controls, keyboard focus.
- **Browser surfaces** — text selection, caret, scrollbars, focus rings,
  underline offset, tabular numerals. These ship with browser defaults that
  belong to no design system. Theming them is the cheapest signal a page was
  built rather than assembled, and the thing models skip most reliably.
- **Copy** — controls name their action; errors name the problem *and* the
  recovery.

## 3. Refuse list

Category defaults, not absolute bans — a brief's own words can earn any of
them. Reaching for one when the axis is free means you were not deciding.

**Page scaffolds**
- Same-size cards of icon + heading + text as the page structure. Nested cards
  are always wrong.
- The hero-metric template: big number, small label, supporting stats, accent.
- A kicker or eyebrow above a heading. *This one is an absolute ban* — no brief
  earns it back.
- Section numbers (01 / 02 / 03) unless the sequence carries information.
- A modal for a task needing neither interruption nor protected focus.

**Surface habits**
- Gradient text. Emphasis comes from weight or size.
- Glass and blur as decoration rather than as a specific effect.
- A coloured `border-left`/`border-right` above 1px on cards, list items, alerts.
- Hard offset shadows (`4px 4px 0`) outside a genuinely neobrutalist world.
- Sparklines, progress rings and soft-shadowed rounded rectangles standing in
  for content.
- Monospace as a costume for "technical" rather than for code or data.
- A system display face (Impact, Arial Black, platform sans) as the display
  voice. The closest installed font is a failure, not a fallback.
- Unicode glyphs or emoji standing in for an icon system.
- Geometric masks approximating a photographic subject's edge.
- Light or dark picked by category rather than by use scene.
- 1px border under a wide soft shadow (the "ghost card"). Declare elevation
  once: border **or** shadow. Card radii 12–16px; pills for small controls.
- Sketch-style SVG scenes, `feTurbulence` grain, doodle illustration. Bans SVG
  imitating pictures, never SVG doing geometry.

## 4. The four modes

Chosen from the **surface**, not the product. A tool's landing page is still
Persuade; a fashion house's docs are still Read.

- **Persuade** — visitor decides and acts. Landing, marketing, pricing.
- **Operate** — visitor completes a task. Dashboards, admin, settings. Scanability
  and consistency outrank expression; brand lives in precise details.
- **Read** — visitor understands. Docs, articles, guides.
- **Experience** — visitor is inside the work. Portfolios, galleries.

## 5. The 23 commands

Available directly as `/impeccable <command> <target>` from the global install.

`init` `document` `extract` `shape` `craft` · `critique` `audit` · `polish`
`bolder` `quieter` `distill` `harden` `onboard` · `animate` `colorize`
`typeset` `layout` `delight` `overdrive` · `clarify` `adapt` `optimize` · `live`

Most useful here: `critique` (UX review), `audit` (a11y/perf/responsive),
`polish` (pre-ship pass), `typeset`, `layout`, `harden`.

## 6. Guidance we deliberately do not adopt

- **`init` / `PRODUCT.md` / `DESIGN.md` per project.** Our brand context is
  already authoritative in `branding-agent` and `~/.claude/design-sources/
  brand-overrides/`. Do not run `/impeccable init` on Bishop AI work; it will
  interview you for context we already hold.
- **"The brief wins" over brand.** Impeccable defers to a pinned brief. On
  Rich's work the brand lock outranks both.
- **Hooks that auto-run on every edit.** Not enabled globally; the gate runs at
  delivery, not on every keystroke.
