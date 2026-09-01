# AIOS: the operating system this folder runs

`~/.claude` is not a pile of skills. It is an operating system for the work, and
this file is its map. `CLAUDE.md` holds the standing rules; this file holds the
structure those rules govern.

An **AIOS layer** is a group of skills that share one job, one authority, and one
delivery standard. A layer answers three questions: what does it decide, who
wins when it disagrees with something else, and how do we know its output is
good enough to ship.

---

## The design layer

The first layer formalised. Three support skills plus one plugin. **None of them
produce deliverables.** The owner skill (`visual-code`, `slideforge`, `citadel`,
`ai-audit`, and the rest) always builds the thing.

| Component | Job | Runs |
|---|---|---|
| `design-extract` | Measured tokens from one specific site, repo, or project (SkillUI) | before, when a reference is named |
| `design-intel` | Generic recommendations from the ui-ux-pro-max database | before, always |
| `design-sources` | The deterministic delivery gate (Impeccable) | after, before shipping |
| `ui-ux-pro-max` (plugin) | The database itself: 84 styles, 192 palettes, 74 pairings, 119 UX rules, 25 charts, 22 stacks | queried by `design-intel` |

### Authority

1. Explicit instruction in the request
2. `branding-agent` for colours, fonts, logo on Bishop AI and Prompt Anything work
3. Active extracted design system for layout, spacing, type scale, components, motion
4. Style preset (`minimalist-skill`, `brutalist-skill`) for aesthetic character
5. `design-intel` where 2 to 4 are silent
6. Skill defaults

Measured beats recommended. Borrow ratios and structure from an extracted system;
keep brand colours, typefaces and logo from `branding-agent`. Only the literal
phrase "full \<name\> system" promotes an extracted system above brand, and only
for one deliverable.

`design-sources` is a gate, not a layer in that list. It runs regardless of which
level supplied the values.

### Delivery standard

Any HTML artifact runs the gate before it ships:

```bash
python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file> --mobile
```

Exit 0 ships. Exit 2 has findings. Exit 1 is a setup problem. **Never self-assess
a page as clean**, and gate the HTML *before* the PDF or screenshot step, because
a defect baked into a PDF costs far more to find.

Brand conflicts get a scoped, reasoned entry in
`design-sources/brand-overrides/config.json`, never a blanket ignore. Bishop AI
fails `cream-palette` and `overused-font` out of the box by design; those waivers
already exist and print as "overridden by brand".

### Known traps

- The gate's detector runs on jsdom, which **does not resolve `clamp()`**. Clamped
  headings are invisible to `flat-type-hierarchy`, so a page can look
  hierarchical and still fail the 2.0 min/max ratio. Use explicit px with a media
  query where the gate has to see the scale.
- **Never write `~` or `$HOME` in a documented command.** Git Bash expands both to
  `/c/Users/...`, which Windows Python reads as `c:\c\Users\...` and cannot open.
  Use the literal `C:/Users/richm/...` form.
- Bishop contrast on warm-white `#F9F6F0`, measured: deep-black 18.63:1 and
  dark-charcoal 14.49:1 pass. **Gold `#E0B848` is 1.75:1 and blue `#1894C9` is
  3.18:1**, so gold is never text and blue is large-text or non-text only. White
  on gold is 1.89:1 and white on blue is 3.43:1, so neither carries a button
  label. Buttons take dark-charcoal.

---

## Layers not yet formalised

These clusters exist and work, but have no written authority or delivery standard
yet. Each is a candidate for the same treatment.

| Cluster | Skills | Has a gate? |
|---|---|---|
| Video and motion | `reelforge`, `vistage`, `hyperframes`, `video-use`, `reel-cover` | partial: `verify_render.py`, `caption_lint.py` |
| Content and copy | `scriptforge`, `hookcraft`, `captioncraft`, `humanizer`, `richmond-ai-content` | partial: banned-phrases, `caption_lint.py` |
| Research and leads | `bishop-research-agent`, `intent-lead-research`, `agent-reach`, `signal-trace` | no |
| Client delivery | `ops-audit`, `ai-audit`, `lead-audit-walkthrough`, `pitch-deck-architect` | inherits the design gate |
| Money | `invoice-generator`, `receipt-filer`, `expense-classifier`, `receipt-gaap` | no |

The content cluster is the closest to ready: the banned-phrases list and
`caption_lint.py` are already the gate, they are simply not written up as one.

---

## Adding a layer

1. Name the skills that share the job.
2. Write the authority order, including what beats what and the escape hatch.
3. Name the delivery standard and make it deterministic. A gate somebody can
   argue with is not a gate.
4. Add the routing to `CLAUDE.md` so a fresh session picks it up without being told.
5. Add a row to this file.

The design layer is the worked example. Copy its shape.
