# Adapter: video overlays and motion

Owner skills: `reelforge`, `hyperframes`, `claude-design-hyperframes`,
`slide-overlay`, `video-use`, `vistage`, `gsap`.

**Type-craft guidance only. The gate never runs here, and this adapter has the
narrowest remit of the four.**

## Read this first: the firewall

Rich's overlay grammar is already tightly specified and hard-won. The
Saraev / Murph / Mav cut styles, the IG safe band, white-plate captions, card
pacing, face-time ratios, the no-zoom rule. That grammar is **locked** and is not
open to revision by an external source written for websites.

There is a standing lesson that unifying a code path to fix a bug costs a
Saraev/Murph/Mav difference: share correctness, never share grammar. The same
applies here. Impeccable is a correctness input, never a grammar input.

**Do not** let anything in the digest change: card timing or hold length, plate
rules, safe-area bounds, caption sync approach, cut rhythm, face framing, zoom
policy, or the style-specific differences between the three cuts.

## What actually transfers

A short list. Type craft on a still frame is still type craft:

- **Contrast** on overlay text against the footage behind it. Same ≥4.5:1 floor.
  This is a real failure mode when a plate is semi-transparent.
- **Tracking floor -0.04em.** Overlay type set too tight is a common defect.
- **No gradient text** in an overlay. Weight or size instead.
- **Flat type hierarchy** is a real fault: an overlay where every line is the
  same size and weight reads as unconsidered.
- **Text overflow**: run the real caption at the real length; do not trust an
  estimate.
- **No emoji standing in for an icon.**

That is the whole transferable set. Everything else in the digest assumes a DOM.

## Rich's overlay rules that already outrank all of the above

- Never underline type in any overlay. Colour, a fill, or a bar beside it.
- Every glyph on a white plate; all plates touch; type inside the IG safe band.
- Overlays SHOW the artefact, never restate the caption in big type.
- Never open on an overlay; hook on the face.
- No zoom of any kind on talking-head footage.
- Advance text with `textlength`, not `textbbox`.

## Motion

Impeccable's motion guidance ("one authored moment", exponential ease-out,
no bounce/elastic easing) is written for web UI transitions. It is worth reading
for `gsap` and `hyperframes` work, where there genuinely is a DOM. It has no
authority over reel cut rhythm.

Bounce and elastic easing being dated is a fair point and worth honouring in
HyperFrames compositions.
