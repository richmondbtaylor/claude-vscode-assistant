# AIOS Setup — Engagement Overlay Edit (Design)

Date: 2026-08-10
Source: `C:\Users\richm\OneDrive\Desktop\AI Sales Course\AIOS Setup.mp4`
(9:02.65, 2560x1440, 30fps, embedded audio)

## Goal

Increase retention on the long talking moments of the AIOS Setup tutorial by
covering them with full-screen animated graphic cards in the Bishop AI light
brand. Demo moments stay untouched. Overlays only: no trims, no cuts, no music,
no SFX, audio track byte-identical, output duration identical to source.

## Measured structure (talking vs demo)

Boundaries were measured from extracted frames and the Whisper transcript, not
estimated. Values below are locked unless re-measurement during implementation
contradicts them (re-measure at 2s granularity around each boundary before
compositing).

| Window | Content | Type |
|---|---|---|
| 0:00.0–~0:23 | Hook + promise | Talking head |
| ~0:23–2:19 | IDE setup demo (Antigravity, OpenCode, Node, aiossetup.netlify.app) | Screen demo — untouched |
| ~2:19–3:04 | Orchestrator concept | Talking head |
| 3:04–7:21 | PromptAnything + Antigravity demos | Screen demo — untouched |
| 7:21.6–~8:11 | Three tips, voiced over vertical result-video on screen | Covered by tip cards (approved) |
| ~8:11–9:02 | Outro, share + comment CTAs | Talking head |

## Overlay inventory

All times are seconds from source start. Cards hard-cut in and out. Voice
continues underneath. Each in/out point and each mutation beat is tied to the
transcript word it lands on.

### 1. Promise card — 12.7 to 22.6 (~10s)
Face holds for the two hook questions (0.0–12.7). Then full-screen card:
- Beat 1 at 12.7: "Build your own AI Operating System"
- Beat 2 at 16.4: adds "Become a master prompt engineer in minutes"
- Out at 22.6, exactly on the cut to the screen recording.

### 2. Buildables card — 141.2 to 157.6 (~16s)
Over "any agent, employee, workflow, web application, image, video, whatever
you want": icon grid, each buildable pops in on its spoken word
(agent, employee, workflow, web app, image, video), closing beat at ~148.6
introduces promptanything.io as the way prompts get built.

### 3. Face break — 157.6 to 163.2 (~6s)
No overlay. Rich on camera for "our first and most important skill... our
orchestrator agent." Keeps the block from being wall-to-wall graphics.

### 4. Orchestrator diagram card — 163.2 to 184.0 (~21s)
Progressive animated diagram:
- 163.2–176.2: "Your idea" node → Orchestrator node → routes to "the most
  efficient way to complete the task"
- 176.2–183.0: skills fan out under the Orchestrator, then sub-skills fan out
  under skills ("even sub-skills below those skills")
- Out at 184.0 on the cut back to the demo ("So let's get started").

### 5. Tip cards — 441.6 to 491.2 (~49s)
Covers the on-screen vertical result-video (approved). Four beats:
- 441.6: section header "3 tips for building an AI Operating System"
- 445.0: Tip 1 — "Be thorough. Speak to your AI the way it likes to be spoken
  to." (mentions PromptAnything)
- 454.2: Tip 2 — "Don't understand something? Ask it to explain like you're
  five. Step by step. Foolproof."
- 470.1: Tip 3 — "Not satisfied? Demand a full audit and internet research for
  better options."
- 481.9: recap — all three tips stacked
- Out at 491.2 when the face returns for the outro.
Within each tip, sub-elements animate every 1.0–1.5s so nothing sits static.

### 6. End CTA card — 526.4 to 541.9 (~15.5s)
Face holds 491.2–526.4 (personal outro stays personal). Then:
- 526.4: "Share this with the masses"
- 536.9: joins "Comment: what AI skill did you build today?"
- Card runs to end of video (541.9→542.65 tail freeze is fine).

## Card design system

- Bishop AI light brand: light background as primary foundation, brand
  typography and accent colors taken from the slideforge / course-builder
  design system (single palette across all 6 cards).
- Copy rules: no em dashes, no invented acronyms, no AI-lingo banned phrases.
  Card copy uses the words from the voiceover, tightened, never paraphrased
  into new claims.
- Logos: circular logos clipped with border-radius 50%, no border ring.
- No people on cards, no glow effects behind subjects.
- Motion: GSAP-animated HTML. A visible change (element entering, highlight,
  progress) at least every 1.5s on every card. No camera shake. Hard cut in
  and out (no swoosh SFX because the audio track is untouched this pass).

## Pipeline

1. **Boundary re-check:** extract frames at 2s granularity around each in/out
   point; adjust to the true cut frame. Measure, never estimate.
2. **Author cards:** one HTML page per card, GSAP timelines keyed to the beat
   offsets above (offsets relative to card start).
3. **Record cards:** Playwright screen-record each card at 2560x1440, 30fps.
   Known defect: rec-card/Playwright clips run 7–13% time-compressed. Measure
   each clip's true duration and setpts-stretch to wall-clock before use.
4. **Composite:** single ffmpeg pass, one overlay filter per card with
   `enable='between(t,in,out)'`. Video re-encodes; audio stream is stream-copied
   (`-c:a copy`) so it is untouched.
5. **Verify (hard gate):** automated script extracts frames at every overlay
   in/out boundary ±0.5s and asserts card presence/absence; extracts one frame
   per mutation beat and asserts the expected element is visible; asserts
   output duration equals source duration and audio stream is a copy. Edit does
   not ship until the gate passes.

## Output

- `AIOS Setup - overlays.mp4` next to the source file (source never
  overwritten), 2560x1440, 30fps, 9:02.65, original audio.
- Verification report (boundary frame grid) for review.

## Out of scope

- Trims (including the 50s outro), the 8:08 possible misspeak ("strong,
  terrible things"), music bed, SFX, captions, speed-ramps inside demos,
  thumbnail, social copy. Flagged for a possible finishing pass later.
