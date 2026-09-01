# Claude Code Global Rules

## Receipt Filing (Claude Code)

When the user shares a receipt image (any format), do the following — no need to ask:

1. **Read the image** using vision to extract: date (YYYY-MM-DD), vendor name, amount (numeric, no $), payment method
2. **Determine the tab**: `Bishop AI` for business expenses, `Prompt Anything` if clearly that brand, `Personal` for non-business
3. **Run the filer script**:
```
python C:\Users\richm\.claude\scripts\file_receipt.py "<image_path>" "<date>" "<vendor>" "<amount>" "<tab>" "<payment_method>"
```
4. Report the confirmation back to the user

The script handles Drive upload + Sheet logging automatically.
If the image was shared as a file attachment in Claude Code, it will be at a temp path — use that path directly.

## Web Access Fallback

When WebFetch fails to access a URL (due to authentication, JavaScript rendering, redirects, or any other reason), automatically fall back to Playwright to fetch the content instead. Write and run a temporary Python Playwright script to load the page, wait for content to render, and extract the needed data. Do not ask permission — just use Playwright as the fallback.

Playwright is available via `python -m playwright`. Write a temp async script: launch chromium, goto url, wait networkidle, return page content.

## Python: use uv, never bare pip or venv

`uv` is the Python package manager for this system (`C:\Users\richm\.local\bin\uv.exe`, on PATH). Full recipes: `references/uv.md`.

- **Throwaway or utility scripts:** declare deps in a PEP 723 header and run `uv run script.py`. Never `pip install` a package just to run a one-off script.
- **CLI tools:** `uvx <tool>` to run without installing, `uv tool install <tool>` to keep it.
- **Projects:** `uv init` / `uv add` / `uv run`. Never activate a venv manually; `uv run` syncs first so the lock file and the running code cannot drift.
- **Never** run `pip install`, `python -m venv`, or `python -m pip` directly. If pip semantics are genuinely needed, use `uv pip ...`.
- Environments live in the global uv cache, not in `.claude`, which keeps the folder fast to browse.

Existing bots on `requirements.txt` + global Python still work. Migrate one only when already touching it, per the recipe in `references/uv.md`.

## Memory Enhancements

These rules override the auto-memory instructions where they conflict.

- **Project subtypes:** Label memories as `**Subtype:** experience` (facts/events/decisions) or `**Subtype:** mental-model` (patterns/strategies). Mental-models should be kept current; experiences can stale out.
- **Tag recalls:** Before acting on a recalled memory, classify it internally as `fresh` (verified), `assumed` (unverified -- check before acting), or `stale` (contradicted -- update/delete it first).
- **Reflect:** When 3+ experiences point at the same pattern, write a mental-model memory synthesizing them.

## Design skill routing

System map: `AIOS.md` at the root of this folder describes the layers this setup
runs and how to add one. Read it when the question is structural rather than
about a single skill.

Three support skills sit under my design work. None of them produce deliverables;
the owner skill (visual-code, slideforge, citadel, ai-audit, etc.) always builds.

| Skill | Answers | When |
|---|---|---|
| `design-extract` | what a *specific site* measures at | before building, when a reference site is named |
| `design-intel` | what is *generally* right (layout, spacing, UX, a11y, chart choice) | before building, always |
| `design-sources` | whether what I built is *good enough to ship* | after building, before delivery |

### Precedence when they disagree

1. Explicit instruction in the request
2. `branding-agent` for colors, fonts, logo on any Bishop AI or Prompt Anything work
3. Active extracted design system (layout, spacing, type scale, components, motion)
4. Style preset (`minimalist-skill`, `brutalist-skill`) for aesthetic character
5. `design-intel` where 2 to 4 are silent
6. Skill defaults

Measured beats recommended where both cover a decision. Borrow ratios and
structure from an extracted system; keep brand colors, typefaces and logo from
`branding-agent`. Only the literal phrase "full \<name\> system" promotes an
extracted system above brand, and only for that one deliverable. Full contract:
`skills/design-extract/references/consumption.md`.

### The gate is not optional

`design-sources` is a gate, not a precedence layer. Any HTML deliverable runs it
before shipping, whichever layer supplied the values:

```
python C:/Users/richm/.claude/skills/design-sources/scripts/check_design.py <file> 
```

Exit 0 = ship. Exit 2 = findings to fix. Never self-assess a page as clean, and
gate the HTML *before* the PDF or screenshot step. Brand conflicts get a scoped,
reasoned entry in `design-sources/brand-overrides/config.json`, never a blanket
ignore.

### ui-ux-pro-max plugin collisions

The plugin ships generic design skills that overlap mine. On my work, mine wins:

| Plugin skill | Always defer to |
|---|---|
| `brand` | `branding-agent` |
| `slides` | `slideforge` or `prestige` |
| `design` (logo, banner, CIP) | `citadel`, `carousel`, `infographic-generator` |
| `ui-styling`, `design-system` | `visual-code` |
| `banner-design` | `citadel` |

The `ui-ux-pro-max` skill itself has no conflict. Query it freely.
