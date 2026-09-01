---
name: reelforge
description: >
  Short-form video rendering pipeline. Handles ffmpeg filter chain, overlay compositing,
  caption burning, and audio mixing to produce final.mp4. Also provides rec_*.py
  screen recording scripts and brand configs. For talking-head-to-Short/Reel content
  with brand overlays, music, captions, thumbnail generation, and social copy.
---

# ReelForge — Short-Form Video Production

Full end-to-end pipeline: raw video → edited 9:16 clip + thumbnail + Instagram/LinkedIn captions + music + SFX.

Base dir: `C:\Users\richm\.claude\skills\reelforge\`
Workspace per video: `C:\Users\richm\.claude\skills\reelforge\videos\Unposted\<slug>\` (moved to `videos\Posted\` after publishing — if a workspace path 404s, check the other folder; all intake.json paths are absolute and must be repointed after a move)

---

## Workflow

### Step 1 — Intake

Ask ALL of the following in a SINGLE message. Don't split into multiple rounds.

---

**REELFORGE INTAKE — answer what you know, skip what doesn't apply:**

**Block 1 — Identity**
1. Brand? (Prompt Anything / Bishop AI / Personal)
2. Platform? (YouTube Short / Instagram Reel / both)
3. Slug? (short folder name, e.g. `google-search-short`)

**Block 2 — Raw Assets**
4. Raw talking-head video path?
5. Any screen recordings to overlay? For each: file path + when it should appear (start/end seconds in final video) + what second in the recording to start from
6. Hook card video to open with? (path, or none)
7. SFX: use built-in camera click / custom MP3 path / none?

**Block 3 — Video Structure**
8. Use the full raw video, or specific clip? (start/end seconds)
9. Target duration in seconds?
10. Paste the full script/transcript here (I'll auto-time the captions)

**Block 4 — Audio**
11. Music style? (lofi-hiphop / cinematic / upbeat / dark-tension / none)
12. Music volume? (default 12%)
13. SFX volume? (default 25%)

**Block 5 — Thumbnail**
14. Thumbnail headline? (5 words max across 2 lines — or say "suggest" and I'll propose)
15. Style? (dark-dramatic / light-editorial)
16. Which headshot? (specific file path, or "auto" to pick from brand folder)

**Block 6 — Social Copy**
17. What is this video about? (one sentence)
18. Opening line of the video?
19. Instagram tone? (direct / casual / hype)
20. LinkedIn tone? (professional / thought-leader / story)
21. What do you want viewers to do? (CTA)

---

### Step 2 — Caption Auto-Timing

**Sarev-style videos (the talking-head default) do NOT use this step.** Their captions come from measured word times on the spliced file, not from evenly-distributed script chunks:
1. `scripts/retime_words.py --video spliced.mp4 --out words.json` — windowed, silence-anchored transcription for the TRANSCRIPT text (full-file whisper drifts up to ~1.3s after pauses and bunches words, which both mistimes captions and triggers multi-word merges). Hand-fix product names/mishears in the json.
2. **Timing gold standard = CTC forced alignment, now promoted to `scripts/align_words.py`** (colorado-ai-law + anthropic-47b-revenue, 2026-07-17): `python scripts/align_words.py --video spliced.mp4 --words words.json --out words_aligned.json [--expand "SB=ESS BE"]`. torchaudio `forced_align` aligns the KNOWN transcript at frame level; on anthropic-47b-revenue whisper had 28/150 words off >0.15s (max 0.4s) and Rich read it as "the video is not lining up with the audio" — anchors at silences can all pass while mid-sentence words lag. The script auto-expands numbers/years/%/$/AI/Qn to spoken form, consumes the '|' separator spans, does the min-0.08s zero-width repair, prints a drift report, and FAILS if a word starts deep inside a real silence. The windowed-whisper times from step 1 are only the fallback when torchaudio is unavailable.
3. `scripts/make_sarev_ass.py --words words.json --out captions.ass --max-merge 1 --center-windows "<a-b,...>"`. Strict one-word captions are the standard (openai-codex-plugins, 2026-07-16): a 2-3 word merge shows words before they're voiced and Rich reads it as "the voice and captions don't go together". **Always pass `--center-windows` with every half-screen overlay window** (union of the screen_recordings ranges): captions there render mid-screen in the gap between card and face card instead of low over the face — Rich's explicit request, anthropic-47b-revenue 2026-07-17. Set `captions_ass_file` in intake.json and leave `captions: []`.

For non-sarev chunk-caption videos, when user pastes the script, break it into 2-4 word caption chunks:
- Distribute timestamps evenly across target_duration
- Pick the most punchy/important word per chunk as `highlight` (shown in gold)
- Leave gaps around screen recording windows (captions still show but subject changes)
- Format each chunk as: `{"start": X.XX, "end": X.XX, "text": "...", "highlight": "..."}`

**Caption vertical position (`"caption_position"`):** default `"bottom"` sits captions low. Set `"caption_position": "center"` and the renderer auto-centers each caption in the middle of the page **only while an overlay (full-screen b-roll or half-screen card) is on screen** for that chunk; captions over a bare talking-head shot stay low so they never cover the face. Use `"center"` on any video that runs b-roll/half-screen overlays (the renderer keys off the `screen_recordings` windows, so no per-caption tagging is needed).

### Step 3 — Thumbnail Headline

If user says "suggest" for headline, propose 3 options in this format:
```
Line 1 (white, 2 words): GOOGLE SEARCH
Line 2 (white, 2 words): WILL NEVER
Line 3 (gold, 2-3 words): BE THE SAME
```
Confirm before continuing.

**Thumbnail headshot flow (every video):** the headshot must come from the pose ledger — run `python C:\Users\richm\.claude\skills\citadel\scripts\pick_pose.py` (no args) to get the next unused reference image + index, put that path in `intake.json → thumbnail.headshot`, and after rendering commit it with `pick_pose.py --commit "<path>" <index>`. Never reuse a pose. Single-image references (non-grid aspect ratio) auto-detect as 1×1 — use `headshot_cell: [0, 0]`. Proven news-topic headline pattern: white statement line + gold question payoff ("THE NSA NOW" / "POLICES AI?"), dark-dramatic style.

### Step 4 — Write intake.json

Write to `C:\tmp\reelforge\<slug>\intake.json`:

```json
{
  "slug": "<slug>",
  "brand": "prompt-anything",
  "platform": ["youtube-short", "instagram-reel"],
  "workspace": "C:\\Users\\richm\\.claude\\skills\\reelforge\\videos\\<slug>",
  "raw_video": "<path>",
  "hook_card": {
    "file": "<path or null>",
    "timeline_start": 0.3,
    "timeline_end": 3.0,
    "source_start": 0.3
  },
  "screen_recordings": [
    {
      "file": "<path>",
      "timeline_start": 6.5,
      "timeline_end": 13.0,
      "source_start": 1.0
    }
  ],
  "sfx_source": "default",
  "beat_sync": true,
  "target_duration": 40,
  "captions": [
    {"start": 0.0, "end": 0.4, "text": "Google search", "highlight": "Google"}
  ],
  "music_style": "lofi-hiphop",
  "music_volume": 12,
  "sfx_volume": 25,
  "thumbnail": {
    "label": "PROMPT ANYTHING",
    "sub": "Google Search",
    "headline": "WILL<br>NEVER",
    "headline_gold": "BE THE<br>SAME",
    "style": "dark-dramatic",
    "headshot": "auto",
    "headshot_cell": [0, 0]
  },
  "social": {
    "topic": "Google AI Overview changed how search works",
    "hook": "Google search just changed for the first time in 25 years",
    "instagram_tone": "direct",
    "linkedin_tone": "professional",
    "cta": "follow for more"
  }
}
```

If `hook_card.file` is null, set the whole `hook_card` key to `null`.
If `screen_recordings` is empty, set it to `[]`.

**`beat_sync: true`** (default on): `video_processor.py` snaps every overlay `timeline_start` (= flash + SFX moment) to the nearest beat of the generated music (`music_gen.py` starts its beat grid at t=0; BPM per style: lofi-hiphop 80, cinematic 75, upbeat 95, dark-tension 88, overridable via `music_bpm`). It shifts that recording's `source_start` by the same delta so the content stays locked to the narration — only the cut moves (max ±half a beat). Back-to-back overlays whose end met the next one's start are re-stitched so no face-strip gap opens. Beat-sync only moves `screen_recordings` (and their flash/SFX); `callouts`, `chapters`, and `logo_overlays` keep their authored times — snap those to beats yourself if wanted.

**Per-recording `"no_flash": true`** suppresses the white flash + click SFX at that overlay's `timeline_start` — use it when two same-page windows butt-join and the cut should read as a silent jump (added 2026-07-15). **No zoom on the talking head, ever:** leave `punch_zooms` and `zoom_drift_windows` empty — Rich killed both the in-out punches and static framing windows ("stop zooming in and out"); engagement comes from overlay cadence, not scaling the face.

**Overlay windows near a splice join must release EXACTLY on the cut.** If an overlay ends within ~2s before a splice join in spliced.mp4, extend its `timeline_end` to the exact cut frame — locate it by frame-differencing spliced.mp4 around the join (numpy mean-abs-diff on grayscale rawvideo at 30fps; the cut reads ~3x the noise floor). The overlay's dissolve then completes exactly as the take changes, hiding the jump cut and killing the bare-face gap (Rich's request, trump-nsa-ai-eo 44–45s, 2026-07-16). Bonus: any splice join that lands INSIDE an overlay window is invisible — plan overlays over joins when possible.

**No sub-second cuts back to the full talking head.** A gap of <~1s between two overlay windows flashes the bare full-frame face for a beat and reads as a glitch. When two overlays are close, extend the earlier one's `timeline_end` to meet the next one's `timeline_start` (or pull the next one's start back) so the layout stays half-screen continuously. Deliberate full-head breathing beats of 1.5s+ are fine; sub-second flashes are not.

### Audio finishing (every video, 2026-07-08 standard)

- **Voice/music balance — DUCK the music, don't just turn it down.** A flat `music_volume: 12` still lets a dense (esp. Suno) track fight the voice — the "background too loud" complaint. Instead build a **voice-ducked bed** with `scripts/duck_music.py --voice spliced.mp4 --music <raw_track> --out music.mp3` (sidechain-compresses the music under the voice so it dips during speech and recovers in gaps, sets it ~12 dB under the voice). Then in intake.json set `"music_volume": 100` (level is baked into the bed), `"music_offset": 0` (duck_music already trimmed it), and `"master_lufs": -22` so `video_processor.py` masters the whole mix to Rich's level (voice just above a subtle bed). This supersedes flat `music_volume: 12` for real/Suno tracks. If the raw track has a soft intro, probe its first seconds and pass `--offset` to `duck_music.py`.
- **Voice level:** `scripts/sarev_splice.py` loudnorms the spliced voice to **-23 LUFS** as part of the splice. Not -14 — Rich rejected that as too loud. The `master_lufs: -22` master pass lands the delivered mix at that standard.
- **Head trim:** measure leading dead air with `silencedetect` and start the video ~0.15s before the first word (`sarev_splice.py` first segment start does this).
- **Fades:** set **`fade_edges: true`** in intake.json (+ optional `fade_in` 0.4 / `fade_out` 0.6). `video_processor.py` fades video AND audio from/to black at start/end — baked into every render, no separate post pass.
- **NEVER open on an overlay, card or infographic (Rich, 2026-08-24 — this REVERSES the 2026-07-17 rule below).** Frame 0 is Rich's face delivering the hook, full-frame, captions only. **The first overlay lands after the hook beat**, and from there overlays carry the video. Checked against every reference reel: `saraev-refs/ns1` and `ns3` open half-screen (real screen recording on top, face in the bottom strip), `murph-refs/mm1` and `mav-refs/mav1` open full-frame face with a banner pill. **Not one reference ever covers his face completely, at any point.** A full-bleed card that blacks him out is off-grammar everywhere, not just at 0:00.
- **Start the video ON the cut (Rich, token-maxing-shift v2, 2026-07-17 — SUPERSEDED for the opening).** Still true that frame 0 must be a composed state with `"fade_in": 0` and no black fade-up. No longer true that a card should be on screen at 0.0.
- **Overlay cap is 20** (was a SILENT 12 — dropped card11+card12 without any warning on the first 14-window video; now warns when truncating). Count your windows if a late overlay ever goes missing.

### Render input — repoint `raw_video` to `spliced.mp4` before rendering

`video_processor.py` takes BOTH the base video and the voice (`[0:a]`) from the config's `raw_video`. After splicing, update intake.json so `raw_video` points at the workspace `spliced.mp4` — every posted project follows this. If it still points at the raw camera file, the captions/overlays (timed for the spliced edit) get composited over the unspliced take and voice/content mismatch completely ("anthropic-alibaba-distillation" incident, 2026-07-15; the giveaway was final.mp4's audio start_time inheriting the MOV's ~0.7s offset). Verify after render: a frame from final.mp4 must match the same timestamp in spliced.mp4, not the raw file. **Also verify picture↔voice, not just captions↔audio:** the openai-codex-plugins A/V bug shipped twice because every check compared captions to audio and final to spliced — all four agreed while lips were 0.74s off. Ground truth = a mouth tile on final.mp4 at 2–3 word onsets (one-liner in "Splice preflight" above), or template-match final frames at bare-face timestamps back to the RAW file at the wall times the segment map predicts (offset ≤2 frames).

### Splice preflight — probe the raw file BEFORE designing cuts

`ffprobe -show_entries stream=codec_type,start_time <raw>` on every source. iPhone MOVs report audio `start_time` ~0.74–0.76s after video 0.000 — a container ARTIFACT, not real sync (mouth-tile frames prove lips articulate at audio-INTERNAL word times; see `probe_av_offset` docstring in `sarev_splice.py` and memory `project_iphone_mov_audio_offset`). `sarev_splice.py` cuts audio on its internal timeline (`asetpts` before `atrim`), which matches whisper-on-extracted-wav times — so design cuts from whisper/RMS on extracted wavs and everything agrees. Two tells that the offset is in play: (a) the splicer prints a NOTE with the measured gap; (b) whisper full-file times and silencedetect-on-the-container times disagree by that same constant — it is the offset, NOT model drift. After every splice of offset footage, verify lip sync on spliced.mp4 with a mouth tile before building anything downstream:

```
ffmpeg -ss <word_onset-0.4> -i spliced.mp4 -vf "select='not(mod(n,3))',crop=360:280:180:660,scale=180:140,tile=8x2" -frames:v 1 tile.png
```

Lips must be articulating across the tile row where the word is heard. If voice reads ~0.7s BEFORE lips instead, the source really was presentation-synced — compensate by ADDING the probed offset to the VIDEO trim ranges (never by padding audio; the first_pts=0 silence-pad approach shipped a lagging voice on colorado-ai-law, 2026-07-16).

### Splice cut points — verify acoustically, not by Whisper times

**Repeated retakes scramble Whisper word times.** When the raw take contains near-identical repeated sentences (flub → retake), Whisper (base AND small) misassigns word timestamps by up to 3s around the repetition — words get stretched across the between-take silence or attributed to the wrong take ("trump-nsa-ai-eo" 2026-07-15: cut placed from full-file times clipped "AI models" and "right now"; full-file said "right now" ended 33.56, isolated clip showed 34.28). Never place cuts near a retake from full-file word times: transcribe an ISOLATED clip of just that region (±2s, no repetition in the window) and cross-check onsets with an RMS probe / silencedetect. After splicing, ALWAYS re-transcribe spliced.mp4 and diff the text against the intended keep-list — a dropped boundary word means re-splice from raw.

Whisper word-END timestamps underestimate trailing decays by up to ~0.3s. When cutting a segment after a word, never use `whisper_end + fixed_pad`: run `silencedetect` (`noise=-38dB:d=0.06`) on the raw audio around the cut, find where the word's energy ACTUALLY ends, and place the cut inside the measured silence. A clipped word tail cannot be repaired by adding room tone afterward — the only fix is re-splicing from the raw source ("date change" incident, 2026-07-08).

**Soft-onset words read as silence — never cut BEFORE a word from silencedetect alone.** Fricative onsets ("**f**irst?") dip under −32dB and silencedetect reports the word's first ~0.2s as "silence"; a cut placed there decapitates the word (openai-codex-plugins: cut at 53.30 clipped "first?" which actually ran 53.22–53.62). Cross-check the whisper word extent from an isolated-clip transcription, keep ≥0.4s past the previous word's decay, and re-transcribe the JOIN after splicing to confirm the boundary word survived.

**Breathy starts run ~0.4s of inhale before the voiced onset.** Whisper stamps "That's" from the breath; the −40dB voiced onset can be 0.4s later. When tightening a pause INTO such a word, cut at the voiced onset (silencedetect −40dB) minus ~0.15s — cutting at whisper's start keeps the whole breath and the pause stays audible.

**Dead-air pass (mandatory before captions).** Run `silencedetect noise=-40dB:d=0.2` on **spliced.mp4** — the voice-only file; the ducked music bed masks gaps in final.mp4, so measuring there finds nothing. Tighten any mid-sentence gap >0.4s and any sentence-pivot gap >~0.35s by re-splicing the FULL keep-list in one pass (split the segment at the hesitation silence). Rich flags these as "awkward pauses"; zero dead air is the style. An "awkward pause" is often two stacked artifacts: a retake hesitation plus a breathy next-word onset — both invisible to caption-level checks.

### Lip-sync gate (MANDATORY — three shipped desyncs before this existed)

iPhone MOV audio `start_time` metadata is unreliable in BOTH directions (colorado-ai-law 2026-07-17: metadata said 0.757s, true measured offset 0.55s; assuming 0 or assuming 0.757 each shipped a desynced render). The audio-to-video offset must be MEASURED from content, never taken from metadata or eyeballed from frame tiles:

1. Before splicing any raw source: `python scripts/measure_av_offset.py --offset <raw> --windows a-b,a-b` (two dense-speech windows) → set the result as `"av_video_shift"` in splice.json. `sarev_splice.py` shifts only the VIDEO trim ranges; audio stays on its internal (whisper/CTC) timeline so captions and overlay beats are unaffected.
2. After every splice AND after every render: `python scripts/verify_lipsync.py <file> --windows ... --max-lag 0.3` must PASS (|weighted lag| ≤ 0.15s). Windows must match the layout: bare-face stretches use a full-frame mouth crop; card-overlay stretches use the bottom face-strip crop (`360:280:360:1420` at 1080x1920). Ignore windows with corr < 0.1 and windows where hands gesture near the face.
3. Final human check: frame-tile a bilabial plosive ("B"/"P"/"M" word) with captions burned in — lips must be pressed on the closure within ~2 frames of the caption.

**Do every cut in ONE pass, not layered re-cuts.** Trimming an already-exported edit again and again sounds choppy (Rich: "cutting closer in and out is choppy"). Build the whole edit from the clean base in a single `sarev_splice.py` run with the full keep-segment list.

**Prefer a real-silence cut over `faded_tail` — measure first.** faded_tail is a last resort for true zero-gap flow-throughs only. Probe RMS + silencedetect around the kept word's end: if ≥0.3s of real silence exists between its energy end and the next (removed) word's onset, place a normal cut inside that silence and skip the fade/gain. A guessed faded tail both cut early and faded through the word's release ("conversation cut off pretty heavily" — trump-nsa-ai-eo, 2026-07-16).

**Flow-through word → keep a FADED TAIL.** When a cut removes the word immediately after a kept word with NO silence between (keep "Siri **AI**", drop "**and** one…"), the kept word gets clipped and can go inaudible ("can't hear AI" incident, siri-ai-gemini-privacy). There is no silence to cut into — the word only reads WITH its following context. Fix: extend the kept segment ~0.15–0.25s into the removed audio, `fade_out ~0.15s` so the trailing word fades to nothing, small `gain` (1.3–1.6) so the rushed word reads, and EXCLUDE that faded-tail word from captions. `sarev_splice.py` handles this via `faded_tail: true` on the segment.

**Never `apad` the last segment with digital SILENCE.** The end tail must be the raw take's own room tone, carried past the final word — pad with silence and you chop the last word's decay ("comments" ended in a hard −90 dB cliff that cut its trailing "s" — the "clipped comments" incident). Splice with `sarev_splice.py` (its faded tail carries real room tone). If you must hand-splice, cut in the SILENCE just before the closing phrase and replay it complete from the raw source with ~1s of the raw's natural room tone after the last word — do NOT `apad=pad_dur=`. Verify by re-transcribing the tail AND checking the energy decays gradually (raw floor ~−65 dB), not to digital silence.

### Optional burned-in overlays (video_processor.py config keys)

**`callouts` are BANNED — never use them.** (Rich, 2026-07-08: burned-in gold stat text like "IT WILL COMPOUND" is not wanted, ever. The renderer still supports the key for old configs; never author new ones.) If a moment needs a visual punch, build a proper animated HTML card via `rec_card.py`, or use a real screen recording / b-roll instead.

Two lightweight overlay types remain — chapters render via the ASS caption track, logos composite as looped PNG inputs:

```json
"chapters": [
  {"text": "THE EXPANSION", "start": 17.0, "end": 24.5}
],
"logo_overlays": [
  {"file": "<transparent-png>", "timeline_start": 6.0, "timeline_end": 9.0,
   "width": 420, "x": "center", "y": 430}
]
```

- **`chapters`** — small white section label (42pt) top-center, 250ms fade in/out. Use for part/section markers on longer videos.
- **`logo_overlays`** — transparent PNG scaled to `width`, alpha-fades in 0.12s while rising 24px, fades out 0.18s. `x`: `"center"` or px; `y` default 430 (top half). No flash/SFX fires for logos and they don't trigger the face strip.

Choosing: multi-beat animated sequence (timeline, counter, stacked stats) → HTML card via `rec_card.py`; section label → `chapters`; brand mark moment → `logo_overlays`. Never a bare burned-in stat callout.

### Step 5 — Run Pipeline

```powershell
python "C:\Users\richm\.claude\skills\reelforge\pipeline.py" "C:\tmp\reelforge\<slug>"
```

Report all 4 output paths on completion.

### Step 6 — QC gate (MANDATORY after every render)

```powershell
python "C:\Users\richm\.claude\skills\reelforge\scripts\verify_render.py" --config intake.json
```

Never deliver on a failing gate; never re-deliver after a re-render without re-running it (anthropic-47b-revenue shipped a lagging caption track and a dead punchline card while every eyeball check passed, 2026-07-17). The gate checks: decode integrity, stream start_times, duration, mastered LUFS, final↔spliced audio+video shift, caption anchors vs acoustic onsets, per-card beats, and lips onsets. Requirements:

- Every designed card's `screen_recordings` entry carries `"beats": [output_ts, ...]` — WORD-LOCKED beats only (slams, counters, reveal lines). Decorative micro-elements (an 84px arrow) register ~0.02 on card-region motion and false-fail the gate.
- Pair it with the lip-sync gate above (`verify_lipsync.py`) — they catch different failure classes: verify_render catches captions/beats/mix drift; verify_lipsync catches source-offset desync.
- Finish with 2-3 spot frames at word midpoints: the burned caption must show the word being spoken.

**Diagnosing "the video is not lining up with the audio":** that phrase can mean captions (most common — whisper times lag 0.15-0.4s mid-sentence; check ASS starts vs forced-aligned times), card beats (an animation firing late/never inside its window; frame-diff the card region), or true lip desync (rarest; verify_lipsync). Measure before re-splicing — on anthropic-47b-revenue the lips were perfectly in sync and the real causes were whisper caption lag + one dead card; a guessed offset "fix" would have broken sync.

---

## Alternate Flow — Pre-filled intake.json

If user drops an `intake.json` (generated via `intake_prompt.md`), skip straight to Step 5:
```powershell
python "C:\Users\richm\.claude\skills\reelforge\pipeline.py" "<path_to_intake.json>"
```

---

## Output Files

| File | Description |
|---|---|
| `final.mp4` | Edited 9:16 video, h264, 192k aac |
| `thumbnail.png` | 1080×1920 branded thumbnail, background removed headshot |
| `instagram_caption.txt` | Platform-native IG caption with hashtags |
| `linkedin_caption.txt` | LinkedIn post, no hashtags |

---

## Script Locations

| Script | What it does |
|---|---|
| `pipeline.py` | Orchestrator — calls all scripts in order |
| `scripts/sfx_processor.py` | Scales SFX MP3 → flash_sfx.wav |
| `scripts/music_gen_suno.py` | **PREFERRED** — real AI music via Suno (`--out --prompt --style`). Rich prefers this over the synth. |
| `scripts/music_gen.py` | Fallback only — procedural synth (`--config intake.json`); sounds artificial AND uses a fixed random seed, so re-running yields the IDENTICAL track (can't "regenerate" for variety — use Suno) |
| `scripts/duck_music.py` | Builds the voice-ducked music bed (`--voice spliced.mp4 --music <raw> --out music.mp3`); run after splice, before render — see Audio finishing |
| `scripts/rec_card.py` | Records an animated HTML overlay card at **1080×960** (half-screen slot, the nick-sarev default) — `--html X --out Y --secs N`; the page must define a `start()` JS function. Prints **`SCHED_AT`** — the measured moment `start()` fired in the output (corner-marker method). **Set `source_start` from SCHED_AT, never guess**: capture-to-`start()` latency varies 0–2.6s per run (worst under parallel recording load; the "it just might." card shipped DEAD because its schedule ran 2.6s late and every beat landed after the window — anthropic-47b-revenue, 2026-07-17). Record beat-critical cards serially. |
| `scripts/rec_card_full.py` | Same but **1080×1920** — only for an opt-in full-screen designed card (a 1080×960 card in a full_screen slot gets black bars) |
| `scripts/sarev_splice.py` | Single-pass, silence-aligned multi-cut splicer (`--config splice.json`): per-segment fade/gain, `faded_tail` support, −23 LUFS voice loudnorm, word remap → `spliced.mp4` + `*_words.json` |
| `scripts/make_sarev_ass.py` | Authors the nick-sarev single-word dual-font caption `.ass` from a words json (`--words --out [--emph --dark-windows --center-windows]`); `--center-windows` = half-screen overlay ranges → captions render mid-screen there (standing rule, see Step 2) |
| `scripts/measure_first_paint.py` | Prints each card's first-paint time — a LOWER BOUND only; first paint ≠ schedule start (a card measured 0.1s first-paint while `start()` fired at 2.6s). Use rec_card's `SCHED_AT` for `source_start`. |
| `scripts/align_words.py` | **Caption timing standard** — CTC forced alignment of the known transcript to the spliced voice (`--video --words --out [--expand]`); see Step 2 |
| `scripts/verify_render.py` | **Mandatory post-render QC gate** (`--config intake.json`): decode integrity, start_times, duration, mastered LUFS, final↔spliced audio+video shift, caption anchors vs acoustic onsets, per-card beat + mid-window animation checks (add `"beats": [output_ts,...]` to each card's screen_recordings entry), lips-onset probe. Never deliver on a failing gate. |
| `scripts/video_processor.py` | ffmpeg: cuts, overlays, captions, mixes audio → final.mp4 |
| `scripts/thumbnail_maker.py` | Playwright + rembg → thumbnail.png |
| `scripts/caption_writer.py` | Claude API → Instagram + LinkedIn captions. **Social copy standard: write via hookcraft + captioncraft, and EVERY caption block must pass `captioncraft/scripts/caption_lint.py --platform <p>` (exit 0) before delivery — canonical ban list + emoji policy (IG 2-4, LinkedIn 0-1, YT 1-2)** |
| `scripts/rec_prompt.py` | Playwright → animated prompt-input interface recording |
| `scripts/rec_skills.py` | Playwright → animated skill-selector grid recording |
| `scripts/rec_aiops.py` | Playwright → animated AI pipeline/workflow recording |
| `scripts/retime_words.py` | **Caption timing standard** — windowed silence-anchored word times on spliced.mp4 (`--video --out [--initial-prompt "names"]`); snaps in-silence onsets; hand-fix product names in the output json before make_sarev_ass. **Also repair zero-width words** (whisper emits w.start==w.end tokens, e.g. "which" in fast speech): two ASS events at the same instant render as a STACKED two-word caption (anthropic-47b-revenue, 2026-07-16). Enforce min 0.08s per word by extending into the preceding gap (or shifting the next word's start) before make_sarev_ass |
| `scripts/serve_spa.py` | SPA history-fallback static server (`--root <dist> --port N`) — for recording the local PromptAnything build (plain http.server 404s client routes) |
| `scripts/rec_pa_hero.py` | Real PA landing-hero recording at 1080×960 (`--out [--base-url] [--type-text] [--hold-secs]`): cookie pre-accept, frames the prompt box, live-types, prints MARK lines for source_start — see "PromptAnything overlays" |

Brand configs: `brands/prompt-anything.json`, `brands/bishop-ai.json`
AI intake prompt: `intake_prompt.md` (paste into any LLM to generate intake.json)

---

## Playwright Screen Recordings

**All overlay recordings are generated with Playwright** — no real screen capture needed. Write an animated HTML page, record it headless, convert webm→mp4. This means overlays are always on-brand, perfectly timed, and reproducible.

### How to generate a recording

```python
# Run any rec_*.py script with --out path:
python scripts/rec_prompt.py --out workspace/rec_prompt.mp4
python scripts/rec_skills.py --out workspace/rec_skills.mp4
python scripts/rec_aiops.py --out workspace/rec_aiops.mp4
```

Run in parallel with `&` + `wait` in bash.

### Full-screen vs split-screen recordings

Set `"full_screen": true` in the screen_recordings entry when the source footage would look bad in the bottom face strip (e.g., shot landscape, wrong orientation, or face not needed):

| Mode | `full_screen` | Overlay size | Face strip |
|---|---|---|---|
| Full-screen | `true` | 1080×1920 | Hidden |
| Split-screen | `false` (default) | 1080×960 | Shown at bottom |

Record at the matching viewport:
- Full-screen scripts: `viewport={"width":1080,"height":1920}`
- Split-screen scripts: `viewport={"width":1080,"height":960}`

### Writing a new Playwright recording script

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    ctx = await browser.new_context(
        viewport={"width": 1080, "height": 1920},   # or 960 for split
        record_video_dir=tmp_dir,
        record_video_size={"width": 1080, "height": 1920},
    )
    page = await ctx.new_page()
    await page.set_content(HTML, wait_until="networkidle")
    await page.wait_for_timeout(6000)   # animation duration in ms
    webm = await page.video.path()      # must await — async API
    await ctx.close()
    await browser.close()
# Convert webm → mp4
subprocess.run(["ffmpeg","-y","-i",webm,"-c:v","libx264","-pix_fmt","yuv420p",out_mp4], check=True)
```

Key gotcha: `page.video.path()` is a coroutine — always `await` it.

### Recording real articles synced to narration

For overlays of live article pages (anthropic.com, news sites) where scrolls and highlights must land on the words being narrated:

1. **Probe the page text first** — dump `h1/h2/h3/p` innerText via Playwright and confirm the exact phrases the narration references still exist. Articles get rewritten; a rec script that captured the right content last week may point at a completely different page today. If the phrases are gone, find the page that has them (e.g. the original launch post) instead of recording mismatched content.
2. **Map the timeline**: `recording t = narration t - timeline_start + source_start`. Schedule every scroll/highlight beat from the caption timestamps.
3. **Styled-check every load.** Require the article's actual headline text in the `<h1>` (rejects Cloudflare "Performing security verification" challenge pages AND error pages) and that CSS applied (`getComputedStyle(h1).fontFamily` not Times, `document.styleSheets.length > 1` — pages sometimes half-load with no stylesheet and look broken on camera).
4. **Beat Cloudflare**: warm the cache with a throwaway non-recording context first, use a real Chrome UA + `--disable-blink-features=AutomationControlled`, back off 8s+ between retries. Rapid repeated loads of the same page are what trigger the challenge; if challenged, cool off 60-90s before rerunning.
5. **Print `T_SCHED`** (`time.monotonic()` from recorded-context creation to schedule start) and set `source_start = T_SCHED + first-beat offset`. Load time varies run to run; never hardcode source_start for a live-site capture. Verify with extracted frames.
6. **Eased scroll, never native smooth**: `window.scrollTo({behavior:'smooth'})` whips through long jumps in a few hundred ms. Animate scroll manually with rAF + ease-in-out over ~2s per move:
```js
window.__scrollToPhrase = (phrase, delayMs, offset, durMs) => setTimeout(() => {
    const n = window.__findTextNode(phrase);   // TreeWalker over text nodes
    if (!n) return;
    const target = n.parentElement.getBoundingClientRect().top + window.scrollY - (offset || 240);
    const y0 = window.scrollY, dist = target - y0, t0 = performance.now(), dur = durMs || 2000;
    const ease = p => p < .5 ? 2*p*p : 1 - Math.pow(-2*p + 2, 2) / 2;
    const step = t => { const p = Math.min(1, (t - t0) / dur);
        window.scrollTo(0, y0 + dist * ease(p)); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
}, delayMs);
```
7. **Gold phrase highlights**: find the text node containing the phrase, wrap the substring with `Range.surroundContents(span)`, animate a gold (#E0B848) background sweep via `background-size 0%→100%` transition. Fall back to an outline box on the parent element if the range spans elements. Working reference: any `rec_*_sync.py` in a recent project's `source/`.

### Animated overlay cards (stats / timelines / CTAs)

Cover narration stretches that have no natural screen capture with brand-styled animated HTML cards recorded via `scripts/rec_card.py --html card.html --out card.mp4 --secs N` (these are full designed cards — NOT the banned burned-in `callouts` text):
- **Default style = `styles/broadcast-light`** (light cream bg, navy broadcast kicker pills, gold accent bars, `PROMPT ANYTHING` footer, gold-feather divider). Each card `<link>`s `styles/broadcast-light/cards.css` and uses its shared classes — see `styles/broadcast-light.md`. This is the on-brand light look; use it over the old dark `#000814` cards. Pair with `caption_position: center`.
- **Reusable logos:** `assets/logos/` holds transparent, cream-legible company logos (`openai`, `nvidia`, `google`, `gemini`, `apple`, `amazon`). Drop them onto cards (chip-maker timeline, X-vs-Y face-off, stat subject) instead of re-sourcing.
- Page defines `start()`; inside it, `setTimeout` delays = `(narration t - timeline_start) + source_start` per element (rec_card starts capture ≈ when it calls `start()`, so with `source_start: 0.5` a delay of 300ms lands right at window start).
- Card types proven to work: date timeline (node → line-draw → node → counter), stacked stat rows sliding in per narration beat, CTA card (icon pop → big gold keyword → subtitle). Number counters: rAF count-up over ~1.2-1.4s ending right as the narrated number is said.
- Record `secs` ≥ window + source_start + 2 so the clip never freezes early.

### Smooth page pans — screenshot + programmatic crop, never live scroll

Live Playwright scrolling judders on playback. To pan a page: take a FULL-PAGE screenshot, then render the pan with ffmpeg on the still — `crop=1080:960:0:'<end_y>*(0.5-0.5*cos(PI*t/<dur>))'` (single easeInOutSine across the whole clip) at the composite frame rate. Verify smoothness by template-matching a few frames back to the source image (constant px/frame within ~1px). Live scrolling is acceptable only when the page must visibly interact (typing, clicks).

### Avoiding cookie banners in real-site recordings

Banners appear AFTER `networkidle`, so clicking them mid-recording leaves them visible. Fix: pre-accept in a non-recording context, save storage state, then record with it pre-loaded:

```python
# Step 1: accept cookies (no recording)
setup_ctx = await browser.new_context(viewport={"width": 1080, "height": 1920})
setup_page = await setup_ctx.new_page()
await setup_page.goto(url)
await setup_page.wait_for_load_state("networkidle")
await setup_page.wait_for_timeout(2000)
await setup_page.click("text=Accept all", timeout=4000)
storage = await setup_ctx.storage_state()
await setup_ctx.close()

# Step 2: record with cookies pre-accepted — banner never appears
ctx = await browser.new_context(
    viewport={"width": 1080, "height": 1920},
    storage_state=storage,
    record_video_dir=tmp_dir,
    record_video_size={"width": 1080, "height": 1920},
)
```

### PromptAnything overlays — ALWAYS the real product, never a designed card

Rich (2026-07-16, openai-codex-plugins): the PA overlay must be real PromptAnything branding — a live recording of the actual product, not a brand-colored HTML card. Recipe (`scripts/rec_pa_hero.py` does all of this):

1. Prod `promptanything.io/prompt-studio` redirects to `/auth` (login-gated) — do NOT try to log in. Serve the local build instead: `python scripts/serve_spa.py --root "C:\Users\richm\Desktop\promptanything-live\dist" --port 8082` (SPA history-fallback static server; a plain http.server 404s the client routes). Fresh port per the PA local-deploy memory; kill the server when done.
2. The public LANDING page has the branded prompt box: quill logo, "Build expert AI prompts in minutes", mode chips (Agent…Voice/TTS), red Generate button.
3. Record at 1080×960: cookie pre-accept in a throwaway context ("Accept all"), scroll the textarea into frame (top −200px), click it, live-type a TOPIC-RELEVANT prompt (~45–48ms/char — echo an example already used in the video's other overlays; repetition with variation reads as intentional), hold ~7s. The caret blink keeps the held shot alive.
4. The script prints `MARK` lines (framed / type_start / type_end); set `source_start` ≈ `type_start − 0.35` so typing begins right on the "builds your prompts"-class narration beat.

### Fixing sideways face from iPhone footage

iPhones store all video as landscape pixels + rotation metadata tag. ffmpeg auto-applies this tag even in filter_complex. So:
- **Portrait footage**: already upright after auto-rotate → `scale=1080:1920` only, no transpose
- **Landscape footage**: stored landscape, auto-rotate is irrelevant → `crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920` (center-crop to 9:16, no transpose)

Never apply `transpose=1` to iPhone footage without first extracting a raw frame to confirm it's sideways — if it looks correct already, no transpose is needed.

---

## Thumbnail headshots — crop the pose cell yourself

`thumbnail_maker.py`'s grid auto-detect fails on the citadel reference images: it treated the 2304×1844 3×2 pose grid as 1×1, so rembg processed the WHOLE grid and rendered a blurry smudge where the person should be (openai-codex-plugins, 2026-07-15). The small reference screenshots (215–440px) are also too low-res for a 1080×1920 thumbnail. Working flow:

1. `python C:\Users\richm\.claude\skills\citadel\scripts\pick_pose.py` → `<grid_path>\t<pose_index>` (never repeats a pose; ledger-backed).
2. If the pick is a tiny screenshot (<600px), re-run until it lands on a real grid (big-grid cells are 768×922 — the only refs big enough).
3. PIL-crop that cell to a standalone PNG (3 cols; index → col = n%3, row = n//3) and set it as `thumbnail.headshot` with `"headshot_cell": [0, 0]`.
4. Render, then ALWAYS view thumbnail.png: the person must be present, sharp, and match the avatar baseline (brown hair, stubble — never the blond rich_reference face).
5. `pick_pose.py --commit <grid_path> <pose_index>` so the pose is never reused.

## Style standard: nick-sarev.md §14-15 govern every sarev video

Before authoring cards or a script for any talking-head Reel/Short, read `styles/nick-sarev.md` §14 (motion spec) and §15 (script formula), evidence in `styles/saraev-refs/`:
- **Cards are info-in-motion**: author every card with 3-5 sequential mutation beats (bars fill, rows pop, text types, checkmark lands) so something changes every 0.8-1.5s; a card that animates in once and then sits is below standard.
- **Default cutaway techniques** (in priority order): dressed real screenshots w/ orange highlights + push-in, progressive-build diagrams/charts, DOF blur montage for enumerations, logo beats, metaphor micro-animations, cursor-as-actor typing/clicking. Veo3 cinematic b-roll is the Rich-approved variant, not the default.
- **Lockups**: accumulating serif/sans multi-line lockups at hook, pivots, and the CTA (`comment "Keyword"`) — flow captions stay strict one-word.
- **Script**: word budget = 4 x target seconds, zero dead air, LIST/PROCESS/DISCOVERY shapes, comment-keyword CTA.

## Troubleshooting

**ffmpeg filter error** — check stderr in terminal; most common cause is a bad file path or mismatched timestamps
**rembg slow** — normal, first run downloads model (~175MB); subsequent runs are fast
**caption timing off** — re-run caption auto-timing with adjusted duration; or edit intake.json captions array directly
**thumbnail seam** — ensure `bg_color` in brand config exactly matches the body background in thumbnail_maker.py


<!-- design-bridge:start -->

## Design bridges: consult before building

Three bridge skills sit under this one. None of them produces deliverables; this
skill still owns the output.

1. **`design-extract`** — MEASURED tokens from one named site, repo, or project.
   When a design system is active it wins on layout, spacing, type scale,
   components, motion and interaction states.
2. **`design-intel`** — RECOMMENDED generic values (layout, spacing, UX,
   accessibility, chart selection, font pairing) where brand and the active
   system are silent.
3. **`design-sources`** — external craft rules plus the deterministic gate. Read
   `C:/Users/richm/.claude/skills/design-sources/references/video-motion.md` for this medium.

**Precedence:** explicit instruction in the request > `branding-agent` (colours,
fonts, logo) > active extracted system > style preset (`brutalist-skill`,
`minimalist-skill`) > `design-intel` > skill defaults. Measured beats
recommended where both cover a decision. Borrow ratios and structure from an
extracted system; keep brand colours and typefaces from `branding-agent`.

`design-sources` is a **gate, not a precedence layer**: it runs before shipping
no matter which layer supplied the values.

3. **No gate here**, and the adapter is deliberately narrow. Rich's overlay grammar (Saraev / Murph / Mav, safe bands, plate rules, cut pacing, no-zoom) is locked and is **not** open to revision by an external web-design source. Share correctness, never share grammar.

**Brand outranks both.** Bishop AI / Prompt Anything / BOB colours and typefaces
come from `branding-agent` and `tokens.json`, never from an external source.
Verified: Bishop AI's own palette trips two Impeccable rules (`cream-palette` on
warm-white `#F9F6F0`, `overused-font` on Open Sans); both are waived in
`C:/Users/richm/.claude/design-sources/brand-overrides/config.json` and reported as overridden
rather than failed. Do not "fix" brand to satisfy a detector.

<!-- design-bridge:end -->
<!-- design-extract:connector v1 -->

---

## Extracted Design System

**First, scan the request for the literal phrase "full <name> system"** (e.g. "full linear
system"). Near-miss phrasings — "use Linear's colors", "make it look like Linear", "match
Linear's branding" — do NOT count. Only the literal phrase.

- **Phrase present** -> that extracted system supersedes `branding-agent` for this one
  deliverable. Read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`, and use its
  colors and font families directly.
- **Phrase absent** -> resolve the active system the normal way:
  1. A system named in the request ("in the linear system", "build this like Stripe"), or a
     `.design-system` marker file in the working folder.
  2. If found, read `~/.claude/design-systems/<slug>/DESIGN.md` and `tokens/`.
  3. **BORROW** from it: layout, spacing grid, type scale ratios, component patterns,
     motion, easing, interaction states.
     **KEEP from `branding-agent`:** Bishop AI / Prompt Anything colors, font families, logo
     treatment.
  4. Nothing active -> proceed exactly as normal. This block adds no default behavior.

Measured beats recommended: where an active system covers a decision, it outranks
`design-intel`. Where it is silent — accessibility, chart choice, breakpoints —
`design-intel` is still the answer.

**This skill emits motion.** Read `references/ANIMATIONS.md` and `references/INTERACTIONS.md` for real keyframes, durations, and easing curves rather than inventing timings.

Full contract: `~/.claude/skills/design-extract/references/consumption.md`
<!-- /design-extract:connector v1 -->
