# Design Source — Consumption Contract

The rule in one line: **extracted design systems are reference; Bishop AI brand is authority.**

## Precedence

| Layer | Source | Wins on |
|---|---|---|
| 1 (highest) | Explicit instruction in the request | everything |
| 2 | `branding-agent` | colors, fonts, logo treatment on any Bishop AI or Prompt Anything deliverable |
| 3 | Active design system | layout, spacing, type scale, components, motion, interactions |
| 4 | Style preset (`brutalist-skill`, `minimalist-skill`) | aesthetic character where 2 and 3 are silent |
| 5 | `design-intel` | generic layout, spacing, UX, accessibility, and font-pairing recommendations where 2-4 are silent |
| 6 (lowest) | Skill defaults | everything else |

Separately, `design-sources` is a **gate, not a layer**. It vendors external design-craft
repos and runs a deterministic check before delivery. It applies no matter which layer
supplied the values, so it has no row in this table — run it before shipping, as it asks.

`design-intel` and `design-extract` are siblings, not rivals. `design-extract` supplies
**measured** values from one specific site; `design-intel` supplies **recommended**
values from a general database. Measured beats recommended on any decision both cover.
Where the extraction is silent — accessibility rules, chart selection, responsive
breakpoints — `design-intel` is the answer and should be consulted normally.

## The one escape hatch

The phrase **"full \<name\> system"** promotes the active system above `branding-agent`
for that single deliverable. Nothing else does. Not "use Linear's colors", not "make it
look like Linear", not "match Linear's branding" — only the literal phrase
"full linear system".

If a request seems to want brand override but does not use that phrase, follow the
precedence table and say in one line which colors and fonts you used and why.

## Borrow / keep

**BORROW from the active system:** layout, spacing grid, type scale ratios,
component patterns, motion, easing, interaction states.

**KEEP from `branding-agent`:** Bishop AI / Prompt Anything colors, font families,
logo treatment.

Type scale is a ratio, not a font. Borrowing Linear's 1.25 scale while keeping the Bishop
typeface is the intended outcome, not a compromise.

## Resolving the active system

1. A system named in the request — match against `slug` or `name` in each
   `~/.claude/design-systems/*/manifest.json`.
2. Otherwise, a `.design-system` marker file in the working folder. Format:
   `<slug>  # activated YYYY-MM-DD`. Read the first token before any `#`.
3. Otherwise, none is active — proceed exactly as the skill would have before.

A named system beats the marker for that request and does not overwrite it.

## What to read, by medium

| Group | Read |
|---|---|
| Web/code | `tokens/colors.json`, `tokens/typography.json`, `tokens/spacing.json`, `fonts/` — drop values in directly, do not round or reinterpret |
| Brand/graphics | `screens/` and `references/VISUAL_GUIDE.md` — describe the visual language in image prompts; `tokens/` for palette bounds |
| Style presets | `references/LAYOUT.md` and `references/COMPONENTS.md` — the extracted system supplies structure (layout, grid, spacing, components); the preset supplies aesthetic character where the extracted system is silent |
| Motion/diagram | `references/ANIMATIONS.md` and `references/INTERACTIONS.md` — real keyframes, durations, and easing curves |

Refer to `DESIGN.md` for full orientation. Use token values exactly as written. Do not round them, re-derive them, or substitute a "close enough" value. The entire point is that these are measured rather than guessed.

## When sources disagree

`tokens/*.json` wins. The JSON is the schema'd machine extraction (W3C
design-tokens format, explicit `role` and `name` per value); `DESIGN.md` and
the generated `SKILL.md` are human-readable renderings of the same crawl and
can drift from it. Prefer the JSON for any value going into code.

This is observed, not hypothetical. In `~/.claude/design-systems/linear/`,
`tokens/colors.json` gives accent `#828fff` and text-muted `#b4bcd0`, while
the prose in `SKILL.md`/`DESIGN.md` says accent `#7170ff` and Text Muted
`#8b93a1`. Use the JSON values.

When you notice the two disagreeing on a value you're using, say so in one
line in your output rather than silently picking one.

This tiebreak only applies where `tokens/` exists. Default-mode extractions
have no `tokens/` directory at all, so `DESIGN.md` is the only source. Check
`manifest.json`'s `has.tokens` first.

## When files are absent

`manifest.json` carries a `has` map (`tokens`, `screens`, `animations`, `interactions`,
`layout`, `components`). Check it before relying on a file. Default-mode extractions have
no screenshots, animations, or interaction diffs.

If a system is named but not registered, say so and list what is available. Do not fall
back to invented values silently.
