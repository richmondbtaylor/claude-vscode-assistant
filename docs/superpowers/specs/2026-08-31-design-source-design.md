# design-source — Design System Extraction Layer

**Date:** 2026-08-31
**Status:** Approved design, not yet implemented
**Owner:** Rich Taylor

## Problem

Every design skill in `~/.claude/skills/` invents its own colors, type scale, spacing,
and motion when the deliverable is not Bishop AI branded. There is no way to say
"build this the way Linear builds things" and have the skill work from that site's
real tokens rather than a guess at them.

[SkillUI](https://github.com/amaancoderx/npxskillui) (`npm: skillui`, v1.3.4, MIT)
solves the extraction half: it crawls a URL, git repo, or local directory using pure
static analysis and emits a folder of design-system facts. It does not solve the
distribution half — getting those facts in front of the nineteen design skills that
should be using them.

This spec covers a single new skill that owns extraction and storage, plus a uniform
connector appended to each design skill that teaches it to read from that store.

## Goals

1. One command turns any site into a stored, reusable design system.
2. Every design skill checks that store before choosing colors, type, spacing, or motion.
3. Bishop AI brand integrity is never at risk from an extracted system.
4. Adding a twentieth design skill later costs one appended block, not a new skill.

## Non-Goals

- Ingesting non-SkillUI sources (other GitHub design repos, third-party `.skill`
  packages, Figma exports). The library format is deliberately simple enough to
  accept those later, but no adapter is built now.
- Replacing or superseding any existing design skill.
- Editing the aesthetic content of any existing skill. The connector is additive only.

## Background: what SkillUI produces

Verified against the repo README and file tree on 2026-08-31.

**CLI surface:**

```
skillui --url <url>            crawl a live website
skillui --dir <path>           scan a local project directory
skillui --repo <url>           clone and scan a git repository

--mode ultra                   cinematic extraction (requires Playwright)
--screens <n>                  pages to crawl in ultra mode (default 5, max 20)
--out <path>                   output directory (default ./)
--name <string>                override the project name
--format design-md|skill|both  output format (default both)
--no-skill                     DESIGN.md only, skip .skill packaging
```

**Output folder:**

```
<name>-design/
  <name>-design.skill        packaged ZIP of everything
  SKILL.md                   master skill file
  CLAUDE.md                  project context
  DESIGN.md                  full design system tokens
  references/
    ANIMATIONS.md            motion specs and keyframes        (ultra)
    LAYOUT.md                layout containers and grid        (ultra)
    COMPONENTS.md            DOM component patterns            (ultra)
    INTERACTIONS.md          hover/focus state diffs           (ultra)
    VISUAL_GUIDE.md          all screenshots in sequence
  screens/
    scroll/                  7 scroll journey screenshots      (ultra)
    pages/                   full-page screenshots             (ultra)
    sections/                section clips                     (ultra)
  tokens/
    colors.json
    spacing.json
    typography.json
  fonts/                     bundled Google Fonts (woff2)
```

Default mode yields tokens, typography, spacing, and fonts. Ultra mode adds every
row marked `(ultra)` above. Ultra is the default for this skill because the motion
and graphics skills depend on `ANIMATIONS.md`, `INTERACTIONS.md`, and `screens/`.

**Environment (verified 2026-08-31):** Node v22.18.0, npm 10.9.3, Playwright present
(used elsewhere in this repo). `skillui` is not installed globally and will be invoked
via `npx -y skillui@latest`.

## Architecture

Two pieces: an extractor skill that writes, and a connector block that reads.

```
                    npx -y skillui --url X --mode ultra
                                  |
                                  v
        ~/.claude/skills/design-source/  (owns extraction + registration)
                                  |
                                  v
        ~/.claude/design-systems/<slug>/  (the library — one folder per system)
                                  |
        +-------------------------+-------------------------+
        |             |                       |             |
     tokens/       screens/            references/       DESIGN.md
        |             |                       |             |
        v             v                       v             v
   web/code      brand/graphics         motion/diagram   all skills
    skills          skills                  skills
```

### Component 1: the `design-source` skill

```
~/.claude/skills/design-source/
  SKILL.md
  scripts/
    extract.py          run skillui, land output in the library, write manifest
    activate.py         write/read/clear the .design-system marker
    library.py          shared: slug rules, library path, manifest read/write
  references/
    consumption.md      THE CONTRACT — borrow/keep rules, per-medium file map
    library.md          human-readable index of registered systems
```

**Triggering.** The `description` frontmatter fires on: "extract the design system
from X", "pull in <site>'s design", "use the <name> system", "build this like
<site>", "list design systems", "what design systems do I have", "skillui",
"activate the <name> system".

**Python conventions.** Per the global CLAUDE.md rule, every script carries a
PEP 723 header and runs via `uv run`. No bare `pip`, no manual venv.

### Component 2: the library

```
~/.claude/design-systems/
  README.md                      what this folder is, how to add to it
  <slug>/
    manifest.json
    DESIGN.md  CLAUDE.md  SKILL.md
    tokens/  references/  screens/  fonts/
    <slug>.skill
```

Slug rules: lowercase, hyphen-separated, derived from `--name` if given, otherwise
from the registrable domain (`https://linear.app` -> `linear`,
`https://www.nothing.tech` -> `nothing-tech`). Collisions are resolved by prompting
before overwrite; an existing slug is never silently replaced.

`manifest.json`:

```json
{
  "slug": "linear",
  "name": "Linear",
  "source": "https://linear.app",
  "source_type": "url",
  "mode": "ultra",
  "extracted": "2026-08-31",
  "skillui_version": "1.3.4",
  "screens": 10,
  "has": {
    "tokens": true, "screens": true, "animations": true,
    "interactions": true, "layout": true, "components": true
  },
  "palette": ["#5E6AD2", "#0D0E10", "#F7F8F8"],
  "fonts": ["Inter Variable", "SF Mono"]
}
```

`palette` and `fonts` are summary fields lifted from `tokens/` so the index and the
connector can describe a system without reading the whole folder.

### Component 3: the connector block

Appended verbatim to the end of each wired `SKILL.md`. Identical across all skills so
it can be regenerated or removed mechanically.

```markdown
## Design Source

Before choosing colors, type, spacing, or motion, check for an active design system:

1. A system named in the request ("in the linear system", "build this like Stripe"),
   or a `.design-system` marker file in the working folder.
2. If found, read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`.
3. **BORROW** from it: layout, spacing grid, type scale ratios, component patterns,
   motion, easing, interaction states.
   **KEEP** from `branding-agent`: Bishop AI / Prompt Anything colors, font families,
   logo treatment.
   Override only when the request explicitly says "full <name> system".
4. Nothing active -> proceed exactly as normal. This block adds no default behavior.

Full contract: `~/.claude/skills/design-source/references/consumption.md`
```

Plus **one** medium-specific line per group, appended directly beneath:

| Group | Extra line points at |
|---|---|
| Web/code | `tokens/colors.json`, `tokens/typography.json`, `tokens/spacing.json`, `fonts/` — drop values in directly, do not round or reinterpret |
| Brand/graphics | `screens/` and `references/VISUAL_GUIDE.md` — describe the visual language in image prompts; `tokens/` for palette bounds |
| Style presets | `references/LAYOUT.md` and `references/COMPONENTS.md` — the extracted system supplies structure (layout, grid, spacing, components); the preset supplies aesthetic character where the extracted system is silent |
| Motion/diagram | `references/ANIMATIONS.md` and `references/INTERACTIONS.md` — real keyframes, durations, and easing curves |

### Component 4: precedence

The rule, in one line: **extracted systems are reference; Bishop AI brand is authority.**

| Layer | Source | Wins on |
|---|---|---|
| 1 (highest) | Explicit instruction in the request | everything |
| 2 | `branding-agent` | colors, fonts, logo — on any Bishop AI or Prompt Anything deliverable |
| 3 | Active design system | layout, spacing, type scale, components, motion, interactions |
| 4 | Style preset skill (brutalist/minimalist) | aesthetic character where 2 and 3 are silent |
| 5 | `design-intel` | generic layout, spacing, UX, accessibility, font-pairing recommendations where 2-4 are silent |
| 6 (lowest) | Skill defaults | everything else |

> **Amendment, 2026-08-31 (post-approval, approved by Rich during planning).** Layer 5
> did not exist when this spec was first approved. A skill named `design-intel` — which
> bridges the same design skills to a generic recommendation database — surfaced during
> planning. Measured beats recommended, so it sits below an active design system and
> below the style presets, and fills in whatever the extraction was silent on
> (accessibility rules, chart selection, responsive breakpoints).
>
> Separately, a pre-existing skill named **`design-sources`** (trailing *s*) vendors
> external design-craft repos and runs a delivery gate. It is a **gate, not a layer**: it
> applies regardless of which layer supplied the values, so it gets no row here.
>
> The skill built by this spec was also renamed **`design-source` -> `design-extract`**
> to avoid a one-letter collision with `design-sources`. All paths are
> `~/.claude/skills/design-extract/`.

The single escape hatch is the phrase **"full <name> system"**, which promotes the
active system above `branding-agent` for that one deliverable. Nothing else does.

`branding-agent` receives an **inverted** block rather than the standard one. It does
not defer to the library; it states that it is layer 2 and that extracted systems sit
beneath it. This is what makes "brand always wins" hold in practice — the authority
skill has to know it is the authority, or the two blocks contradict each other.

### Component 5: activation

Named per request, sticky per project.

- **Named:** any request mentioning a registered system's name or slug activates it
  for that request. Fuzzy match against `manifest.json` `name` and `slug`.
- **Sticky:** `activate.py` writes a `.design-system` file into the working project
  folder containing the slug and the date. Subsequent design work in that folder
  picks it up without re-naming. `activate.py --clear` removes it.
- **Precedence between the two:** a system named in the request beats the marker for
  that request, and does not overwrite the marker.

`.design-system` is a one-line text file, not JSON, so it is trivially greppable and
obvious in a diff:

```
linear  # activated 2026-08-31
```

## Skills wired (19)

| Group | Skills |
|---|---|
| Web/code (6) | `visual-code`, `image-to-code-skill`, `imagegen-frontend-web`, `email-html-gen`, `course-builder`, `codecraft` |
| Brand/graphics (6) | `branding-agent` (inverted), `citadel`, `carousel`, `infographic-generator`, `slideforge`, `presentation-impact-enhancer` |
| Style presets (2) | `brutalist-skill`, `minimalist-skill` |
| Motion/diagram (5) | `hyperframes`, `claude-design-hyperframes`, `gsap`, `excalidraw-skill`, `reelforge` |

All nineteen `SKILL.md` files were confirmed present on 2026-08-31.

**Edit discipline.** The block is appended at end of file. No existing line is
modified, no frontmatter is touched, no `description` is rewritten. Several of these
files carry a UTF-8 BOM and several exceed 1,000 lines; appending avoids both hazards.
A skill's triggering behavior must not change as a result of this work.

## Data flow

**Extraction:**

1. Rich: "extract the design system from linear.app"
2. `design-source` resolves slug `linear`, checks for a collision in the library.
3. Runs `npx -y skillui@latest --url https://linear.app --mode ultra --screens 10
   --name Linear --out <temp>`.
4. On Playwright failure, retries once without `--mode ultra` and records
   `"mode": "default"` in the manifest.
5. `extract.py` moves the output into `~/.claude/design-systems/linear/`, writes
   `manifest.json`, appends a line to `references/library.md`.
6. Reports: slug, mode actually used, palette, fonts, what is and is not present.

**Consumption:**

1. Rich: "build a landing page in the linear system"
2. `visual-code` triggers, reads its Design Source block.
3. Resolves `linear`, reads `DESIGN.md` + `tokens/`.
4. Builds using Linear's layout, spacing, type scale, and motion; uses Bishop AI
   colors and fonts unless the request said "full linear system".

## Error handling

| Condition | Behavior |
|---|---|
| Named system not in library | List what is available. Do not silently fall back to defaults. Offer to extract it. |
| Playwright unavailable / ultra fails | Retry once in default mode, record it in the manifest, and say plainly which mode ran. Never report ultra output that was not produced. |
| `skillui` run fails entirely | Report the actual stderr. Leave the library untouched. No partial slot. |
| Slug collision | Prompt before overwriting. Never silently replace an existing system. |
| Extraction yields no usable tokens | Refuse to register. A slot with no tokens is worse than no slot, because the connector will read it and find nothing. |
| Marker names a deleted system | Warn, ignore the marker, proceed as if none were active. |

## Testing

No part of this is reported working until observed working.

1. **Extraction** — run against `linear.app` in ultra mode. Verify the library slot
   exists, `manifest.json` is populated, `tokens/colors.json` holds real values, and
   `screens/scroll/` is non-empty.
2. **Degradation** — force ultra to fail. Verify default mode runs, the manifest says
   `"mode": "default"`, and the report says so out loud.
3. **Consumption** — run `visual-code` against the extracted system. Read the emitted
   HTML and confirm the color and font values trace back to `tokens/`, not to
   invented ones.
4. **Precedence** — run a Bishop AI deliverable with `linear` active. Confirm Bishop
   colors and fonts survive and Linear's layout comes through. Then run the same
   request with "full linear system" and confirm the override takes.
5. **Non-regression** — run one wired skill with no system active. Confirm output is
   unchanged from its pre-edit behavior.
6. **Stickiness** — activate in a folder, make a second request without naming the
   system, confirm it is still applied. Clear it, confirm it stops.

## Risks

- **`skillui` is young.** Published 2026-04-08, latest 1.3.4 on 2026-05-08, single
  maintainer. `npx -y` executes unvetted code from npm. Acceptable for a local design
  tool operating on public websites; worth knowing. `extract.py` records the resolved
  version in `manifest.json` so a bad release is traceable after the fact.
- **Nineteen skill edits.** Any change to a `SKILL.md` risks perturbing triggering.
  Mitigated by append-only edits and the non-regression test.
- **Blocks drifting out of sync.** Nineteen copies of one paragraph will diverge if
  edited by hand. Mitigated by keeping the real contract in `consumption.md` and the
  block short enough to regenerate mechanically.
- **Extracted systems bleeding into client work.** This is the failure mode the
  precedence table exists to prevent. The "full <name> system" phrase is the only
  path to it, and it is deliberately awkward to say by accident.

## Open items

None. All decisions resolved during brainstorming on 2026-08-31.
