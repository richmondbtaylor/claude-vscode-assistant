# Claude Video Design — Install

## What you're installing

- **video-use** (browser-use/video-use) — the editing engine and Claude Code skill
- **HyperFrames** (heygen-com/hyperframes) — HTML-to-video motion graphics renderer
- **FFmpeg** — core video processing
- **ElevenLabs Scribe** — word-level transcription with filler detection

---

## Steps

### 1. Clone video-use

```bash
git clone https://github.com/browser-use/video-use ~/Developer/video-use
cd ~/Developer/video-use
pip install -e .
```

### 2. Install HyperFrames

```bash
npm install -g hyperframes
# verify
npx hyperframes --version
```

### 3. Install FFmpeg

```bash
# Windows (via winget or chocolatey)
winget install ffmpeg
# or
choco install ffmpeg

# verify
ffmpeg -version
ffprobe -version
```

### 4. Install Manim (optional — for data viz animations)

```bash
pip install manim
```

### 5. ElevenLabs API key

Get a key at https://elevenlabs.io/app/settings/api-keys

```bash
echo "ELEVENLABS_API_KEY=your_key_here" > ~/Developer/video-use/.env
chmod 600 ~/Developer/video-use/.env
```

Verify:
```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "xi-api-key: $(grep ELEVENLABS_API_KEY ~/Developer/video-use/.env | cut -d= -f2)" \
  https://api.elevenlabs.io/v1/user
# 200 = good
```

### 6. Register video-use skill with Claude Code

```bash
cd ~/Developer/video-use
npx skills add browser-use/video-use
```

Or manually — add the SKILL.md path to your Claude Code skills config.

### 7. Register HyperFrames skills with Claude Code

```bash
npx skills add heygen-com/hyperframes
```

This installs:
- `hyperframes` — composition authoring
- `hyperframes-cli` — init, lint, preview, render, transcribe, tts
- `gsap` — animation API reference

### 8. Verify end-to-end

```bash
# Drop a test video in a folder
mkdir ~/test-video
cp /path/to/test.mp4 ~/test-video/
cd ~/test-video
claude
```

In the session: `> edit this into a clean cut`

Expected: strategy proposed, awaiting confirmation.

---

## Cold-start checklist (every new session)

- [ ] `ELEVENLABS_API_KEY` in env or `.env`
- [ ] `ffmpeg` + `ffprobe` on PATH
- [ ] `npx hyperframes --version` responds
- [ ] Python deps installed in video-use (`pip install -e ~/Developer/video-use`)
