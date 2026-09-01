# Brand and style-direction lookups

Owner skills: `branding-agent`, `minimalist-ui`, `industrial-brutalist-ui`.
They own the direction. This file tells you what to look up first.

Set `S` per the SKILL.md resolution block before running anything.

## Read the brand lock first

On Bishop AI, Prompt Anything and BOB work the palette and typefaces are
**already decided** and are not a lookup. `branding-agent` and `tokens.json` are
the source of truth. Querying the database for "what colours should Bishop AI
use" is the wrong question and the answer must be discarded.

What the database is *for* on branded work: structure, scale, spacing, pairing
mechanics, and the vocabulary to describe a direction. Not the identity itself.

Speculative work, moodboards, and client work with no brand yet may use database
palettes and pairings freely.

## Direction and style vocabulary

```bash
python "$S" "editorial serif minimal brand" -n 3
python "$S" "bold geometric sans display" -n 3
python "$S" "industrial brutalist grid typography" --domain style -n 3
```

84 styles indexed. Use these to *name* a direction precisely before building, so
`minimalist-ui` and `industrial-brutalist-ui` get a brief rather than a vibe.

Both of those skills already carry a fully specified aesthetic. The database
informs the direction; it does not override the skill's own protocol.

## Type pairing

```bash
python "$S" "editorial serif minimal brand" --domain google-fonts -n 3
python "$S" "display face with neutral body" --domain typography -n 3
```

74 pairings indexed. **On Bishop AI work the faces are locked**: Poppins (title),
Montserrat (sub), Open Sans (body). BOB is Figtree. Use pairing results only to
reason about weight, scale and contrast between the locked faces, never to
substitute one.

## Colour

```bash
python "$S" "muted warm neutral palette" --domain color -n 3
python "$S" "high contrast accent on light ground" --domain color -n 3
```

192 palettes indexed. On branded work take **only** the reasoning (how many
accents, where contrast sits, what carries state) and apply it to the locked
hexes. Never take a hex.

## Scale, spacing and hierarchy

```bash
python "$S" "type scale modular hierarchy" --domain typography -n 3
python "$S" "whitespace density layout" --domain style -n 3
```

This is the highest-value branded query: brand rarely specifies rhythm, so the
database fills a real gap without touching the lock.

## Cross-check against design-sources

Once a direction is chosen, read `design-sources` for the craft floor and the
refuse list before building. Direction and craft are different questions, and the
kicker/eyebrow ban, nested-card ban and gradient-text ban apply to brand work too.

## Before handing off

- Brand lock held: no database hex, no database face on branded work
- Direction named precisely, not as a vibe
- Light background unless there is a stated reason otherwise
- No em dashes anywhere
- Run the SKILL.md pre-delivery check
