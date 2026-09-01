# Adapter: brand graphics and generated images

Owner skills: `branding-agent`, `citadel` (thumbnails), `carousel`,
`infographic-generator`, `imagegen-frontend-web`, `reel-cover`.

**Guidance only. The gate does not run here.** These produce PNG/JPG, and
`impeccable detect` scans HTML, CSS and live URLs. There is nothing for it to
parse. Do not claim a gate pass on an image deliverable.

The exception: if the image is produced by screenshotting an HTML card (the
infographic and carousel pipelines do this), run the gate on that intermediate
HTML before capture. That is the one place the detector earns its keep in this
cluster.

## What transfers to image work

The digest's refuse list is mostly about visual reflexes, and those survive the
jump from DOM to canvas:

- **No kicker or eyebrow above the headline.** Absolute ban. Thumbnails and
  carousel slides reach for this constantly.
- **No gradient text.** Emphasis comes from weight or size.
- **No purple-to-blue gradients, no cyan-on-dark.** The most recognisable
  AI-image tells.
- **No icon-tile stack**: the rounded-square icon tile above every heading.
- **No same-size card grids** as the structure of a carousel. Vary the slide
  composition.
- **No emoji or Unicode glyphs standing in for icons.** Drawn SVG only.
- **No gray text on a coloured background.** Tint from the background hue instead.
- Contrast still governs: ≥4.5:1 for anything at body size, ≥3:1 for large
  display type. A thumbnail read at phone size is *less* forgiving than a page.
- **Real illustration or none.** Sketchy SVG, doodle scenes and grain filters
  read as amateur.

## What does not transfer

Ignore browser-surface theming, states, responsive breakpoints, motion, i18n and
overflow rules. There is no browser.

## Brand precedence is absolute here

This is the cluster where the brand lock matters most, because these are the
most visibly Bishop AI / Prompt Anything / BOB artifacts Rich ships.

- Colours come from `tokens.json` / `bob-tokens.css`. Never from an external
  source's palette advice.
- Bishop AI: Poppins (title), Montserrat (sub), Open Sans (body). BOB: Figtree.
  Impeccable's `overused-font` opinion does not get to relitigate a locked face.
- Light backgrounds are the default.
- Carousels: square 1:1, no word-labels or domains, hard-edge headshot never cut
  off, seamless panorama mode by default.
- Never reuse a headshot pose; use the pose ledger.
- Thumbnail subject fully in frame, bottom waist crop only.

These standing rules outrank anything in the digest. Where they are silent, the
refuse list above applies.
