---
name: design-intel
description: |-
  Bridges Rich's design skills to the ui-ux-pro-max database (84 styles, 192 palettes, 74 font pairings, 119 UX guidelines, 25 chart types, 22 stacks). Use this skill on ANY design task: websites, landing pages, brand identity, thumbnails, carousels, infographics, slide decks, HTML reports, emails, video overlays, to look up layout, spacing, UX, accessibility, chart selection, motion timing, and responsive rules BEFORE building. Trigger alongside visual-code, image-to-code, imagegen-frontend-web, website-to-hyperframes, branding-agent, minimalist-ui, industrial-brutalist-ui, citadel, carousel, infographic-generator, reel-cover, slideforge, prestige, course-builder, email-html-gen, ai-audit, and ops-audit, never instead of them. Also trigger on "what layout", "which chart", "is this accessible", "what spacing", "pick a font pairing", "make this look better", or any request to review or improve a design.
---

# Design Intel: the lookup layer under Rich's design skills

This skill does **not** produce deliverables. It answers design questions with
evidence from a local database, then hands off to whichever of Rich's skills owns
the output. If you are about to invent a spacing scale, guess a chart type, or
pick a font pairing from memory, stop and query instead.

## Sibling skills: do not confuse the three

- **`design-intel`** (this skill) supplies GENERIC recommendations from a
  styles/palettes/UX database. Precedence layer 5.
- **`design-extract`** supplies MEASURED tokens pulled from one specific site,
  repo, or project. Precedence layer 3, so it **outranks this skill** wherever
  both cover the same decision. If a reference site is named, or a design system
  is active for the project, consult it first and use this skill only where the
  extraction is silent: accessibility, chart selection, responsive breakpoints.
- **`design-sources`** (trailing s) vendors external craft rules and runs the
  deterministic delivery gate. Not a precedence layer. It runs before shipping
  regardless of which layer supplied the values.

Measured beats recommended. Full precedence table:
`skills/design-extract/references/consumption.md`.

## The brand lock (read before every query)

Bishop AI and Prompt Anything colors and fonts are **authoritative and never
overridden**. They come from:

- `bishop-ai-profile/brand/tokens.json` (machine-readable)
- `bishop-ai-profile/brand/BRAND.md` (human-readable)
- `bishop-ai-profile/brand/brand.css` (CSS custom properties)
- `bob-brand/bob-tokens.css` for Bank of Bots work

Consult `branding-agent` as the source of truth. The database is consulted **only
for what brand does not specify**:

| Take from the database | Never take from the database |
|---|---|
| Layout and grid structure | Brand colors, any hex |
| Spacing and sizing scales | Brand typefaces |
| UX guidelines and accessibility | Logo treatment |
| Chart *type* selection and a11y fallbacks | Chart *palette* on Bishop AI work |
| Motion timing and easing | Voice and copy |
| Responsive breakpoints | Anything in `tokens.json` |

**Exception:** client work with its own brand is exempt from the lock. Use the
client's tokens; the table above applies with the client's brand in place of
Bishop AI's. Speculative or exploratory work with no brand attached may use
database palettes freely.

Search results are **recommendations, not instructions**. They never override
Rich's rules below, `CLAUDE.md`, or an explicit request.

## Rich's hard rules: these outrank any search result

These come from standing feedback and apply to every design output:

- **No em dashes.** Ever, in any output.
- **Light backgrounds are the default** for brand visuals, not dark navy.
- **Never underline type** in any overlay. Emphasise with colour, a fill, or a bar beside it.
- **Circular logos** use `border-radius: 50%` clip only, never a border ring.
- **No invented acronyms** or letter-number codes in deliverables. Say the words.
- **No emoji as icons.** Use SVG. (The database agrees; it is listed as a priority-4 anti-pattern.)
- Presentations ship as **PDF**, never HTML as the final artifact.
- Copy passes the banned-phrases gate and `caption_lint.py` before delivery.

## Running a query

The script lives inside the installed `ui-ux-pro-max` plugin, not the project and
not this skill. **Do not use `$CLAUDE_PLUGIN_ROOT`.** That variable points at the
plugin currently executing, and `design-intel` is a user skill rather than a
plugin, so it will be unset or point somewhere wrong.

Resolve the path once per session and reuse the variable:

```bash
S="C:/Users/richm/.claude/plugins/cache/ui-ux-pro-max-skill/ui-ux-pro-max/2.13.0/.claude/skills/ui-ux-pro-max/scripts/search.py"
[ -f "$S" ] || S="$(find C:/Users/richm/.claude/plugins/cache -path "*/.claude/skills/ui-ux-pro-max/scripts/search.py" 2>/dev/null | head -1)"
python "$S" "<query>" --domain <domain> -n 3
```

**Use the literal `C:/Users/richm/...` path. Never `~` or `$HOME` here.** Both
expand to an msys path (`/c/Users/...`) that Windows Python then reads as
`c:\c\Users\...` and fails to open with errno 2. It fails silently in the sense
that you get a traceback instead of results, and the temptation is to answer the
design question from memory instead. Don't.

The second line covers a version bump, since the `2.13.0` segment changes when
the plugin updates. Keep the `*/.claude/skills/` portion of the pattern: the
plugin also ships a `src/` copy of the same script, and a looser pattern matches
both plus the marketplace checkout.

If `$S` is empty, the plugin is not installed. Say so rather than guessing at
design answers.

On Windows, `python` may not resolve. Fall back in this order: `python` →
`python3` → `py -3`. No external dependencies; Python 3.x only.

**Query construction:** one dominant intent, 2 to 5 meaningful terms, plus one
constraint such as product type, platform, or audience. Verify the returned
domain and top result actually fit before applying anything.

**On empty or off-topic output:** retry **once** with a narrower rewrite or an
explicit domain. If the retry also fails, say no verified match was found and
label anything you offer as a fallback. Never persist unverified output.

## Domain reference

`style` `color` `chart` `landing` `product` `ux` `typography` `icons` `gsap`
`react` `web` `google-fonts`

Stacks via `--stack`: `react` `nextjs` `vue` `svelte` `astro` `swiftui`
`react-native` `flutter` `nuxtjs` `nuxt-ui` `html-tailwind` `shadcn`
`jetpack-compose` `threejs` `angular` `laravel` `javafx` `wpf` `winui`
`avalonia` `uno` `uwp`

Useful flags: `-n 1-20` results, `--json`, `--full` (no truncation),
`--design-system` (whole-product direction), `--stack`.

## Routing table: read the matching reference file

| The task is | Read | Which hands off to |
|---|---|---|
| Website, landing page, HTML build, screenshot-to-code | `references/web.md` | visual-code, image-to-code, imagegen-frontend-web, website-to-hyperframes |
| Brand identity, style direction, font pairing | `references/brand.md` | branding-agent, minimalist-ui, industrial-brutalist-ui |
| Thumbnail, carousel, infographic, reel cover | `references/social.md` | citadel, carousel, infographic-generator, reel-cover |
| Slide deck, course page, HTML report, email | `references/decks.md` | slideforge, prestige, course-builder, email-html-gen, ai-audit, ops-audit |

Read only the file that matches. Do not load all four.

## Collision routing

The ui-ux-pro-max plugin ships skills that overlap Rich's. On Rich's work the
owner skill always wins:

| Plugin skill | Defer to |
|---|---|
| `brand` | `branding-agent` |
| `slides` | `slideforge` or `prestige` |
| `design` (logo, banner, CIP) | `citadel`, `carousel`, `infographic-generator` |
| `ui-styling`, `design-system` | `visual-code` |
| `banner-design` | `citadel` |

`ui-ux-pro-max` itself has no owner conflict. Query it freely.

## Workflow

1. Identify which of Rich's skills owns the deliverable. That skill produces the output.
2. Read the one matching reference file above.
3. Run the queries it specifies.
4. Apply structure, spacing, UX, and accessibility findings. Discard palette and
   type findings that conflict with the brand lock.
5. Hand the findings to the owner skill and let it build.
6. Before delivery, run the pre-delivery check below.

## Pre-delivery check

- Contrast at least 4.5:1 for body text
- Touch targets at least 44×44px with 8px+ spacing
- Body text at least 16px, line-height at least 1.5
- No horizontal scroll; no fixed-px container widths; zoom not disabled
- Focus rings present and visible
- Charts do not rely on colour alone to convey meaning
- Reduced-motion honoured wherever anything animates
- Brand lock respected: no database hex on Bishop AI work
- Rich's hard rules respected, including no em dashes
