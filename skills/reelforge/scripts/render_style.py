#!/usr/bin/env python
"""Render one talking-head take into a Saraev / Murph / Mav cut.

One style-agnostic overlay track in, one styled cut out. The track says WHAT information
appears at a beat; the renderer decides how that object looks in its grammar.

    python render_style.py --base base.mp4 --words words.json --track overlay.txt \
                           --style saraev|murph|mav --out cut.mp4

Track format (see styles/THREE-STYLE-OUTPUT.md):
    0.0   STAT   21% | of finance teams ship | bar:0.21
    3.9   LIST   Bad data / No engineers / Weak model
    10.9  CLAIM  Not technical | and all three are free
    15.1  CITE   Cambridge alternative finance survey
    24.5  COUNT  3 | things separate them
    28.3  ITEM   1 | A number attached | before anybody builds
    43.1  CTA    comment | "Pilot"

Standing rules, enforced here so they stop being re-litigated (Rich, 2026-08-24):
  * NEVER alter voice speed. No atempo, and no setpts that SCALES pts. The cut is the
    length of the take. `setpts=PTS-STARTPTS` is used and is not a speed change: it is
    a constant origin reset that drags the container start_time to 0.
  * Captions bottom only, never mid-screen, rounded-corner pills.
  * Frame 0 is the FACE on the hook. No cut opens on a card. Enforced: the first Saraev
    cue must land at or after the end of the first spoken sentence, or this exits 1.
  * Nothing ever covers the face completely. Saraev cards fill the top band and the face
    bleeds in as a bottom strip; Murph and Mav stay full-frame face per their refs.
  * Overlays are ANIMATED, not static plates: numbers count up, bars fill, lines stack,
    rules draw, tiles pop. Rendered at 30fps so the motion is smooth.
  * Grammar per style is measured, not invented: styles/{saraev,murph,mav}-refs/analysis.md
"""
import argparse, json, re, subprocess, sys
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
# BOB brand, REBRANDED 2026-08-27 (joinbob.ai/landing/smb). Values lifted verbatim from
# .claude/bob-brand/bob-tokens.css, which was read off the site's own :root custom
# properties - never sampled by eye. The old #5A3FE0 / #0F9F8C / #F8FAFC set is retired.
# `SALMON` keeps its name because it is referenced in ~30 places; it is BOB violet.
#
# LIME IS ACTION ONLY and is deliberately UNUSED here: the brand rule is one lime element
# per screenful, on a surface, never on text or icons. A video overlay has no button
# surfaces, so violet stays the single accent and lime stays out rather than being misused
# as an emphasis colour.
BOB_VIOLET = (89, 33, 232)          # #5921E8  the one accent
BOB_LIME = (170, 235, 31)           # #AAEB1F  action only - see note above
BOB_INK = (10, 10, 10)              # #0A0A0A  headlines
BOB_GROUND = (251, 248, 255)        # #FBF8FF  lavender-tinted page ground, never neutral grey
BOB_FIELD2 = (247, 241, 253)        # #F7F1FD  second ground
BOB_MUTED = (138, 138, 144)         # #8A8A90
CREAM, INK, SALMON = BOB_GROUND, BOB_INK, BOB_VIOLET
WHITE, NEAR_BLACK = (255, 255, 255), (10, 10, 10)
YELLOW = BOB_VIOLET                 # legacy alias; nothing brand-side is yellow
PAL = {"cream": CREAM, "black": NEAR_BLACK, "white": WHITE}
FG = {"cream": INK, "black": (245, 245, 245), "white": INK}
FONTS = {"serif_i": "C:/Windows/Fonts/georgiaz.ttf",
         "serif_b": "C:/Windows/Fonts/georgiab.ttf",
         "sans_b":  "C:/Windows/Fonts/arialbd.ttf"}

# arialbd has no emoji glyphs, so an emoji in --banner renders as a tofu box. Mav's
# banners do end in one emoji, so this is real lost fidelity rather than a non-issue -
# but shipping a visible box is worse. Strip and say so. Proper colour-emoji rendering
# needs a second pass with seguiemj.ttf and embedded_color=True.
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\uFE0F\u2B00-\u2BFF]+")


_WARNED = set()


def strip_emoji(s, where="banner"):
    out = EMOJI.sub("", s).strip()
    # called once per rendered frame, so warn once per distinct string, not 1448 times
    if out != s.strip() and s not in _WARNED:
        _WARNED.add(s)
        print(f"WARNING: dropped emoji from {where} - arialbd cannot render it and it "
              f"would ship as a tofu box. Text kept: {out!r}")
    return out

# Saraev half-screen grammar (saraev-refs/analysis.md, "LAYOUT"): card fills the top
# ~55%, the face bleeds in as a bottom band. Never a floating panel beside the face.
SLOT_H = 1060
# A SHOT is a small framed INSET over the live face in EVERY grammar - never a slot
# fill, never a full-frame takeover (Rich, 2026-08-25: "the transition needs to be
# subtle, not the entire page"). Inside SAFE_TOP..CAP_Y so it clears the IG header
# and the caption block.
# Sized off a face detector, not by eye. haarcascade over every 5th frame of base.mp4
# found the face in 276 of 277 samples; inside the three SHOT windows the highest brow
# line sits at y 761. The box ends at 740, so his eyes are visible in every frame of
# every shot (Rich, 2026-08-28: "There's too much time when there are overlays over my
# face... Let me speak some more to the people so they can see my face").
#
# It was 960x760 at y300, which reached y 1060 - past his mouth. In those beats he was a
# mouth, a hand and a mic, and they covered 82% of the runtime with no gaps at all.
# Literal, not SAFE_L/SAFE_R: those are defined below this line and referencing them
# here is a NameError at import. Keep them in step by hand - 120 and 840 = 960 - 120.
# Rich, 2026-09-01: "I like the overlays (screenshots / recordings) to take over the whole
# screen." A SHOT now owns the FULL FRAME rather than riding as an inset over the live face.
# The pipeline contains-and-pads (decrease-scale + pad) instead of cover-cropping, so a
# landscape capture letterboxes onto the brand ground instead of losing 670px off each side.
SHOT_BOX = (0, 0, W, H)
STRIP_H = H - SLOT_H          # 860
FACE_Y = 520                  # crop origin: whole head with headroom (feedback_face_strip_full_head)
# ---- Instagram Reels title-safe band (Meta's published 14% top / 20% bottom).
# Conservative on purpose: TikTok's and Shorts' unsafe regions both sit inside this, so one
# band serves all three and we do not maintain per-platform layouts. Rule is BLEED THE PLATE,
# INSET THE TYPE - grounds and the face strip still run edge to edge, every glyph sits inside.
SAFE_TOP = 270
SAFE_BOT = 1536
# ---- HORIZONTAL safe band. Rich, 2026-08-31: uploaded to Instagram "it crops it to where
# it looks zoomed in". The file is a spec-perfect 9:16, but a 9:16 video (0.5625 w/h) on a
# 19.5:9 or 20:9 phone (0.4615 / 0.45) cannot fill the screen without being scaled up: the
# player matches HEIGHTS, the video becomes 1.22-1.25x wider than the screen, and the sides
# are cropped. That is the zoom, and it costs 97px per side at 19.5:9 and 108px at 20:9.
#
# Everything used to run x40..1040 - 40px margins - so the overlays were the first thing
# clipped. 120 clears the 20:9 worst case with 12px to spare.
SAFE_L, SAFE_R = 120, 960
RAIL_W, RAIL_TOP = 180, 1100   # right-hand action rail, only below RAIL_TOP
CAP_Y = SAFE_BOT - 36          # 1500: caption block BOTTOM edge, identical in all 3 styles
BANNER_Y = SAFE_TOP + 30       # 300: banner / HOOK lockup top edge

# ---- Every glyph sits on a white plate (Rich, 2026-08-25: "white backgrounds for ALL text").
# No text is drawn straight onto a card ground, onto video, or onto a dark pill anywhere.
PLATE = BOB_GROUND + (242,)     # #F8FAFC, slightly translucent
_OOB = []                      # safe-area violations, collected then reported by main()


def guard(y0, y1, what):
    """Record any type that lands outside the title-safe band.

    Collected rather than raised: a hard raise 1500 frames into a render loses the whole
    render, and one number being wrong should not cost 12 minutes. main() fails on it.
    """
    if y0 < SAFE_TOP or y1 > SAFE_BOT:
        k = (what, int(y0), int(y1))
        if k not in _OOB:
            _OOB.append(k)


def guard_x(x0, x1, what):
    """Same, for the horizontal band Instagram's fill-crop eats on a tall phone."""
    if x0 < SAFE_L or x1 > SAFE_R:
        k = (what + " [x]", int(x0), int(x1))
        if k not in _OOB:
            _OOB.append(k)
PLATE_R, PLATE_PAD = 30, 26    # radius / padding, inherited from the old caption pill
HOOK_R = 20                    # hook-lockup plates stack TOUCHING; at PLATE_R the
                               # corners pinch visibly where two plates meet
CAP_R = 20                     # caption plates stack touching too, same pinch


def row_h(font):
    """Plate height for `font`, CONSTANT for every string drawn in it.

    Sizing a plate from `textbbox(txt)[3]` makes the row height depend on whether that
    particular string happens to own a descender: "Practice more" measures short, "Study
    the frameworks" measures tall. Stack those and the whites can neither touch nor sit
    evenly - the gap breathes line to line, and closing it makes the glyphs collide
    (Rich, 2026-08-25: "the white around the text touching without the words going over
    eachother"). ascent+descent is the font's own line box, so every row is identical and
    the ink is guaranteed to sit inside its plate.
    """
    ascent, descent = font.getmetrics()
    return ascent + descent + PLATE_PAD
MAV_CAP_Y = CAP_Y              # kept as an alias; mav no longer has its own caption line


@lru_cache(maxsize=None)
def F(k, s): return ImageFont.truetype(FONTS[k], s)


def ease(p):
    """ease-out cubic, clamped."""
    p = 0.0 if p < 0 else (1.0 if p > 1 else p)
    return 1 - (1 - p) ** 3


def stagger(t, t0, i, step=0.22, dur=0.34):
    """Progress of element i in a stacked build starting at t0."""
    return ease((t - (t0 + i * step)) / dur)


# ---- "living card" motion. Every ease in a card completes inside ~0.9s, but holds now run
# 3-6s, so without this the card is a frozen plate for most of its life. Both of these draw
# OPAQUE (see mix()): a partial-alpha pass over a card punches through to the video.
PULSE_T = 2.5


def sheen(d, x, y, w, h, t, band=110):
    """A lighter band travelling along a filled bar, on the PULSE_T loop."""
    if w < band:
        return
    cx = x - band // 2 + int((w + band) * ((t % PULSE_T) / PULSE_T))
    a0, a1 = max(x, cx - band // 2), min(x + w, cx + band // 2)
    if a1 - a0 > 2:
        d.rounded_rectangle([a0, y, a1, y + h], h // 2,
                            fill=mix(SALMON, (255, 255, 255), 0.38))


# ---------------------------------------------------------------- track + captions
def parse_track(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip().lstrip("`")
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([\d.]+)`?\s+([A-Z]+)\s+(.*)", line)
        if not m:
            continue
        parts = [p.strip() for p in m.group(3).split("|")]
        row = {"t": float(m.group(1)), "kind": m.group(2), "parts": parts}
        # `hold:<seconds>` on a CARD row overrides the default INSERT for that beat.
        # SHOT rows parse their own hold in shot_spec, so leave their parts alone.
        if row["kind"] != "SHOT":
            keep = []
            for x in parts:
                if x.startswith("hold:"):
                    row["hold"] = float(x.split(":", 1)[1])
                elif x.startswith("logo:"):
                    row["logo"] = x.split(":", 1)[1].strip()
                else:
                    keep.append(x)
            row["parts"] = keep
        rows.append(row)
    for i, r in enumerate(rows):
        r["end"] = rows[i + 1]["t"] if i + 1 < len(rows) else 10_000
    return rows


def hook_row(track):
    return next((r for r in track if r["kind"] == "HOOK"), None)


def hook_end(track):
    """When the hook lockup / banner clears, in EVERY style.

    Murph used to draw its banner unconditionally, so a HOOK-derived banner sat on screen
    for the whole cut and collided with the numbered list from 28s on. The track's own
    `hold:` is now the single source of truth for how long the hook is up (Rich,
    2026-08-25: "remove the top hook caption after 4 seconds").
    """
    hk = hook_row(track)
    if hk:
        return min(hk["t"] + card_span(hk), hk["end"])
    return min((r["t"] for r in track), default=1e9)


# ---------------------------------------------------------------- HOOK (three grammars)
# The hook is the only overlay allowed at frame 0, so it IS the scroll-stop. v7 shipped it
# as dead type. `hook_pills()` drew Murph's and Mav's fully formed on frame 0 and never
# touched them again; `lockup()` finished its build at 0.95s and then froze for the
# remaining 3.75s of a 4.70s hold. It was also set SMALLER than the captions underneath it
# (54/52 against 58/62), so the hook read as a footnote to its own subtitles.
#
# Three rules now hold in every style, because they are legibility, not grammar:
#   * the hook outranks the caption in size - relatively. Both came down ~20% on
#     2026-08-30 (Rich: "make this hook and captions smaller"); the RATIO is the rule,
#     not the point sizes, so the hierarchy survives the change,
#   * the money token carries the violet accent - the same keyword device the captions
#     already use, so at hook scale it reads as house grammar rather than a new one,
#   * the hold carries EVENTS, spaced so no stretch of it sits dead.
#
# That third rule was first written as "something moves on every frame", and the first pass
# implemented it as a travelling hairline. Measured off the overlay layer (the composite is
# useless here - the face moving under the transparent gaps swamps the signal) that hairline
# changed ~180px per frame and left 84-91% of hook frames below any visible-change
# threshold. It was moving and it was not motion. What reads on a phone in a 4.7s hook is
# EVENTS with area: a line arriving, a number resolving, a block landing on it. So each
# style now fires 3-4 of them across the hold, in its own vocabulary, and HOOK_EVENTS
# below is the schedule they are measured against.
#
# The MOTION is per style and deliberately NOT shared (THREE-STYLE-OUTPUT.md, "Keeping the
# three APART" - one shared helper is how Murph and Mav collapsed into one renderer with
# two configs on v7). Saraev is centred serif that wipes open, counts up and rules itself
# top and bottom; Murph is left-rail sans that slides in, grows a vertical bar and takes a
# hard mechanical nudge; Mav is centred caps that snap word by word and stamp the number
# into a violet block. No two share a device.

HOOK_MAXW = (SAFE_R - SAFE_L) - PLATE_PAD * 2   # 788px: the plate, not just the ink,
                                               # has to fit the horizontal safe band
MONEY = re.compile(r"^\$[\d.,]+[kKmMbB]?$")


def fit_font(d, txt, key, size, maxw=HOOK_MAXW, floor=34):
    """Largest size <= `size` at which `txt` fits `maxw` on ONE line.

    An overflowing hook line does not warn, it silently wraps into an extra plate and the
    lockup stops being the shape it was designed as - "How $40k leaves" measured 835
    against an 828 limit and turned a two-plate lockup into three
    (feedback_hook_lockup_plates_touch). Measuring here means the copy can change without
    anyone re-deriving the point size by hand.
    """
    while size > floor and d.textlength(txt, font=F(key, size)) > maxw:
        size -= 2
    return F(key, size)


def salient(toks):
    """Index of the one word worth marking: a number if there is one, else the longest
    word that is not a stopword. Same choice caption_kw makes, so the hook marks the word
    the captions would have marked."""
    cand = [((1 if any(c.isdigit() for c in x) else 0, len(x)), k)
            for k, x in enumerate(toks) if x.lower().strip(STRIPCH) not in STOP]
    return max(cand)[1] if cand else -1


def money_tok(tok):
    return bool(MONEY.match(tok.strip(STRIPCH)))


# ---------------------------------------------------------------- half-screen hook stage
# Rich, 2026-09-01: "make this take up half the screen as an animated graphic". The hook is
# no longer plates floating over his face: it is a CARD filling the top SLOT_H, with his
# face reframed into the strip below it (see the hook window in main()). The motif SHOWS
# the claim rather than decorating it - three inbox rows arrive, then one of them is opened
# by somebody who is not you, which is the sentence the voice is saying.
#
# Each style still draws its OWN type over this stage (count-up, bar, word-snap), so the
# three do not collapse into one hook - see styles/THREE-STYLE-OUTPUT.md.
HOOK_EXIT = 0.42           # ground fade-out; the face strip must END when this STARTS
HOOK_TYPE_Y = 636          # type sits in the LOWER half of the card, under the motif
HOOK_ROW_W, HOOK_ROW_H = 640, 92


def hook_stage(d, hk, t, ground, accent=None):
    """Ground + animated inbox motif for the top half. Type is drawn after, by the caller."""
    accent = accent or SALMON
    t0 = hk["t"]
    # Nothing before the row starts. Murph and Mav call their hook unconditionally and let
    # `hook_end` bound it, so without this the ground painted from t=0 and the cut opened on
    # a full card - which the frame-0 gate correctly refused once it read the overlay layer.
    if t < t0:
        return
    he = min(t0 + card_span(hk), hk["end"])
    out = ease((t - (he - HOOK_EXIT)) / HOOK_EXIT)   # leaves on the same beat as the type
    a = 1.0 - out
    if a <= 0.01:
        return
    lift = int(18 * out)
    d.rectangle([0, 0, W, SLOT_H], fill=tuple(ground) + (int(255 * a),))

    cx = W // 2
    for i in range(3):
        pr = stagger(t, t0, i, step=0.22, dur=0.38)
        if pr <= 0:
            break
        y = 150 + i * (HOOK_ROW_H + 26) - lift
        x0 = cx - HOOK_ROW_W // 2 + int(-70 * (1 - ease(pr)))
        ra = int(255 * pr * a)
        breached = i == 2
        # the breached row is the EVENT: it arrives like the others, then its border and
        # marker cross-fade to the accent at +1.30, on the same beat as the type emphasis.
        bp = ease((t - t0 - 1.30) / 0.55) if breached else 0.0
        d.rounded_rectangle([x0, y, x0 + HOOK_ROW_W, y + HOOK_ROW_H], 16,
                            fill=(255, 255, 255, ra),
                            outline=mix((226, 232, 240), accent, bp)[:3] + (ra,),
                            width=3 + int(3 * bp))
        dr = 15
        d.ellipse([x0 + 26, y + HOOK_ROW_H // 2 - dr, x0 + 26 + dr * 2,
                   y + HOOK_ROW_H // 2 + dr],
                  fill=mix((203, 213, 225), accent, bp)[:3] + (ra,))
        for lw, ly in ((300, 30), (210, 56)):
            d.rounded_rectangle([x0 + 76, y + ly, x0 + 76 + int(lw * ease(pr)), y + ly + 12],
                                6, fill=mix((226, 232, 240), accent, bp * 0.35)[:3] + (ra,))
        if breached and bp > 0.05:
            tw = int(74 * ease(bp))
            d.rounded_rectangle([x0 + HOOK_ROW_W - 14 - tw, y + 22,
                                 x0 + HOOK_ROW_W - 14, y + HOOK_ROW_H - 22], 8,
                                fill=accent + (int(255 * bp * a),))
    d.rectangle([0, SLOT_H - 6, W, SLOT_H], fill=accent + (int(255 * a),))


def hook_line_kw(d, x, y, txt, font, alpha=1.0):
    """One hook line: the money token violet, everything else ink.

    Advances with textlength for the same reason caption_kw does - textbbox measures INK,
    so it under-reads a token's advance and each following word creeps left into the one
    before it.
    """
    a = int(255 * max(0.0, min(1.0, alpha)))
    for tok in txt.split():
        d.text((x, y), tok, font=font, fill=(SALMON if money_tok(tok) else INK) + (a,))
        x += d.textlength(tok + " ", font=font)


def hook_saraev(d, hk, t):
    """A: editorial. Four events, none of them a line. The plate WIPES open from its centre
    while the number counts up inside it (0.00), the second line rises into contact (0.38),
    the number CROSS-FADES from ink to violet (1.30), the second line's salient word does
    the same (2.80), then the whole thing fades and lifts away into the first SHOT.

    v9 carried these last two as rules drawing themselves under and over the lockup. Rich,
    2026-08-28: "dont underline anything." A soft ink-to-violet cross-fade on the word
    itself is the same emphasis without a rule, and a dissolve is his register anyway -
    Murph marks with a bar and Mav hard-cuts a block, so all three stay apart.

    The count-up is his alone: Murph and Mav both land their number instantly.
    """
    parts = [p for p in hk["parts"] if p]
    if not parts:
        return BANNER_Y
    hook_stage(d, hk, t, FLOW_CFG["saraev"]["ground"])
    t0, y = hk["t"], HOOK_TYPE_Y
    # The hook used to vanish on a single frame at hook_end while the first SHOT faded in
    # underneath it. Leaving in each style's own vocabulary is both a proper handoff and
    # the event that keeps the last ~1.5s of the hold from sitting dead.
    he = min(hk["t"] + card_span(hk), hk["end"])
    ex = ease((t - (he - 0.42)) / 0.42)
    # The lift is capped so the TOP rule (BANNER_Y - lift - 12) cannot rise out of
    # the title-safe band. At 26 it reached y 262 and the draw-time guard refused
    # the render, which is exactly what that guard is for.
    a_ex, lift = 1.0 - ex, int(18 * ex)
    for j, ln in enumerate(parts):
        f = fit_font(d, ln, "serif_b" if j == 0 else "sans_b", 84 if j == 0 else 58)
        pr = stagger(t, t0, j, step=0.38, dur=0.46)
        if pr <= 0:
            break
        rh = row_h(f)
        # Plate geometry comes from the FINAL string, never the counting one, or the box
        # jitters wider as digits are added underneath it.
        full = d.textlength(ln, font=f)
        txt = count_up(ln, pr) if j == 0 else ln
        x0, pw = int((W - full) / 2) - PLATE_PAD, int(full) + PLATE_PAD * 2
        dy = int(20 * (1 - pr)) - lift
        guard(y + dy, y + dy + rh, "hook lockup")
        half, cx = int(pw / 2 * ease(pr)), x0 + pw // 2
        d.rounded_rectangle([cx - half, y + dy, cx + half, y + dy + rh], HOOK_R,
                            fill=PLATE[:3] + (int(PLATE[3] * a_ex),))
        if pr > 0.30:
            # The emphasis EVENT: the marked token starts ink and cross-fades to violet,
            # line 0 at +1.30 and line 1 at +2.80. Everything else stays ink throughout.
            toks = txt.split()
            mark = 0 if j == 0 and money_tok(toks[0]) else salient(toks)
            mp = ease((t - t0 - (1.30 if j == 0 else 2.80)) / 0.50)
            a = int(255 * min(1.0, (pr - 0.30) / 0.70) * a_ex)
            x = (W - d.textlength(txt, font=f)) / 2
            for k, tok in enumerate(toks):
                col = mix(INK, SALMON, mp)[:3] if k == mark else INK
                d.text((x, y + dy + PLATE_PAD // 2), tok, font=f, fill=col + (a,))
                x += d.textlength(tok + " ", font=f)
        y += rh          # plates TOUCH, never a gap
    return y


def hook_murph(d, hk, t):
    """B: blunt, off the left rail. Plates enter from off-frame LEFT and settle on x=70,
    the same rail and the same slide his numbered list uses; nothing here is centred and
    nothing dissolves. From +1.30s a violet BAR draws down the left edge of the lockup and
    a brighter segment keeps drifting down it for the rest of the hold.

    The bar replaced a violet highlighter block over the money token. That block was the
    right gesture and the wrong one to give this cut: Mav already stamps its number into a
    violet block, so in a still frame the two hooks were the same picture again and only
    the motion told them apart (THREE-STYLE-OUTPUT.md, "Keeping the three APART"). A
    vertical rule is the one axis nothing else in the set uses, and it belongs to the rail
    his list already sits on. Murph's money stays violet type on white.
    """
    parts = [p for p in hk["parts"] if p]
    if not parts:
        return BANNER_Y
    hook_stage(d, hk, t, FLOW_CFG["murph"]["ground"])
    t0, y = hk["t"], HOOK_TYPE_Y
    top, left, settled = BANNER_Y, None, True
    # Leaves the way it arrived - back off the left rail, not a fade. Same reason as
    # Saraev's lift: the hook used to disappear on one frame, and the last ~1.5s of the
    # hold had no event in it.
    he = min(hk["t"] + card_span(hk), hk["end"])
    ex = ease((t - (he - 0.36)) / 0.36)
    for j, ln in enumerate(parts):
        # Ceilings, not fixed sizes: fit_font steps down to whatever actually fits, so the
        # hook is always as large as the line allows. v7 set the second line at 58 against
        # a 58 caption - the hook did not outrank its own subtitles.
        f = fit_font(d, ln, "sans_b", 70 if j == 0 else 56, HOOK_MAXW - 40)
        pr = stagger(t, t0, j, step=0.14, dur=0.30)
        if pr <= 0:
            break
        rh, tw = row_h(f), d.textlength(ln, font=f)
        # The whole lockup takes a hard mechanical nudge off the rail at +2.70 and stays
        # there. Translating every plate at once is the largest-area event available in
        # this grammar, and a blunt shove is his register - Saraev would draw a rule.
        nudge = 26 if (t - t0) >= 2.70 else 0
        x0 = SAFE_L + 20 + nudge + int(-460 * (1 - pr)) - int(760 * ex)
        guard(y, y + rh, "hook pill")
        d.rounded_rectangle([x0, y, x0 + int(tw) + PLATE_PAD * 2, y + rh], HOOK_R,
                            fill=PLATE[:3] + (int(PLATE[3] * pr),))
        hook_line_kw(d, x0 + PLATE_PAD, y + PLATE_PAD // 2, ln, f, pr)
        left = x0 if left is None else min(left, x0)
        settled = settled and pr >= 1.0
        y += rh
    # The rail bar. Held off until the plates have finished sliding, or it draws in the
    # air beside type that has not arrived yet.
    if settled and left is not None and t > t0 + 1.30:
        pr = ease((t - (t0 + 1.30)) / 0.34)
        x1, y1 = left - 18, top + int((y - top) * pr)
        guard(top, y, "hook rail")
        d.rectangle([x1, top, x1 + 20, y1], fill=SALMON + (255,))
        if pr >= 1.0:
            # brighter segment drifting DOWN the bar on the shared pulse loop
            span, band = y - top, 120
            cy = top - band // 2 + int((span + band) * ((t % PULSE_T) / PULSE_T))
            a0, a1 = max(top, cy - band // 2), min(y, cy + band // 2)
            if a1 - a0 > 2:
                d.rectangle([x1, a0, x1 + 20, a1],
                            fill=mix(SALMON, (255, 255, 255), 0.42))
    return y


def hook_mav(d, hk, t):
    """C: kinetic caps. Words SNAP on one at a time and the plate grows rightward by
    exactly that word's advance - no alpha ramp anywhere, because his corpus hard-cuts
    (mav-refs S3: median zero gaps, no dissolves). Through the hold the money token
    hard-cuts into a violet block and back out twice. Caps and word-snap are his; the
    other two cuts fade and neither is set in caps.
    """
    parts = [p.upper() for p in hk["parts"] if p]
    if not parts:
        return BANNER_Y
    hook_stage(d, hk, t, FLOW_CFG["mav"]["ground"])
    t0, y, n = hk["t"], HOOK_TYPE_Y, 0
    for i, ln in enumerate(parts):
        f = fit_font(d, ln, "sans_b", 64 if i == 0 else 54)
        toks = ln.split()
        shown = [tk for k, tk in enumerate(toks) if t >= t0 + (n + k) * 0.08]
        n += len(toks)
        if not shown:
            break
        rh = row_h(f)
        full = d.textlength(ln, font=f)
        x0 = int((W - full) / 2) - PLATE_PAD
        grown = d.textlength(" ".join(shown), font=f)
        guard(y, y + rh, "hook pill")
        u = t - t0
        # The second line hard-INVERTS to white on violet for 0.55s at +2.55. A whole
        # plate flipping is the biggest event this grammar allows, it needs no ramp (his
        # corpus hard-cuts), and it lands in the gap between the number's own stamps.
        inv = i == 1 and 2.55 <= u < 3.10
        d.rounded_rectangle([x0, y, x0 + int(grown) + PLATE_PAD * 2, y + rh], HOOK_R,
                            fill=(SALMON + (255,)) if inv else (255, 255, 255, 242))
        x, ty = x0 + PLATE_PAD, y + PLATE_PAD // 2
        for tok in shown:
            # Three pulses, not two: at 1.50/3.00 the longest frozen stretch was 0.94s,
            # which is long enough to read as a still frame in a 4.7 w/s grammar.
            hot = money_tok(tok) and (1.10 <= u < 1.70 or 2.30 <= u < 2.90
                                      or 3.50 <= u < 4.10)
            if hot:
                tk = d.textlength(tok, font=f)
                d.rounded_rectangle([x - 8, ty - 6, x + tk + 8,
                                     ty - 6 + rh - PLATE_PAD + 12], 10,
                                    fill=SALMON + (255,))
            if inv:
                col = WHITE
            else:
                col = WHITE if hot else (SALMON if money_tok(tok) else INK)
            d.text((x, ty), tok, font=f, fill=col + (255,))
            x += d.textlength(tok + " ", font=f)
        y += rh
    return y


# ---------------------------------------------------------------- FLOW (converge card)
# Modelled directly on saraev-refs/ns1.mp4 at 1.2-3.6s, which is the one card in the whole
# reference corpus that is genuinely watchable. Rich, 2026-08-30: "Have cards that come up
# that are engaging... look at the videos that have examples."
#
# What that reference actually does, frame by frame - and none of it is typography:
#   1.2s  an OBJECT sits centred (icon + "Claude Code" + "PLUGIN INSTALLER") with an empty
#         progress bar under it reading "Preparing... 0%"
#   2.0s  numbered arrows begin ARRIVING at the object, one at a time, and the bar fills
#   2.8s  all five arrows are in, the bar completes and flips orange to
#         "checkmark Claude Code Plugin installed  100%"
#
# So the device is: a thing, other things arriving at it one by one, and a state
# completing. It is engaging because it RESOLVES - not because the type is large. Every
# card this pipeline shipped before was a plate with words on it, which is why they read as
# subtitles in a bigger font (feedback_overlays_show_dont_restate).
#
# "Payments, accounting, bookkeeping, everything automated" is that exact shape: three
# things converging into one, ending in a completed state. The labels land on the spoken
# words, the bar fills, and it resolves to "everything automated" as he says it.
#
#   t  FLOW  <label1> | <label2> | <label3> | node:<centre> | done:<final state>
#            | at:<t1,t2,t3> | hold:<s>
#
# It draws into the SHOT box, so it obeys the same face rule as every screen recording:
# bottom edge at y740, clear of his brow line (feedback_face_time_over_overlay_density).

def flow_spec(r):
    """(labels, node, done, [t1,t2,t3], hold) for a FLOW row.

    A label may carry context as `Label :: detail`. Bare department nouns read as a
    diagram legend rather than a claim (Rich, 2026-08-30: "have the 1,2,3 have more
    context"), so `labels` returns (head, detail) pairs and detail may be "".
    """
    labels, node, done, at, hold, box = [], "BOB", "", None, None, ""
    for x in r["parts"]:
        if x.startswith("box:"):
            box = x.split(":", 1)[1].strip()
        elif x.startswith("node:"):
            node = x.split(":", 1)[1].strip()
        elif x.startswith("done:"):
            done = x.split(":", 1)[1].strip()
        elif x.startswith("at:"):
            at = [float(v) for v in x.split(":", 1)[1].split(",")]
        else:
            head, _, det = x.partition("::")
            labels.append((head.strip(), det.strip()))
    hold = r.get("hold", 4.0)
    if at is None or len(at) != len(labels):
        at = [r["t"] + 0.10 + i * 0.45 for i in range(len(labels))]
    return labels, node, done, at, hold, box


def _arrow(d, x0, y0, x1, y1, p, col, w=5):
    """Arrow drawing itself from (x0,y0) toward (x1,y1), p in 0..1, head at the end."""
    p = max(0.0, min(1.0, p))
    if p <= 0:
        return
    ex, ey = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    d.line([x0, y0, ex, ey], fill=col + (255,), width=w)
    if p > 0.82:                       # head only once it has essentially arrived
        import math
        a = math.atan2(y1 - y0, x1 - x0)
        h, sp = 20, 0.42
        d.polygon([(ex, ey),
                   (ex - h * math.cos(a - sp), ey - h * math.sin(a - sp)),
                   (ex - h * math.cos(a + sp), ey - h * math.sin(a + sp))],
                  fill=col + (255,))


def _tick(d, x, y, sz, p, col, w=8):
    """A checkmark drawn as two strokes, sweeping on.

    NOT a glyph. arialbd has no U+2713 and it shipped as a tofu box in the first pass -
    the same failure strip_emoji() already guards for banners.
    """
    p = max(0.0, min(1.0, p))
    if p <= 0:
        return
    ax, ay = x, y + sz * 0.52
    bx, by = x + sz * 0.36, y + sz * 0.88
    cx, cy = x + sz, y + sz * 0.06
    leg = 0.42                      # share of the sweep spent on the short stroke
    if p <= leg:
        q = p / leg
        d.line([ax, ay, ax + (bx - ax) * q, ay + (by - ay) * q], fill=col + (255,),
               width=w, joint="curve")
    else:
        q = (p - leg) / (1 - leg)
        d.line([ax, ay, bx, by], fill=col + (255,), width=w, joint="curve")
        d.line([bx, by, bx + (cx - bx) * q, by + (cy - by) * q], fill=col + (255,),
               width=w, joint="curve")


def draw_flow(im, d, r, t, cfg):
    """The converge card: three things arriving at one, then a state completing.

    Layout is a LEFT COLUMN of labels feeding a node on the right, not three labels across
    the top. Across the top was the first attempt and the words collided: "Bookkeeping" is
    ~300px at a readable weight and three of those do not fit in an 820px box, so the type
    had to shrink to 38pt to fit and became unreadable at phone size. Stacked, each label
    owns the full column width and can be set at 54.

    cfg carries the per-style TREATMENT only. The structure is shared on purpose - the
    shape is the argument the line makes, and it is the same argument in all three cuts.
    """
    labels, node, done, at, hold, box = flow_spec(r)
    bx0, by0, bw, bh = ([int(v) for v in box.split(",")] if box else cfg["box"])
    # The layout below was drawn against an 820x464 card. It is SCALED, not re-tuned, so a
    # bigger box cannot silently re-open the collisions that were measured out of it
    # (labels into the progress bar, labels into each other). Type scales on the vertical
    # factor - the smaller of the two here - so nothing stretches.
    kx, ky = bw / 820.0, bh / 464.0
    kf = min(kx, ky)
    def sx(v): return int(round(v * kx))
    def sy(v): return int(round(v * ky))
    u = t - r["t"]
    intro = ease(u / 0.36)
    if intro <= 0:
        return

    g = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g, "RGBA")
    # OPAQUE. At 248/255 his head ghosted through the card in the first pass; a diagram
    # with a face behind it reads as a mistake, not as translucency.
    gd.rounded_rectangle([0, 0, bw - 1, bh - 1], cfg["radius"],
                         fill=cfg["ground"] + (255,),
                         outline=cfg["edge"] + (255,), width=cfg["edge_w"])

    lf = F(cfg["label_f"], int(cfg["label_s"] * kf))
    nf = F(cfg["node_f"], int(cfg["node_s"] * kf))
    df = F("sans_b", int(cfg["done_s"] * kf))

    col_x, spine = sx(40), sx(452)
    n = max(1, len(labels))
    has_det = any(dt for _, dt in labels)
    # 88px pitch, not 104: at 104 the third label ran from y304 into the progress bar at
    # y320 and the two overprinted. Measured, the widest label is 362px (serif 54) against
    # a 412px column, so the width is fine - it was only the vertical rhythm that was wrong.
    # With details the row grows, so the label drops to 46 and the pitch tightens to 84.
    # Budget: 3 rows from y40 at pitch 84 end at y286 against the progress bar at y308.
    # The 88/54 pair is kept when there is no detail so existing cards are untouched.
    if has_det:
        lf = F(cfg["label_f"], int(46 * kf))
        dtf = F("sans_b", int(30 * kf))
        pitch, row0 = sy(84), sy(36)
    else:
        pitch, row0, dtf = sy(88), sy(40), None
    rows = [row0 + i * pitch for i in range(n)]
    node_w, node_h = sx(300), sy(116)
    node_x, node_y = bw - sx(40) - node_w, sy(96)
    ncx, ncy = node_x + node_w // 2, node_y + node_h // 2

    for i, (lab, det) in enumerate(labels):
        txt = lab.upper() if cfg["upper"] else lab
        pr = ease((t - at[i]) / 0.34)
        if pr <= 0:
            continue
        ly = rows[i]
        gd.text((col_x + int(-22 * kx * (1 - pr)), ly), txt, font=lf,
                fill=cfg["ink"] + (int(255 * pr),))
        tw = gd.textlength(txt, font=lf)
        if det and dtf:
            dp_ = ease((t - at[i] - 0.14) / 0.30)
            if dp_ > 0:
                gd.text((col_x + int(-22 * kx * (1 - pr)), ly + int(lf.size * 1.02)),
                        det, font=dtf,
                        fill=cfg["accent"] + (int(210 * dp_),))
        y_mid = ly + lf.size * 0.62
        # horizontal run out of the label, then into the node - the arrow ARRIVES,
        # which is the whole device
        ap = ease((t - at[i] - 0.10) / 0.32)
        if ap > 0:
            x_from = col_x + tw + sx(18)
            _arrow(gd, x_from, y_mid, spine, y_mid, min(1.0, ap * 2), cfg["accent"],
                   max(3, int(cfg["arrow_w"] * kf)))
            if ap > 0.5:
                _arrow(gd, spine, y_mid, node_x - sx(10), ncy, (ap - 0.5) / 0.5,
                       cfg["accent"], max(3, int(cfg["arrow_w"] * kf)))

    gd.rounded_rectangle([node_x, node_y, node_x + node_w, node_y + node_h],
                         cfg["node_r"], fill=cfg["node_fill"] + (255,),
                         outline=cfg["accent"] + (255,), width=cfg["edge_w"])
    ntw = gd.textlength(node, font=nf)
    gd.text((ncx - ntw / 2, node_y + sy(22)), node, font=nf, fill=cfg["node_ink"] + (255,))

    # the bar that completes: this is what makes the card RESOLVE instead of just sit
    px0, px1, py = sx(40), bw - sx(40), sy(308)
    fill_t = at[-1] + 0.30
    fp = ease((t - fill_t) / 0.70)
    barh = sy(20)
    gd.rounded_rectangle([px0, py, px1, py + barh], 10, fill=cfg["track"] + (255,))
    if fp > 0:
        gd.rounded_rectangle([px0, py, px0 + int((px1 - px0) * fp), py + barh], 10,
                             fill=cfg["accent"] + (255,))
    if fp >= 1.0 and done:
        txt = done.upper() if cfg["upper"] else done
        dp = ease((t - fill_t - 0.70) / 0.34)
        tw = gd.textlength(txt, font=df)
        tick = int(40 * kf)
        x = (bw - (tw + tick + sx(20))) / 2
        _tick(gd, x, py + sy(42), tick, dp, cfg["accent"], w=max(5, int(9 * kf)))
        gd.text((x + tick + sx(20), py + sy(40)), txt, font=df,
                fill=cfg["ink"] + (int(255 * dp),))

    im.alpha_composite(g, (bx0, by0 - int(18 * ky * (1 - intro))))


FLOW_CFG = {
    # Saraev: cream ground and serif labels, thin drawn arrows - the ns1 treatment itself.
    "saraev": dict(box=SHOT_BOX, ground=(245, 241, 232), edge=BOB_VIOLET, edge_w=3,
                   radius=28, label_f="serif_b", label_s=54, node_f="serif_b", node_s=72,
                   done_s=40, upper=False, ink=INK, accent=BOB_VIOLET, node_r=18,
                   node_fill=(255, 255, 255), node_ink=BOB_VIOLET, arrow_w=4,
                   track=(226, 220, 208)),
    # Murph: flat white, sans, heavier arrows, squarer node. Blunter build.
    "murph":  dict(box=SHOT_BOX, ground=(255, 255, 255), edge=(226, 232, 240), edge_w=3,
                   radius=22, label_f="sans_b", label_s=52, node_f="sans_b", node_s=68,
                   done_s=38, upper=False, ink=INK, accent=BOB_VIOLET, node_r=10,
                   node_fill=BOB_VIOLET, node_ink=(255, 255, 255), arrow_w=7,
                   track=(226, 232, 240)),
    # Mav: caps everywhere, hard violet border, node inverted. His register is all-caps.
    "mav":    dict(box=SHOT_BOX, ground=(255, 255, 255), edge=BOB_VIOLET, edge_w=5,
                   radius=8, label_f="sans_b", label_s=46, node_f="sans_b", node_s=64,
                   done_s=34, upper=True, ink=INK, accent=BOB_VIOLET, node_r=4,
                   node_fill=INK, node_ink=(255, 255, 255), arrow_w=6,
                   track=(232, 236, 242)),
}


def flow_row(track, t):
    for r in track:
        if r["kind"] == "FLOW" and r["t"] <= t < min(r["t"] + r.get("hold", 4.0), r["end"]):
            return r
    return None


# ---------------------------------------------------------------- SHOT (real footage)
# A SHOT row drops a REAL screen recording into the style's overlay slot instead of a
# drawn card. Product beats have to be shown as the product, never as a designed panel
# (feedback_pa_overlay_real_ui) - a card reads as an ad, the real UI reads as proof.
#
#   t   SHOT   <file.mp4> | src:<in-point s> | hold:<seconds> | <caption shown under it>
#
# Held at least SHOT_MIN_HOLD so it never flashes past (feedback_broll_halfscreen_3s).
SHOT_MIN_HOLD = 3.0
SHOT_CACHE = Path(".shotframes")


def shot_spec(r):
    """(path, src_in, hold, crop, fit, hl, hlat, box) for a SHOT row.

    box = "x,y,w,h" in FRAME pixels, overriding SHOT_BOX for this row only. Used when a
    beat has to show a whole page rather than a region of one - the mode grid has 19
    chips in four groups, and any crop that makes them big enough also cuts some off
    (Rich, 2026-08-27: "dont zoom in, we need to show them all of them").

    crop = "x,y,w,h" in SOURCE pixels, applied before scaling. A full-page capture
    scaled into the slot leaves body text far too small to read on a phone, so each
    beat frames the region that carries it. fit = cover (fill, may crop) or contain
    (letterbox) - contain is right when the capture's aspect differs from the slot
    and cropping would eat the headline.
    """
    p = r["parts"]
    src, hold, crop, fit, hl, hlat, box = 0.0, None, "", "cover", "", 0.40, ""
    for x in p[1:]:
        if x.startswith("src:"):
            src = float(x.split(":", 1)[1])
        elif x.startswith("hold:"):
            hold = float(x.split(":", 1)[1])
        elif x.startswith("crop:"):
            crop = x.split(":", 1)[1].strip()
        elif x.startswith("fit:"):
            fit = x.split(":", 1)[1].strip()
        elif x.startswith("hl:"):
            hl = x.split(":", 1)[1].strip()
        elif x.startswith("hlat:"):
            hlat = float(x.split(":", 1)[1])
        elif x.startswith("box:"):
            box = x.split(":", 1)[1].strip()
    if hold is None:
        hold = max(SHOT_MIN_HOLD, r["end"] - r["t"])
    return p[0], src, max(SHOT_MIN_HOLD, hold), crop, fit, hl, hlat, box


@lru_cache(maxsize=None)
def src_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip().split(",")
    return int(out[0]), int(out[1])


@lru_cache(maxsize=None)
def src_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def fit_box(crop, sw, sh, tw, th):
    """Expand the must-stay-visible ROI to the target aspect, clamped to the source.

    `crop:` names the region that CARRIES the beat. The three styles have very different
    slot aspects (Saraev 1080x1060, Murph 960x760, Mav a full 1080x1920), so a single ROI
    cover-cropped to each one sliced the sides off the article in the Mav cut - Rich,
    2026-08-25: "why do you zoom in so much and cut off the content". The box now GROWS
    around the ROI, showing more of the surrounding page, and never cuts into it.
    """
    # NO `crop:` means "show the whole thing". Growing the full source to the target aspect
    # is a cover-crop: a 1080x856 band against a 9:16 slot becomes 481x856 and loses ~300px
    # off EACH side, which is how "and sends", "daily brief" and "ABC Supply changed its
    # routing number" all lost their edges when SHOT went full-frame (Rich, 2026-09-01).
    # Return the source untouched and let decrease-scale + pad letterbox it onto the brand
    # ground. `crop:` still grows around a named ROI, which is what that syntax is for.
    if not crop:
        return 0, 0, sw, sh
    cx, cy, cw, ch = [int(v) for v in crop.split(",")]
    ar = tw / th
    nw, nh = (ch * ar, float(ch)) if cw / ch < ar else (float(cw), cw / ar)
    if nw > sw:
        nw, nh = float(sw), sw / ar
    if nh > sh:
        nh, nw = float(sh), sh * ar
    ccx, ccy = cx + cw / 2, cy + ch / 2
    x = min(max(ccx - nw / 2, 0), sw - nw)
    y = min(max(ccy - nh / 2, 0), sh - nh)
    return int(x), int(y), int(nw), int(nh)


def shot_windows(track):
    return [(r["t"], min(r["t"] + shot_spec(r)[2], r["end"]))
            for r in track if r["kind"] == "SHOT"]


@lru_cache(maxsize=None)
def shot_dir(path, w, h, src, hold, crop="", fit="cover"):
    """Decode ONLY the slice a SHOT row uses, scaled to the target box.

    Decoding whole recordings would be wasteful: a 3-minute capture is ~5900 frames
    per geometry, and three styles want three geometries. Slicing first keeps each
    cache to the seconds actually on screen. Frames live on disk and are opened on
    demand rather than held as raw RGB in memory.
    """
    src_p = Path(path)
    tag = (crop.replace(",", "-") or "full") + "_" + fit
    out = SHOT_CACHE / f"{src_p.stem}_{w}x{h}_{src:.2f}_{hold:.2f}_{tag}"
    if out.exists() and any(out.glob("*.png")):
        return out
    out.mkdir(parents=True, exist_ok=True)

    sw, sh = src_size(str(src_p))
    bx, by, bw, bh = fit_box(crop, sw, sh, w, h)
    # the box already matches the slot aspect, so decrease-scale lands exactly on w:h and
    # the pad is a no-op; it only kicks in when the ROI had to be clamped to the source.
    vf = [f"fps={FPS}", f"crop={bw}:{bh}:{bx}:{by}",
          f"scale={w}:{h}:force_original_aspect_ratio=decrease",
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0xFBF8FF"]  # BOB lavender ground

    # A negative `src` means "freeze on frame 0 for that long, then play" (used to land a
    # baked-in sweep on the word being spoken), so the whole clip has to be on disk. For a
    # positive src, decode ONLY the slice actually shown. That assumption used to be
    # "captures here are 5-7s, so a whole-clip decode is ~200 frames per geometry" - a
    # 197s screen recording makes it 5927 per geometry and the render crawls to ~1 fps.
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    if src >= 0 and src_duration(str(src_p)) > hold + 2.0:
        cmd += ["-ss", f"{src:.3f}", "-t", f"{hold + 1.0:.3f}"]
    cmd += ["-i", str(src_p), "-vf", ",".join(vf), str(out / "f%05d.png")]
    subprocess.run(cmd, check=True)
    return out


def shot_base(path, src, hold):
    """Clip-frame index that the first cached frame corresponds to.

    Mirrors the slicing decision in shot_dir: a sliced cache starts at `src`, a
    whole-clip cache starts at 0. Keeping this in one place stops the index and the
    decode drifting apart.
    """
    if src >= 0 and src_duration(str(path)) > hold + 2.0:
        return int(src * FPS)
    return 0


@lru_cache(maxsize=None)
def shot_count(d):
    return len(list(Path(d).glob("*.png")))


@lru_cache(maxsize=192)
def shot_frame(path, w, h, src, hold, crop, fit, idx):
    d = shot_dir(path, w, h, src, hold, crop, fit)
    n = shot_count(str(d))
    if not n:
        return None
    i = idx - shot_base(path, src, hold)
    f = d / f"f{min(max(i, 0), n - 1) + 1:05d}.png"
    if not f.exists():
        return None
    return Image.open(f).convert("RGB")


GOLD = (247, 208, 96)


def _paste(im, fr, x, y, w, h, radius):
    if radius:
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=255)
        im.paste(fr, (x, y), mask)
    else:
        im.paste(fr, (x, y))


def _sweep(im, hl, srcbox, box, p):
    """Gold highlight wiping left-to-right over a SOURCE region, mapped into the slot.

    `p` runs 0..1, so the mark is PAINTED ON as he says the thing rather than sitting
    there pre-drawn. srcbox is the (px, py, cw, ch) actually on screen this frame, so the
    highlight tracks the push-in instead of drifting off the words.
    """
    if p <= 0:
        return
    px, py, cw, ch = srcbox
    x, y, w, h = box
    hx, hy, hw, hh = [int(v) for v in hl.split(",")]
    sx, sy = w / cw, h / ch
    x0, y0 = x + int((hx - px) * sx), y + int((hy - py) * sy)
    x1, y1 = x0 + int(hw * sx), y0 + int(hh * sy)
    x1 = x0 + int((x1 - x0) * min(p, 1.0))          # the wipe
    x0, y0 = max(x, x0), max(y, y0)
    x1, y1 = min(x + w, x1), min(y + h, y1)
    if x1 <= x0 or y1 <= y0:
        return
    reg = im.crop((x0, y0, x1, y1)).convert("RGB")
    tint = Image.new("RGB", reg.size, GOLD)
    im.paste(Image.blend(reg, tint, 0.42).convert("RGBA"), (x0, y0))


@lru_cache(maxsize=None)
def is_static(path):
    """True when a capture never moves, so it is a screenshot wearing an .mp4 extension.

    Measured 2026-08-25: all five CNBC/OpenRouter captures for script-04 were completely
    static, highlight already painted in at frame 0. Dropped into a slot they read exactly
    as Rich described - "it looks like random screenshots". A static source has to be
    DRESSED (push-in + a highlight that sweeps on the beat), which is the documented Saraev
    cutaway technique anyway (nick-sarev.md S14), not played and hoped over.
    """
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                          "fps=8,scale=270:480", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    import numpy as np
    a = np.frombuffer(raw, dtype=np.uint8)
    n = a.size // (270 * 480)
    if n < 2:
        return True
    a = a[:n * 270 * 480].reshape(n, 480, 270).astype(float)
    # COUNT changed pixels, never average the difference. A highlight sweep covers well
    # under 1% of the frame, so a mean-abs-diff dilutes a real 0.7s animation to ~0.015
    # and calls it static - which is exactly the mistake that froze frame 0 of the two
    # CNBC sweep captures and threw their highlights away (2026-08-25).
    changed = (np.abs(np.diff(a, axis=0)) > 24).sum(axis=(1, 2))
    return float(changed.max()) < 270 * 480 * 0.001


@lru_cache(maxsize=None)
def still_frame(path, src):
    out = SHOT_CACHE / f"still_{Path(path).stem}_{src:.2f}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{src:.3f}", "-i", path,
                        "-frames:v", "1", str(out)], check=True)
    return Image.open(out).convert("RGB")


PUSH = 0.07          # how much wider the shot starts before easing in to the ROI
# Mav's shot is full-bleed, so at full height its ROI landed under the caption plate and
# the caption sat on top of the highlight (Rich, 2026-08-25). End the page above the
# caption band and continue the page's own background under it: the caption then reads as
# sitting on the article's margin instead of covering the sentence being narrated.
MAV_SHOT_H = 1370


@lru_cache(maxsize=None)
def page_bg(path, src):
    im = still_frame(path, src)
    return im.getpixel((6, 6))


def paste_shot(im, r, t, box, radius=0, cache_box=None):
    """Composite the active frame of a SHOT row into box=(x, y, w, h).

    `cache_box` is the size the frames are DECODED at, which must stay constant for
    the whole row even while `box` breathes. framed_shot scales its box every frame
    for the pop-in, and the frame cache is keyed on size, so without this each frame
    of the ease triggers a fresh ffmpeg decode of the clip - ~40 decodes per SHOT.
    Decode once at the nominal size, then let PIL resize onto the live box.
    """
    path, src, hold, crop, fit, hl, hlat, _box = shot_spec(r)
    x, y, w, h = box
    dw, dh = cache_box if cache_box else (w, h)
    u = t - r["t"]
    if is_static(path):
        # dressed still: slow push-in from PUSH% wider onto the ROI across the whole hold
        still = still_frame(path, src)
        sw, sh = still.size
        bx, by, bw, bh = fit_box(crop, sw, sh, w, h)
        z = 1.0 + PUSH * (1.0 - ease(min(u / max(hold, 0.01), 1.0)))
        cw, ch = min(bw * z, sw), min(bh * z, sh)
        cx, cy = bx + bw / 2, by + bh / 2
        px = min(max(cx - cw / 2, 0), sw - cw)
        py = min(max(cy - ch / 2, 0), sh - ch)
        fr = still.crop((int(px), int(py), int(px + cw), int(py + ch))).resize(
            (w, h), Image.LANCZOS)
        _paste(im, fr, x, y, w, h, radius)
        if hl:
            _sweep(im, hl, (px, py, cw, ch), box, ease((u - hlat) / 0.55))
        return True
    idx = int((u + src) * FPS)             # negative src = freeze on frame 0, then play
    # Decode PUSH% wider than needed and ease onto the ROI across the hold, the same
    # treatment stills already get. A screen recording is often static for most of its
    # slice (a finished prompt just sits there), and in Mav's full-frame takeover there
    # is no face behind it, so those seconds render as a frozen plate and the delivery
    # gate fails them outright. The push keeps every frame changing and reads as intent.
    ow, oh = int(round(dw * (1 + PUSH))), int(round(dh * (1 + PUSH)))
    fr = shot_frame(path, ow, oh, src, hold, crop, fit, max(idx, 0))
    if fr is None:
        return False
    z = (1 + PUSH) - PUSH * ease(min(u / max(hold, 0.01), 1.0))
    vw, vh = ow * (z / (1 + PUSH)), oh * (z / (1 + PUSH))
    px, py = (ow - vw) / 2, (oh - vh) / 2
    fr = fr.crop((int(px), int(py), int(px + vw), int(py + vh)))
    if (fr.width, fr.height) != (w, h):
        fr = fr.resize((w, h), Image.LANCZOS)
    _paste(im, fr, x, y, w, h, radius)
    # `hl:x,y,w,h` marks a region of the SOURCE page. Some captures bake their own
    # highlight in at capture time; this is for the ones that do not, so a shot always
    # points at something rather than just sitting there (Rich: "it doesn't highlight
    # anything"). Coordinates are mapped through the same box the frame was cut from.
    if hl:
        sw, sh = src_size(path)
        bx, by, bw, bh = fit_box(crop, sw, sh, w, h)
        hx, hy, hw, hh = [int(v) for v in hl.split(",")]
        sx, sy = w / bw, h / bh
        x0, y0 = x + int((hx - bx) * sx), y + int((hy - by) * sy)
        x1, y1 = x0 + int(hw * sx), y0 + int(hh * sy)
        x0, y0 = max(x, x0), max(y, y0)
        x1, y1 = min(x + w, x1), min(y + h, y1)
        if x1 > x0 and y1 > y0:
            reg = im.crop((x0, y0, x1, y1)).convert("RGB")
            tint = Image.new("RGB", reg.size, GOLD)
            im.paste(Image.blend(reg, tint, 0.42).convert("RGBA"), (x0, y0))
    return True


MAT, KEYLINE = 16, 5              # white mat around a recording, then a salmon keyline
SHOT_IN, SHOT_OUT = 0.40, 0.32    # its own entrance and exit


def shot_box(r, default):
    """Per-row inset box, falling back to the style's default."""
    spec = shot_spec(r)[7]
    if not spec:
        return default
    v = [int(x) for x in spec.split(",")]
    return (v[0], v[1], v[2], v[3])


def framed_shot(im, r, t, box, radius=28):
    """A recording as a FRAMED cutout, with its own in/out move.

    Rich, 2026-08-25: "have borders around the cutouts and transitions". A capture butted
    straight against the slot edge reads as a screenshot pasted over the video; a white mat
    and a salmon keyline make it read as a deliberate insert, and the scale-in gives it an
    entrance instead of appearing between two frames.
    """
    x, y, w, h = box
    hold = shot_spec(r)[2]
    t0, t1 = r["t"], min(r["t"] + hold, r["end"])
    p = min(ease((t - t0) / SHOT_IN), ease((t1 - t) / SHOT_OUT))
    if p <= 0.01:
        return False
    s = 1.0        # pure cross-fade: no scale pop (Rich: "transitions as fading in")
    iw, ih = int(w * s), int(h * s)
    ix, iy = x + (w - iw) // 2, y + (h - ih) // 2
    pad = MAT + KEYLINE
    sw, sh = iw - pad * 2, ih - pad * 2
    if sw < 40 or sh < 40:
        return False
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer, "RGBA")
    ld.rounded_rectangle([ix, iy, ix + iw, iy + ih], radius + pad, fill=SALMON + (255,))
    ld.rounded_rectangle([ix + KEYLINE, iy + KEYLINE, ix + iw - KEYLINE, iy + ih - KEYLINE],
                         radius + MAT, fill=PLATE[:3] + (255,))
    # Decode at the size the shot settles to (s == 1.0), not at this frame's eased size,
    # or the pop-in spawns a fresh clip decode per frame.
    nom = (w - pad * 2, h - pad * 2)
    if not paste_shot(layer, r, t, (ix + pad, iy + pad, sw, sh), radius=radius,
                      cache_box=nom):
        return False
    if p < 1.0:
        layer.putalpha(layer.getchannel("A").point(lambda a: int(a * p)))
    im.alpha_composite(layer)
    return True


def caption_groups(words, maxw):
    """Sentence-bounded so a caption never straddles two thoughts."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if w["w"].strip().endswith((".", "?", "!")) or len(cur) == maxw:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    # A sentence boundary leaves runts ("it's real."), and one-word captions are banned
    # outright (Rich, 2026-08-25), so fold any group under 3 words into a neighbour while
    # keeping the merged group at 7 or fewer.
    i = 0
    while i < len(out):
        if len(out[i]) < 3:
            # backward first: a runt is almost always a sentence TAIL, and its own sentence
            # is behind it. Merging forward crosses into the next thought.
            if i > 0 and not out[i - 1][-1]["w"].strip().endswith((".", "?", "!"))                     and len(out[i - 1]) + len(out[i]) <= 7:
                out[i - 1] = out[i - 1] + out.pop(i); continue
            if i + 1 < len(out) and not out[i][-1]["w"].strip().endswith((".", "?", "!"))                     and len(out[i]) + len(out[i + 1]) <= 7:
                out[i] = out[i] + out.pop(i + 1); continue
        i += 1
    res = []
    for g in out:
        txt = re.sub(r"\s+([-',.%])", r"\1", " ".join(x["w"].strip() for x in g))
        res.append((g[0]["s"], g[-1]["e"], txt, g))
    return res


def wrap(d, txt, font, maxw):
    lines, line = [], ""
    for w in txt.split():
        t = (line + " " + w).strip()
        if d.textbbox((0, 0), t, font=font)[2] > maxw and line:
            lines.append(line); line = w
        else:
            line = t
    if line:
        lines.append(line)
    return lines


def caption(d, lines, font, y_base, fg, bg, pad=26, radius=30, gap=0):
    """Rounded pill per line, bottom-anchored. Never mid-screen.

    gap=0: a two-line caption reads as ONE connected white block, not two floating pills
    (Rich, 2026-08-25). Rows advance by the font's line box so the halves touch exactly
    and the glyphs still cannot meet.
    """
    ascent, descent = font.getmetrics()
    rh = ascent + descent + pad
    y = y_base - (rh * len(lines) + gap * (len(lines) - 1))
    guard(y, y_base, "caption")
    for l in lines:
        tw = d.textbbox((0, 0), l, font=font)[2]
        x0 = (W - tw) // 2 - pad
        if bg:
            d.rounded_rectangle([x0, y, x0 + tw + pad * 2, y + rh], radius, fill=bg)
        d.text(((W - tw) // 2, y + pad // 2), l, font=font, fill=fg)
        y += rh + gap


def mix(bg, fg, p):
    """Opaque blend of fg over bg. PIL's RGBA draw mode overwrites destination alpha,
    so anything drawn ON TOP of a card must be fully opaque or it cuts a hole through it."""
    p = 0.0 if p < 0 else (1.0 if p > 1 else p)
    return tuple(int(bg[i] + (fg[i] - bg[i]) * p) for i in range(3)) + (255,)


def centre(d, y, txt, font, fill, alpha=1.0, dy=0, bg=None):
    tw = d.textbbox((0, 0), txt, font=font)[2]
    if alpha < 1.0:
        fill = mix(bg, fill, alpha) if bg else fill[:3] + (int(255 * max(alpha, 0)),)
    d.text(((W - tw) // 2, y + dy), txt, font=font, fill=fill)
    return tw


def plate_line(d, y, txt, font, ground, alpha=1.0, dy=0, ink=INK):
    """One centred line of type on its own white plate. Returns the plate's height.

    Pre-mixed OPAQUE against `ground` rather than drawn with partial alpha: PIL's RGBA
    draw mode overwrites destination alpha, so a fading plate drawn straight onto a card
    punches a hole through to the video underneath (see mix()). The plate fades ground ->
    white and the type fades plate -> ink, so the whole build stays opaque at every step.
    """
    a = 0.0 if alpha < 0 else (1.0 if alpha > 1 else alpha)
    tw, rh = d.textbbox((0, 0), txt, font=font)[2], row_h(font)
    x0, y0 = (W - tw) // 2 - PLATE_PAD, int(y + dy)
    face = mix(ground, PLATE[:3], a)
    guard(y0, y0 + rh, f"card type {txt[:24]!r}")
    d.rounded_rectangle([x0, y0, x0 + tw + PLATE_PAD * 2, y0 + rh], PLATE_R, fill=face)
    d.text(((W - tw) // 2, y0 + PLATE_PAD // 2), txt, font=font, fill=mix(face[:3], ink, a))
    return rh


LOGO_DIR = Path(__file__).resolve().parent.parent / "assets" / "logos"


@lru_cache(maxsize=None)
def load_logo(name, height):
    """Brand mark scaled to `height`, dark ink on transparent."""
    f = Path(name)
    if not f.exists():
        f = LOGO_DIR / (name if name.endswith(".png") else name + "_logo.png")
    if not f.exists():
        return None
    im = Image.open(f).convert("RGBA")
    return im.resize((int(im.width * height / im.height), height), Image.LANCZOS)


def plate_logo(d, im, y, logo, ground, alpha=1.0, dy=0, height=130):
    """Brand mark on its own white plate, same geometry as a line of type.

    Rich, 2026-08-25: when Bishop AI is named, show the mark rather than setting the words.
    """
    lg = load_logo(logo, height)
    if lg is None:
        return 0
    a = 0.0 if alpha < 0 else (1.0 if alpha > 1 else alpha)
    pw = lg.width + PLATE_PAD * 2
    x0, y0 = (W - pw) // 2, int(y + dy)
    guard(y0, y0 + height + PLATE_PAD, "logo")
    # ground=None means we are over live video, not a card: use alpha like a caption
    # does. Mixing opaque against a colour there would paint a solid block on his face.
    fill = PLATE[:3] + (int(PLATE[3] * a),) if ground is None else mix(ground, PLATE[:3], a)
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + height + PLATE_PAD], PLATE_R, fill=fill)
    if a > 0.02:
        faded = lg.copy()
        faded.putalpha(lg.getchannel("A").point(lambda v: int(v * a)))
        im.alpha_composite(faded, ((W - lg.width) // 2, y0 + PLATE_PAD // 2))
    return height + PLATE_PAD


def plate_h(d, txt, font):
    """Height plate_line will occupy, for measuring a stack before drawing it."""
    return row_h(font)


def count_up(target, p):
    """46% -> 0..46 as the beat opens. Keeps any non-digit suffix/prefix."""
    m = re.match(r"^(\D*)(\d+)(.*)$", target)
    if not m:
        return target
    pre, num, post = m.group(1), int(m.group(2)), m.group(3)
    return f"{pre}{int(round(num * p))}{post}"


# ---------------------------------------------------------------- SARAEV
# Top-band card (0..SLOT_H), face strip below. Content BUILDS inside the card.
INSERT = 2.4
SAR_PAL = ["cream", "black", "cream", "white", "black", "cream",
           "cream", "black", "cream", "white", "black"]


def card_span(r):
    """How long this row occupies the slot.

    A SHOT holds far longer than a card insert, so it carries its own length. A card
    row defaults to INSERT unless the track gave it an explicit `hold:<seconds>`.
    """
    if r["kind"] == "SHOT":
        return shot_spec(r)[2]
    return r.get("hold", INSERT)


def card_windows(track):
    """Windows where the top slot is occupied, so the face plays as a bottom strip.

    HOOK is excluded on purpose: it is a lockup over the LIVE face, not a card, so the
    face must stay full-frame underneath it.

    SHOT is NOT excluded. A shot panel occupies y 300..1060 of a full-frame face, which
    leaves his mouth and chin and nothing else - 15 seconds of decapitated head on
    script-07, against feedback_face_strip_full_head. The strip has to engage under a
    product beat exactly as it does under a card; that is what shipped on script-08.
    """
    # Rich, 2026-08-25: "you dont need to move my face to the bottom. just have the overlay
    # go on the screen." The face strip is retired - the picture never reframes, overlays
    # composite over the live full-frame face. Returning no windows disables the crop in
    # main() while leaving the helper in place for anything that still asks.
    return []


def draw_card(track, i, t):
    """Slot content for row i at time t, on its own transparent frame.

    Split out of saraev() so a join can hold TWO cards at once: the outgoing one at its
    settled state and the incoming one from u=0, composited through a moving mask.
    """
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # "RGBA" blends partial-alpha draws instead of replacing the pixel. Without it a
    # fading glyph or a tinted bar track punches a hole clean through the card.
    d = ImageDraw.Draw(im, "RGBA")
    r = track[i]
    t0 = r["t"]
    # Real product footage rides as a SMALL INSET over the live face - it never takes the
    # slot or the frame (Rich, 2026-08-25: "the transition needs to be subtle, not the
    # entire page"). Nothing else is drawn, so the face shows through around it.
    if r["kind"] == "SHOT":
        framed_shot(im, r, t, shot_box(r, SHOT_BOX))
        return im
    u = t - t0
    # Indexed by position among DRAWN CARDS, not by raw track row. `SAR_PAL[i]` counted
    # every row - HOOK, SHOT, FLOW - so inserting the FLOW row on 2026-08-30 shifted the
    # CTA from index 3 ("white") to index 4 ("black") and it silently became a dark navy
    # card with near-white type. Nothing warns: the palette is valid, it is just the wrong
    # entry, and every card after an inserted row re-colours at once.
    cards = [j for j, q in enumerate(track) if q["kind"] not in ("HOOK", "SHOT", "FLOW")]
    pal = SAR_PAL[cards.index(i) % len(SAR_PAL)] if i in cards else SAR_PAL[0]
    bgc = PAL[pal]
    # No opaque slot ground and no seam feather: with the face strip gone, filling the top
    # 1060px would black him out, which is the one thing that must never happen. The card's
    # own white plates carry the contrast instead.
    fg = FG[pal] + (255,)
    # rule draws across as the beat opens, then a highlight travels it, so a long
    # hold never sits completely still
    p, k = r["parts"], r["kind"]
    head = sub = ""

    ordn = ""
    if k == "ITEM":
        ordn = {"1": "FIRST", "2": "SECOND", "3": "THIRD",
                "4": "FOURTH", "5": "FIFTH"}.get(p[0], p[0])
        head, sub = (p[1] if len(p) > 1 else ""), (p[2] if len(p) > 2 else "")

    bar = next((x for x in p if x.startswith("bar:")), None)
    # Type is centred in the VISIBLE part of the slot (SAFE_TOP..floor), never the
    # full plate, so nothing slides under the Instagram header. A bar reserves the
    # bottom of the slot, so the stack centres higher when one is present.
    floor = 820 if bar else SLOT_H

    if k == "CTA":
        fv, fk = F("serif_i", 130), F("sans_b", 112)
        hv = plate_h(d, p[0], fv)
        hk = plate_h(d, p[1], fk) if len(p) > 1 else 0
        y = max(SAFE_TOP, (SAFE_TOP + floor) // 2 - (hv + hk) // 2)
        pr = ease(u / 0.36)
        plate_line(d, y, p[0], fv, bgc, pr, dy=int(30 * (1 - pr)))
        if len(p) > 1:
            pk = ease((u - 0.30) / 0.36)
            plate_line(d, y + hv, p[1], fk, bgc, pk,
                       dy=int(34 * (1 - pk)), ink=SALMON)

    elif k == "LIST":
        items = [x.strip() for x in p[0].split("/")]
        f = F("serif_b", 78)
        rh = row_h(f)                         # identical for every item, so they stack flush
        y = max(SAFE_TOP, (SAFE_TOP + floor) // 2 - (rh * len(items)) // 2)
        for j, it in enumerate(items):
            pr = stagger(t, t0, j)
            plate_line(d, y, it, f, bgc, pr, dy=int(24 * (1 - pr)))
            if pr > 0.5:                      # strike it through once it has landed
                tw = d.textbbox((0, 0), it, font=f)[2]
                sw = int(tw * ease((pr - 0.5) / 0.5))
                yy = y + rh // 2
                d.line([(W - tw) // 2, yy, (W - tw) // 2 + sw, yy],
                       fill=SALMON + (255,), width=8)
            y += rh                           # no gap: the whites touch

    else:                                   # STAT / CLAIM / CITE / COUNT / ITEM
        if k != "ITEM":
            head, sub = p[0], (p[1] if len(p) > 1 else "")
            if k in ("STAT", "COUNT"):
                head = count_up(head, ease(u / 0.55))

        hf = F("serif_b", 190 if len(head) < 9 else 120)
        sf, of = F("sans_b", 46), F("serif_i", 140)
        hlines = wrap(d, head, hf, W - 160 - PLATE_PAD * 2) if head else []
        slines = wrap(d, sub, sf, W - 200 - PLATE_PAD * 2) if sub else []
        gap = 0                 # wrapped head/sub lines touch and read as one white block
        hh = [plate_h(d, ln, hf) for ln in hlines]
        sh = [plate_h(d, ln, sf) for ln in slines]
        logo, LOGO_H = r.get("logo"), 260
        total = ((LOGO_H + PLATE_PAD + 28) if logo else 0) \
            + ((plate_h(d, ordn, of) + 28) if ordn else 0) \
            + sum(hh) + gap * max(0, len(hh) - 1) \
            + ((30 + sum(sh) + gap * max(0, len(sh) - 1)) if sh else 0)
        y = max(SAFE_TOP, (SAFE_TOP + floor) // 2 - total // 2)
        if logo:
            pr = ease(u / 0.40)
            y += plate_logo(d, im, y, logo, bgc, pr,
                            dy=int(26 * (1 - pr)), height=LOGO_H) + 28
        if ordn:
            pr = ease(u / 0.36)
            y += plate_line(d, y, ordn, of, bgc, pr,
                            dy=int(28 * (1 - pr)), ink=SALMON) + 28
        pr = ease((u - (0.18 if ordn else 0)) / 0.34)
        for j, ln in enumerate(hlines):
            plate_line(d, y, ln, hf, bgc, pr, dy=int(26 * (1 - pr)))
            y += hh[j] + gap
        if slines:
            y += 30 - gap
            pr = ease((u - 0.34) / 0.34)
            for j, ln in enumerate(slines):
                plate_line(d, y, ln, sf, bgc, pr, dy=int(20 * (1 - pr)))
                y += sh[j] + gap

    if bar:
        try:
            v = float(bar.split(":")[1])
        except ValueError:
            v = 0.0
        bw, bx, by = W - 220, 110, 880
        d.rounded_rectangle([bx, by, bx + bw, by + 34], 17, fill=mix(bgc, fg, 0.18))
        fill_w = int(bw * v * ease(u / 0.75))
        if fill_w > 4:
            d.rounded_rectangle([bx, by, bx + fill_w, by + 34], 17, fill=SALMON + (255,))
            sheen(d, bx, by, fill_w, 34, t)   # keeps a held card from freezing
    return im


XFADE = 0.42        # join length; both cards are alive for this long at every boundary
WIPE_FEATHER = 110  # soft leading edge on a wipe, in px. A hard edge reads as a bar
                    # sliding over the card; a feathered one reads as a sweep.


def ease_io(p):
    """smoothstep - eases IN and OUT. ease() only eases out, so a join it drives
    starts at full speed and the transition snaps at its first frame."""
    p = 0.0 if p < 0 else (1.0 if p > 1 else p)
    return p * p * (3 - 2 * p)


def join_kind(track, a, b):
    """`push` inside a numbered run, `wipe` when the topic changes."""
    ka, kb = track[a]["kind"], track[b]["kind"]
    # Rich, 2026-08-25: "have the transitions as fading in". One treatment everywhere.
    #
    # The old card<->SHOT wipe existed because blending two OPAQUE slot cards left the
    # outgoing type legible through the incoming recording. That cannot happen now: cards
    # are transparent plates and a SHOT is a small inset, so a dissolve has nothing to
    # double-expose.
    return "dissolve"


def compose_join(prev_im, cur_im, kind, pr):
    """Blend the outgoing card into the incoming one. pr runs 0..1 across XFADE."""
    out = prev_im.copy()
    q = ease_io(pr)
    if kind == "push":
        dy = int(SLOT_H * q)
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(prev_im.crop((0, 0, W, SLOT_H)), (0, -dy))
        out.alpha_composite(cur_im.crop((0, 0, W, SLOT_H)), (0, SLOT_H - dy))
        return out
    if kind == "dissolve":
        return Image.blend(prev_im, cur_im, q)
    # wipe: a salmon edge sweeps left to right, dragging the new card behind it. The
    # reveal is FEATHERED - a hard edge reads as a bar sliding over the card, which is
    # what "smoother transitions" was about. The edge starts off-frame so it enters
    # cleanly, so x is negative for the first frames; nothing is revealed yet then.
    x = int((W + WIPE_FEATHER * 2) * q) - WIPE_FEATHER
    if x > -WIPE_FEATHER:
        row = []
        for i in range(W):
            if i <= x - WIPE_FEATHER:
                row.append(255)
            elif i >= x:
                row.append(0)
            else:
                row.append(int(255 * (x - i) / WIPE_FEATHER))
        strip = Image.new("L", (W, 1)); strip.putdata(row)
        mask = strip.resize((W, SLOT_H), Image.BILINEAR)
        full = Image.new("L", (W, H), 0)
        full.paste(mask, (0, 0))
        out.paste(cur_im, (0, 0), full)
    if 0 < x < W:
        # the accent fades up and back down instead of popping on and off
        edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        a = int(220 * min(1.0, 2.6 * min(pr, 1 - pr)))
        ImageDraw.Draw(edge).rectangle([x - 7, 0, x + 4, SLOT_H], fill=SALMON + (a,))
        out.alpha_composite(edge)
    return out


def saraev(t, track, caps):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    idx = None
    for i, r in enumerate(track):
        # FLOW draws itself above; HOOK has its own path. Neither is a draw_card kind and
        # handing either one to draw_card renders an empty plate.
        if r["kind"] in ("HOOK", "FLOW"):
            continue
        if r["t"] <= t < min(r["t"] + card_span(r), r["end"]):
            idx = i
            break
    if idx is not None:
        cur = draw_card(track, idx, t)
        u = t - track[idx]["t"]
        prev_i = None
        if u < XFADE:
            for j in range(idx - 1, -1, -1):
                # FLOW belongs here as much as HOOK. Without it the CTA's cross-fade
                # looked back, found the FLOW row butt-joining it at 24.20, and ran the
                # FLOW row through draw_card - which has no FLOW case, so it rendered the
                # row's raw parts ("Payments", "Accounting") as head/sub type at card
                # scale, translucent, straight over the CTA. Rich, 2026-08-30: "what is
                # this nonsense on second 24?". The main loop above was guarded on the
                # first pass and this look-back was not.
                if track[j]["kind"] in ("HOOK", "FLOW"):
                    continue
                pend = min(track[j]["t"] + card_span(track[j]), track[j]["end"])
                if abs(pend - track[idx]["t"]) < 0.05:      # they actually butt-join
                    prev_i = j
                break
        if prev_i is None:
            im.alpha_composite(cur)
        else:
            pend = min(track[prev_i]["t"] + card_span(track[prev_i]), track[prev_i]["end"])
            prev = draw_card(track, prev_i, pend - 0.001)
            im.alpha_composite(compose_join(prev, cur, join_kind(track, prev_i, idx),
                                            u / XFADE))
    fr = flow_row(track, t)
    if fr:
        draw_flow(im, d, fr, t, FLOW_CFG["saraev"])
    hk = hook_row(track)
    if hk and hk["t"] <= t < min(hk["t"] + card_span(hk), hk["end"]):
        hook_saraev(d, hk, t)
    g = next((c for c in caps if c[0] <= t < c[1]), None)
    if g:
        caption_kw(d, g[2], F("sans_b", 46), CAP_Y)
    return im


# ---------------------------------------------------------------- MURPH
# Full-frame face (murph-refs/analysis.md: "no half-screen slot, no card panel").
# Black pill banner + progressive numbered list ABOVE the hairline + two-line captions
# with ONE yellow keyword. Rows slide in; nothing sits over the face.
STOP = {"the","a","an","and","or","but","so","of","to","in","on","it","its","is","are","was",
        "were","you","your","that","this","for","with","at","as","be","by","from","if","not",
        "no","do","does","did","can","will","just","one","i","we","they","them","their"}
LIST_Y = 300
STRIPCH = ".,!?'\"“”’"


def caption_kw(d, text, font, y_base, maxw=None, upper=False):
    '''Bottom-anchored caption on white plates with ONE salient word in salmon.

    Rich, 2026-08-25: "for all captions, never do one word at a time, have 3-6 words with
    highlighting important words." Mav used to run strict one-word captions off its
    reference corpus; that is overridden here for every style.
    '''
    txt = text.upper() if upper else text
    # inside the horizontal safe band, not the full frame: a centred 860px caption
    # plate spans x110..970 and loses its ends to the 20:9 crop at x108/972.
    maxw = maxw or (SAFE_R - SAFE_L - PLATE_PAD * 2)
    toks = txt.split()
    cand = [((1 if any(c.isdigit() for c in x) else 0, len(x)), k)
            for k, x in enumerate(toks) if x.lower().strip(STRIPCH) not in STOP]
    hot = max(cand)[1] if cand else -1
    rows, cur = [], []
    for tok in toks:
        if cur and d.textbbox((0, 0), " ".join(cur + [tok]), font=font)[2] > maxw:
            rows.append(cur); cur = [tok]
        else:
            cur.append(tok)
    if cur:
        rows.append(cur)
    offs, run = [], 0
    for r_ in rows:
        offs.append(run); run += len(r_)
    lines = [" ".join(r_) for r_ in rows]
    # ONE height for every plate - row_h() is the single definition (see its docstring).
    lh = row_h(font)
    y = y_base - lh * len(lines)
    guard(y, y_base, "caption")
    # ONE plate behind the whole block, not one per line. Per-line plates hug each line's
    # width, so a narrow line notches into the wider one above it and the rounded corners
    # read as separate cards stacked on top of each other (Rich, 2026-08-30: "the captions
    # are on top of eachother"). Sizing the plate to the widest line removes every internal
    # seam, and the white still touches exactly as asked on 2026-08-25.
    widths = [d.textlength(l, font=font) for l in lines]
    bw = int(max(widths)) + PLATE_PAD * 2
    bx = int((W - bw) / 2)
    d.rounded_rectangle([bx, y, bx + bw, y + lh * len(lines)], CAP_R, fill=PLATE)
    for i, l in enumerate(lines):
        # textlength, not textbbox: bbox measures INK, so it under-reads a token's advance
        # and every following word crept left until the words overlapped (Rich, 2026-08-25:
        # "do not let the words go over eachother"). Measure and draw with the same metric.
        x = (W - widths[i]) / 2
        for k, tok in enumerate(l.split()):
            col = SALMON if offs[i] + k == hot else INK
            d.text((x, y + PLATE_PAD // 2), tok, font=font, fill=col + (255,))
            x += d.textlength(tok + " ", font=font)
        y += lh


MURPH_CARD_Y = 340
SWIPE_T = 0.26


def swipe(d, t, track):
    """Thin salmon accent crossing the frame at a beat boundary.

    Deliberately NOT a page wipe (Rich, 2026-08-25: "the transition needs to be subtle, not
    the entire page"). Two narrow skewed lines, low alpha, gone in a quarter second: enough
    to mark that the overlay changed, not enough to take the frame off him.
    """
    # Retired 2026-08-25. A travelling accent is a sweep across the frame, and Rich asked
    # for fades: "have the transitions as fading in". Overlays now cross-fade and nothing
    # moves across the picture. Kept as a no-op so callers do not need touching.
    return


def murph_card(d, im, r, t):
    """CLAIM / COUNT / CTA as a Murph-language plate: white, slides in from the left.

    These rows used to render NOTHING in this grammar, which left the cut on a bare face
    for 19-28s and again after 45s.
    """
    u = t - r["t"]
    pr = ease(u / 0.34)
    dx = int(-110 * (1 - pr))
    p = [x for x in r["parts"] if x]
    head = p[0] if p else ""
    sub_ = p[1] if len(p) > 1 else ""
    if r["kind"] == "COUNT":
        head, sub_ = p[0], (p[1] if len(p) > 1 else "")
    fh, fs = F("sans_b", 78 if len(head) < 14 else 58), F("sans_b", 44)
    band = SAFE_R - SAFE_L - PLATE_PAD * 2
    hl = wrap(d, head, fh, band) if head else []
    sl = wrap(d, sub_, fs, band) if sub_ else []
    # Line advance is the font's line box, not the string's ink height: lines without a
    # descender otherwise advance short and the next line rides up into them.
    lh, ls_ = sum(fh.getmetrics()), sum(fs.getmetrics())
    hs = [lh] * len(hl)
    ss = [ls_] * len(sl)
    tw = max([d.textbbox((0, 0), l, font=fh)[2] for l in hl] +
             [d.textbbox((0, 0), l, font=fs)[2] for l in sl] + [10])
    bw = tw + PLATE_PAD * 2
    bh = sum(hs) + sum(ss) + (18 if sl else 0) + PLATE_PAD * 2
    # SAFE_L, not 70: at 70 the CTA card's left edge sat outside the horizontal safe
    # band and was clipped for its whole life by Instagram's 20:9 fill-crop (which
    # starts at x108). Found by scanning the overlay layer, not by eye.
    x0, y0 = SAFE_L + dx, MURPH_CARD_Y
    guard(y0, y0 + bh, f"murph card {head[:20]!r}")
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], PLATE_R,
                        fill=PLATE[:3] + (int(242 * pr),))
    y = y0 + PLATE_PAD
    for i, l in enumerate(hl):
        d.text((x0 + PLATE_PAD, y), l, font=fh, fill=INK + (int(255 * pr),))
        y += hs[i]
    if sl:
        y += 18
        ps = ease((u - 0.20) / 0.34)
        for i, l in enumerate(sl):
            d.text((x0 + PLATE_PAD, y), l, font=fs, fill=SALMON + (int(255 * ps),))
            y += ss[i]
    if r.get("logo"):
        plate_logo(d, im, y0 + bh + 24, r["logo"], None, pr,
                   dy=int(20 * (1 - pr)), height=300)


def murph(t, track, caps, banner=""):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im, "RGBA")
    hk = hook_row(track)
    if hk and banner and t < hook_end(track):
        hook_murph(d, hk, t)
    # Murph's grammar is screen-record led (murph-refs/analysis.md): the recording
    # carries the beat as a rounded inset and the face stays live underneath it.
    for r in track:
        if r["kind"] != "SHOT":
            continue
        hold = shot_spec(r)[2]
        if r["t"] <= t < min(r["t"] + hold, r["end"]):
            framed_shot(im, r, t, shot_box(r, SHOT_BOX), radius=36)
            break

    items = [r for r in track if r["kind"] == "ITEM"]
    # MURPH_CARD_Y (340) sits inside the numbered list's band (LIST_Y 300 + n*96), so a
    # CLAIM firing between two ITEMs painted a plate straight through the list and both
    # went unreadable - it shipped that way on script-08 at 20s. In this grammar the list
    # IS the device for the list section, so nothing else takes that band while it is up.
    # Only the CTA overrides, and it fires after the list has cleared anyway.
    list_on = bool(items) and (items[0]["t"] - 0.5) <= t < (items[-1]["end"] + 1.2)
    cur = next((r for r in track if r["kind"] in ("CLAIM", "COUNT", "CTA", "STAT")
                and r["t"] <= t < min(r["t"] + card_span(r), r["end"])), None)
    if cur and not (list_on and cur["kind"] != "CTA"):
        murph_card(d, im, cur, t)

    if items:
        # 0.5s of lead, not 3.0s. At -3.0 the numerals appeared during the sentence
        # BEFORE the checks ("which is a much smaller story..."), so the scaffolding was
        # on screen while he was still on the previous thought - Rich, 2026-08-25: "the
        # 1,2,3 doesn't fit in with the spoken words". The empty-slot open loop is kept,
        # it just opens on the beat that starts the list.
        start = items[0]["t"] - 0.5
        # The list lives for the list SECTION, then clears. murph-refs run list-shaped
        # end to end so persistence never showed there; on a video that pivots away
        # (reveal, CTA) a list left up reads as a stale plate for the rest of the cut.
        stop = items[-1]["end"] + 1.2
        if start <= t < stop:
            f = F("sans_b", 52)
            for n, r in enumerate(items):
                y = LIST_Y + n * 96
                pr = stagger(t, start, n, step=0.18, dur=0.30)
                lab = r["parts"][1] if (t >= r["t"] and len(r["parts"]) > 1) else ""
                lp = ease((t - r["t"]) / 0.30) if lab else 0.0
                txt = f"{n+1}." + (f"  {lab}" if lab else "")
                tw = d.textbbox((0, 0), txt, font=f)[2]
                dx = int(-90 * (1 - pr))
                a = int(232 * max(pr, 0))
                d.rounded_rectangle([70 + dx, y - 12, 70 + dx + tw + 44, y + 70], 22,
                                    fill=(248, 246, 242, a))
                d.text((92 + dx, y), f"{n+1}.", font=f, fill=(20, 20, 20, a))
                if lab:
                    ox = d.textbbox((0, 0), f"{n+1}.  ", font=f)[2]
                    d.text((92 + dx + ox, y), lab, font=f,
                           fill=(20, 20, 20, int(255 * max(lp, 0))))
    fr = flow_row(track, t)
    if fr:
        draw_flow(im, d, fr, t, FLOW_CFG["murph"])
    swipe(d, t, track)          # transition band between beats
    g = next((c for c in caps if c[0] <= t < c[1]), None)
    if g:
        caption_kw(d, g[2], F("sans_b", 48), CAP_Y, upper=True)
    return im


# ---------------------------------------------------------------- MAV
# Full-frame face on the talking head, and the demo is a FULL-BLEED takeover.
# Measured over 20 reels (mav-refs/analysis.md S3): in his experiment format the face is
# absent for 82% of runtime and the UI runs edge to edge - no inset, no rounded card, no
# margin. No designed stat cards anywhere, and the caption is bare white ALL-CAPS
# with no pill (feedback_mav_two_formats, measured 2026-08-25).
def mav(t, track, caps, banner=""):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im, "RGBA")
    # The demo takes the whole frame and the face goes out entirely. This replaced a
    # 1000x900 inset that no reel in the corpus does: the inset was invented, not measured.
    for r in track:
        if r["kind"] != "SHOT":
            continue
        hold = shot_spec(r)[2]
        if r["t"] <= t < min(r["t"] + hold, r["end"]):
            framed_shot(im, r, t, shot_box(r, SHOT_BOX))
            break

    # NO designed stat cards. feedback_mav_two_formats, measured over his corpus on
    # 2026-08-25: there is not one in any reel, and Rich rejected the cut that had them.
    # A number in this style is carried by the real screen it came from plus the caption.
    lg = next((r for r in track if r.get("logo")
               and r["t"] <= t < min(r["t"] + card_span(r), r["end"])), None)
    if lg:
        pr = ease((t - lg["t"]) / 0.40)
        plate_logo(d, im, 380, lg["logo"], None, pr, dy=int(26 * (1 - pr)), height=340)

    # Banner geometry is measured, not chosen: median pill is 79% of frame width with its
    # top edge at 12% of frame height, which clears the head. It is the one overlay
    # allowed at t=0 in this style (see THREE-STYLE-OUTPUT.md rule 2a).
    fr = flow_row(track, t)
    if fr:
        draw_flow(im, d, fr, t, FLOW_CFG["mav"])
    hk = hook_row(track)
    if hk and banner and t < hook_end(track):
        hook_mav(d, hk, t)
    g = next((c for c in caps if c[0] <= t < c[1]), None)
    if g:
        f = F("sans_b", 50)
        # Fixed at 84% of frame height, measured, and it does NOT move when the demo
        # takes the frame - that is the point, the eye never re-hunts the caption.
        caption_kw(d, g[2], f, CAP_Y, upper=True)
    return im


# ---------------------------------------------------------------- driver
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--track", required=True)
    ap.add_argument("--style", required=True, choices=["saraev", "murph", "mav"])
    ap.add_argument("--banner", default="")
    ap.add_argument("--face-y", type=int, default=FACE_Y,
                    help="crop origin of the Saraev face strip; must show the whole head")
    ap.add_argument("--reuse-frames", action="store_true",
                    help="keep an existing overlay PNG sequence of the right length")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    global SHOT_CACHE
    # keep decoded SHOT frames beside the render, not in whatever cwd we ran from
    SHOT_CACHE = Path(a.out).parent / ".shotframes"

    words = json.loads(Path(a.words).read_text(encoding="utf-8"))
    track = parse_track(a.track)
    dur = words[-1]["e"]
    # Mav's captions are ONE word (measured: mav-refs/analysis.md S3, confirmed by eye
    # across four reels). The previous 4-word grouping was not from the reference.
    caps = caption_groups(words, 5)

    # Rule: frame 0 is the face on the hook. No cut opens on a card. The hook beat is the
    # first SENTENCE, not the first caption group.
    hook_end = next((w["e"] for w in words if w["w"].strip().endswith((".", "?", "!"))), 0.0)
    # HOOK rows are exempt: a lockup is type over the LIVE face, not a card, so it cannot
    # break the open-on-the-face rule. Only cards and SHOTs are checked.
    cards = [r for r in track if r["kind"] != "HOOK"]
    if cards and cards[0]["t"] < hook_end:
        print(f"REFUSED: first cue at {cards[0]['t']:.2f}s lands inside the hook beat "
              f"(ends {hook_end:.2f}s). Frame 0 must be the face; move the cue later.")
        return 1
    # The banner is drawn from t=0 and so bypassed the check above entirely, which left
    # the open-on-overlay rule unenforced rather than deliberately waived. Cut C is the
    # documented exception: measured over 20 @mavgpt reels, his pill is up from 0.00s in
    # 15 of 19 and covers the face in 9 frames out of ~4,500, so it never hides the hook.
    hk = hook_row(track)
    banner = a.banner
    if hk:
        # The track carries the hook now; --banner is legacy. A HOOK-derived banner is
        # allowed at 0.00s in every style: Rich asked for the hook text on screen from the
        # start (2026-08-25), and it is type on a plate, never a plate over his face.
        banner = " ".join(x for x in hk["parts"] if x)
    elif a.banner and a.style != "mav":
        print(f"REFUSED: --banner is drawn from 0.00s, inside the hook beat "
              f"(ends {hook_end:.2f}s), and style '{a.style}' opens on the face. "
              f"Only the mav cut may open with a banner. Use a HOOK row instead.")
        return 1

    seq = Path(a.out).parent / f".overlay_{a.style}"
    seq.mkdir(parents=True, exist_ok=True)
    fn = {"saraev": lambda t: saraev(t, track, caps),
          "murph":  lambda t: murph(t, track, caps, banner),
          "mav":    lambda t: mav(t, track, caps, banner)}[a.style]
    n = int(dur * FPS) + 2
    if a.reuse_frames and len(list(seq.glob("*.png"))) == n:
        print(f"reusing {n} overlay frames in {seq.name}")
    else:
        for f in seq.glob("*.png"):
            f.unlink()
        for i in range(n):
            fn(i / FPS).save(seq / f"f{i:05d}.png")

    # Saraev only: the face bleeds in as a bottom strip under the card. Never a full
    # blackout of the face. The strip is a reframe (crop), never a zoom.
    # The face reframes into the bottom strip for any window where an opaque card owns the
    # top band. That is now the HOOK in every style, not just Saraev cards: the half-screen
    # hook stage would otherwise sit straight over his eyes (Rich, 2026-09-01, asked for the
    # hook as a half-screen animated graphic - the face has to go somewhere).
    hk_row = hook_row(track)
    wins = card_windows(track)
    if hk_row:
        # END the strip where the ground STARTS fading, not where the hook ends. While the
        # ground is translucent the full-frame face shows through the top half, and the
        # strip is still painting the same face below it - Rich, 2026-09-01: "why am I
        # doubled here". Cutting the strip under a still-opaque card hides the switch, and
        # the fade then reveals the full-frame face underneath.
        hk_end = min(hk_row["t"] + card_span(hk_row), hk_row["end"])
        wins = wins + [(hk_row["t"], hk_end - HOOK_EXIT)]
    if wins:
        enable = "+".join(f"between(t,{x:.2f},{y:.2f})" for x, y in wins)
        fc = (f"[0:v]setpts=PTS-STARTPTS,split=2[s1][s2];"
              f"[s2]crop={W}:{STRIP_H}:0:{a.face_y},setsar=1[strip];"
              f"[s1][strip]overlay=0:{SLOT_H}:enable='{enable}'[bg];"
              f"[1:v]fps={FPS},format=rgba[o];[bg][o]overlay=0:0[v]")
    else:
        fc = (f"[0:v]setpts=PTS-STARTPTS[s];"
              f"[1:v]fps={FPS},format=rgba[o];[s][o]overlay=0:0[v]")

    # NOTE: no atempo, and no setpts that SCALES pts. `PTS-STARTPTS` is an origin reset
    # that drags the container start_time to 0 (an -ss seek leaves video at +0.033s and
    # that lag ships to the viewer). It cannot change duration or speed.
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.base,
                        "-framerate", str(FPS), "-i", str(seq / "f%05d.png"),
                        "-filter_complex", fc,
                        "-map", "[v]", "-map", "0:a", "-af", "asetpts=PTS-STARTPTS",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                        "-bf", "0", "-c:a", "aac", "-b:a", "192k", a.out],
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-700:]); return 1
    if _OOB:
        print(f"REFUSED: {len(_OOB)} element(s) drawn outside the Instagram title-safe "
              f"band ({SAFE_TOP}..{SAFE_BOT}):")
        for what, y0, y1 in _OOB[:12]:
            print(f"    {what}: y {y0}..{y1}")
        return 1
    print(f"{a.style}: {n} overlay frames -> {a.out} ({dur:.1f}s, voice untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
