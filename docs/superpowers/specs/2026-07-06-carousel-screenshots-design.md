# Carousel Real-Screenshot Cards — Design Spec

**Date:** 2026-07-06
**Scope:** Upgrade the `carousel` skill so value slides can show real, pixel-readable screenshots of the content being discussed, inside the existing signature 3D floating card, without changing the deck's look or breaking seamless mode.

## Problem

Every carousel currently uses image-model-generated (imagined) UI cards. Decks look great but feel samey and contain no real content. Rich wants real screenshots of the actual tools/sites/chats being discussed, captured live by Claude, while keeping the current style, feel, and look.

## Requirements (confirmed with Rich)

- **Source:** Claude captures screenshots live via Playwright during the carousel task (real tools, sites, dashboards, chats).
- **Placement:** Screenshot becomes the content of the signature tilted 3D floating card with amber glow. Style identical; content real.
- **Coverage:** Mixed decks. Slides referencing something screenshottable get a real capture; abstract slides keep generated cards.
- **Fidelity:** Pixel-perfect and readable. Composite real pixels programmatically. Never let the image model redraw a screenshot.
- **Seamless mode** (the default, per standing feedback) must keep working: cards can still straddle slide boundaries.

## Approach (Approach B — approved)

Build the screenshot card programmatically and composite it onto the generated panorama **before** slicing.

For screenshot slides, the panorama prompt leaves that zone's card area as plain uniform `#080B14` background (no model-drawn card). Separately, the real capture is wrapped in a CSS-built card that mimics the generated ones (dark rounded frame, 3D perspective tilt, drop shadow, golden-amber `#E0B848` glow), rendered by Playwright on a transparent background, then pasted onto the panorama with Pillow at an exact position and scale. Because the deck background is uniform near-black, the glow composites cleanly. Because compositing happens before `slice_panorama.py`, boundary-straddling bleed still works.

Deterministic by construction: regenerating a panorama just re-runs the composite — no manual alignment against model-drawn card corners (the rejected Approach A).

## Components

New scripts in `skills/carousel/scripts/`:

1. **`capture_screenshot.py`** — Playwright (chromium). Args: URL (or local HTML file), optional CSS selector or clip region, output path. Loads page, waits for network idle + render, captures at 2x device scale. Output: raw PNG in `images/carousels/<name>/captures/`.
2. **`render_card.py`** — Wraps a capture in the signature card. Loads an HTML template containing the screenshot inside a dark rounded frame with CSS `perspective` + `rotateY` tilt, drop shadow, and amber glow; Playwright screenshots it with transparent background at high resolution. Args: capture path, output path, optional tilt direction (left/right) and glow intensity. Output: `card-XX.png` (RGBA).
3. **`composite_card.py`** — Pillow. Args: panorama (or standalone slide) path, card PNG, x, y, target width, output path. Alpha-composites the card onto the image. Runs before slicing. Placement must obey the existing seamless rule: cards and glow stay out of the outer ~12% of each panorama so seams between groups remain invisible.

## SKILL.md changes

- **Planning step:** while writing slide content, tag slides that reference something real with `[SCREENSHOT: <url or tool> — <what to show>]`. Abstract/conceptual slides keep `[ICON:...]` / generated-card notes. Mixed decks are the norm.
- **Prompt rule:** for a screenshot slide's zone, the panorama prompt describes plain uniform `#080B14` background where the card will sit — the model must not draw a floating card in that zone. Neighboring generated-card zones are unchanged.
- **Workflow update (seamless mode):** plan groups → write panorama JSONs → generate panoramas AND capture screenshots in parallel → render cards → composite cards onto panoramas → slice → visual verify → CTA (unchanged, text-only) → upload. Standalone mode: composite onto the individual slide image instead.
- **Fallback rule:** if a target needs a login Claude can't reach, or won't render, use a generated card for that slide or ask Rich for a manual capture. Never fake a "real" screenshot with the image model.

## Verification

After compositing and slicing, view each final slide with the Read tool and check:

- Screenshot text is legible at slide size
- Card sits naturally — tilt, scale, and glow match neighboring generated cards
- Boundary bleed intact for cards straddling slide edges; no visible seams
- Zone furniture (number, label, handle) not covered by the card

**Shakedown:** first real use is a test carousel on a topic with an obvious screenshot target (e.g., PromptAnything or Claude Code) before trusting the pipeline on a scheduled post.

## Out of scope

- Video-frame extraction as a screenshot source (may come later)
- Full-bleed screenshot slide layouts (rejected — keep the card look)
- Image-to-image stylized redraws (rejected on fidelity grounds)
- CTA slide changes (stays text-only)
