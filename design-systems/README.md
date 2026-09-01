# Design Systems Library

Extracted design systems, one folder per system. Written by
`~/.claude/skills/design-extract/scripts/extract.py`, read by every design skill
carrying a "Design Source" block.

## Layout

```
<slug>/
  manifest.json    slug, name, source, mode, date, palette, fonts, has-map
  DESIGN.md        full token reference
  tokens/          colors.json, spacing.json, typography.json
  references/      ANIMATIONS, LAYOUT, COMPONENTS, INTERACTIONS, VISUAL_GUIDE
  screens/         scroll/, pages/, sections/   (ultra mode only)
  fonts/           bundled woff2
```

## Adding one

```bash
uv run ~/.claude/skills/design-extract/scripts/extract.py --url https://linear.app
```

## Rules

- A folder without a `manifest.json` is invisible to the library and is ignored.
- Extractions with no usable color tokens are refused rather than registered.
- Nothing here overrides Bishop AI brand. See
  `~/.claude/skills/design-extract/references/consumption.md`.
