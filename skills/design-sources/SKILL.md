---
name: design-sources
description: |-
  Applies external design-craft rules from vendored GitHub repos (currently Impeccable) to Rich's design work, and runs the deterministic design gate before delivery. Use on ANY task that produces visual output: websites, landing pages, HTML reports and audits, slide decks, course pages, emails, brand graphics, thumbnails, carousels, infographics, video overlays. Trigger alongside visual-code, image-to-code, imagegen-frontend-web, minimalist-ui, industrial-brutalist-ui, branding-agent, citadel, carousel, infographic-generator, email-html-gen, slideforge, prestige, course-builder, ai-audit, ops-audit, lead-audit-walkthrough, reelforge and hyperframes, never instead of them. Also trigger on "run the design gate", "check this design", "is this AI slop", "polish this page", "audit this HTML", "make this look less AI-generated", or before delivering any HTML file.
---

# Design Sources: external craft rules + the design gate

This skill does **not** produce deliverables. It supplies craft rules from
vendored GitHub repos and runs the deterministic gate that HTML output must pass
before it ships. The owner skill still builds the thing.

Sibling skills, both of which run *before* this one:

- **`design-extract`** supplies MEASURED tokens from one specific site, repo or
  project. Precedence layer 3.
- **`design-intel`** supplies GENERIC recommendations (layout, spacing, chart
  choice, font pairings) from a local database. Precedence layer 5.

This skill enforces *how well it was built* and is **not a precedence layer at
all**: the gate runs before shipping regardless of which layer supplied the
values. On a real design task the order is `design-extract` and `design-intel`
before, `design-sources` after.

## Registry

`~/.claude/design-sources/sources.json` is the manifest. Each source has a
checkout, a hand-written digest, and a note on which clusters it applies to.

| Source | Version | Digest | Gate |
|---|---|---|---|
| impeccable (`pbakaus/impeccable`, Apache-2.0) | 3.6.1 | `design-sources/digests/impeccable.md` | yes, `impeccable detect` |

**Read the digest, not the checkout.** The digest carries the craft floor, the
refuse list, the 47 rule IDs, and what we deliberately do not adopt. Open
`~/.claude/design-sources/impeccable/` only for depth the digest lacks.

### Managing sources

```bash
S=C:/Users/richm/.claude/skills/design-sources/scripts
python $S/sync.py list
python $S/sync.py update            # git pull + re-prune all
python $S/sync.py add <name> <url>  # clone, prune, register
```

After `add`, read the checkout and write `digests/<name>.md` by hand, then add a
row to the table above. Auto-generating a digest would just be the README with
extra steps.

## The brand lock: this outranks every external source

External design rules are **advice**. Rich's brand is **law**. When they
conflict, brand wins and the external rule is overridden, never the reverse.

Authoritative brand sources, in order:

1. `branding-agent` skill (Bishop AI + Prompt Anything)
2. `bishop-ai-profile/brand/tokens.json`, `brand.css`, `BRAND.md`
3. `bob-brand/bob-tokens.css` + `BOB-BRAND-GUIDELINES.md` for Bank of Bots
4. `~/.claude/design-sources/brand-overrides/config.json`: the machine-readable
   waivers the gate applies

This is not theoretical. **Verified against the live detector:** Bishop AI's own
brand fails two Impeccable rules out of the box: `cream-palette` on warm-white
`#F9F6F0` (which `tokens.json` defines as the default background for all
light-mode content) and `overused-font` on Open Sans (the locked body face).
Without the overrides, every Bishop AI light-mode deliverable would fail the
gate. The overrides file exists for exactly this, and each entry records what
was verified.

Client work with its own brand is exempt: the client's tokens take the place of
Bishop AI's, and the same precedence applies.

## Rich's hard rules: never waived by any source

- **No em dashes**, anywhere. Impeccable files `em-dash-overuse` as advisory;
  the gate re-promotes it to blocking.
- **Light backgrounds are the default** for brand visuals.
- **Never underline type** in an overlay. Use colour, a fill, or a bar beside it.
- **Circular logos** use `border-radius: 50%` clip only, never a border ring.
- **No invented acronyms** or letter-number codes.
- **No emoji as icons.** Drawn SVG only. (Impeccable agrees.)
- Presentations ship as **PDF**, never HTML as the final artifact.
- Copy passes banned-phrases and `caption_lint.py` before delivery.

## The gate

Run before delivering **any** HTML artifact.

```bash
python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file|dir|url>
python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py report.html --mobile
```

Exit `0` = clean, safe to deliver. Exit `2` = real findings, fix them. Exit `1` =
setup problem.

The wrapper exists rather than calling `impeccable detect` directly because it:

1. **Refuses to pass a DEGRADED run.** Without its HTML parser deps the detector
   silently undercounts (verified: 1 finding vs 4) and never computes contrast.
   A degraded pass is not a clean bill of health.
2. **Applies the brand overrides** (and resolves them from the right CWD, the
   CLI reads `.impeccable/` from the process working directory, not from the
   target's folder).
3. **Prints what the overrides suppressed** under "overridden by brand". The
   `cream-palette` waiver has to be rule-wide because that rule emits no
   ignoreValue, so a genuinely lazy beige background is still surfaced for a
   human to judge rather than silently dropped.
4. **Re-promotes em-dash findings** to blocking.

**The gate is the standard, not my judgement.** Never self-assess a page as
clean. Run it, get exit 0, and only then deliver. If a finding is a real locked
brand conflict, add a *scoped, reasoned* entry to `brand-overrides/config.json`,
never a blanket `ignoreRules` line without justification.

## Routing: read the one adapter that matches

| The task produces | Read | Gate applies |
|---|---|---|
| Website, landing page, HTML build, screenshot-to-code | `references/web-ui.md` | full, blocking |
| HTML report, audit, slide deck, course page, email | `references/deck-doc.md` | full, blocking |
| Thumbnail, carousel, infographic, brand graphic, generated image | `references/brand-graphics.md` | guidance only (no HTML to scan) |
| Video overlay, reel card, motion graphic | `references/video-motion.md` | type-craft guidance only |

Read only the matching file. Do not load all four.

## Workflow

1. Identify the skill that owns the deliverable. It builds the output.
2. Read `digests/impeccable.md` for the craft floor and refuse list.
3. Read the one adapter above that matches the medium.
4. Build, honouring the brand lock wherever it conflicts with external advice.
5. If the output is HTML, run the gate to exit 0.
6. Deliver, and say the gate passed.

## The 23 Impeccable commands

Both halves are installed, so `/impeccable <command> <target>` works directly for
interactive work: `critique`, `audit`, `polish`, `typeset`, `layout`, `harden`,
`animate`, `bolder`, `quieter`, `distill`, and more. Full list in the digest.

- CLI: `npm install -g impeccable` (v3.6.0, which is npm `latest`) provides
  `impeccable detect` for the gate, with the HTML parser deps that keep it out
  of degraded mode. The checkout's git HEAD reads 3.6.1; that version is
  unreleased, so the CLI being 3.6.0 is correct and not drift.
- Skill: `~/.claude/skills/impeccable/`, copied from the vendored checkout's
  prebuilt universal build. `impeccable install` could not be used because its
  download is corrupted by local Avast cert injection ("invalid zip data"); the
  checkout copy is the same artifact. Its `allowed-tools` script path was
  rewritten to the installed location.
- To refresh it after `sync.py update`, re-copy
  `design-sources/impeccable/.agent/skills/impeccable/` and redo that one path
  rewrite.

Do **not** run `/impeccable init` on Bishop AI work: it interviews you to build
`PRODUCT.md`/`DESIGN.md` context that `branding-agent` already holds
authoritatively.
