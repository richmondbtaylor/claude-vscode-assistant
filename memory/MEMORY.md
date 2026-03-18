# Claude Memory — Bishop AI / Richmond Taylor

## Branding & Documents
- **Always include the Bishop AI logo** in onboarding documents and client-facing deliverables
- Logo file: `C:/Users/richm/Downloads/Bishop AI.png`
- Embed it as base64 in HTML docs so it's self-contained (use Node.js to encode: `fs.readFileSync(...).toString('base64')`)
- Logo placement: top of the header, above the eyebrow text, sized ~64px tall

## Key File Paths
- Bishop AI logo: `C:/Users/richm/Downloads/Bishop AI.png`
- Projects output dir: `C:/Users/richm/.claude/projects/`

## User Preferences
- Communication style: direct, concise - no filler
- No emojis unless asked
- **No em dashes** ever in any output (use hyphens or rewrite the sentence instead)
## Deliverable Format Rules
- [feedback_always_pdf_not_html.md](feedback_always_pdf_not_html.md) - Always output PDF (never HTML or .md) for pitches/presentations; auto-upload to Google Drive

## Writing Rules
- [feedback_no_em_dashes.md](feedback_no_em_dashes.md) - Never use em dashes in any output; use hyphens or rewrite instead
- [feedback_human_first_ai_framing.md](feedback_human_first_ai_framing.md) - Human-first always: never talk about firing, replacing, or eliminating people/roles. AI amplifies humans, never substitutes them. All content must be rooted in viral AI topics.

## Skills
- **ig-tiktok-scan** (`~/.claude/skills/ig-tiktok-scan/SKILL.md`) - IG/TikTok viral content intelligence + weekly Reel/TikTok batch generation. Trigger: `/viral-content-batch`, `/analyze-and-generate`, `/ig-tiktok-scan`, or any request to find viral patterns and generate short-form content packages in Rich's voice
