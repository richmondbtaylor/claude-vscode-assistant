# Branding Kits Plan

## Context
User has two brands — Bishop AI and PromptAnything.io — and wants complete branding kits as Claude skills. The Bishop AI skill (`skills/bishop-brand/SKILL.md`) exists with colors and fonts but has no logo references. PromptAnything has no branding skill at all. User will upload logo files and has a pitch deck PDF for PromptAnything color/font extraction.

---

## Step 1 — Save uploaded logos

When user uploads logo files, save them to a dedicated assets folder:
- `C:\Users\richm\.claude\assets\logos\bishop-ai\` — Bishop AI logos
- `C:\Users\richm\.claude\assets\logos\promptanything\` — PromptAnything logos

Accept any format: PNG, SVG, JPG. Keep original filenames but note variants (dark bg, light bg, icon-only, full wordmark).

---

## Step 2 — Extract PromptAnything brand specs from PDF

PDF: `C:\Users\richm\.claude\2026-03-13 promptAnything.io - Keynote Pitch Deck.pdf`

Since `pdftoppm` is unavailable, use Playwright to render and extract:
- Hex color codes
- Font names
- Logo appearance / layout description
- Brand voice / tone (from copy in the deck)

---

## Step 3 — Create PromptAnything branding skill

Create `C:\Users\richm\.claude\skills\promptanything-brand\SKILL.md` mirroring the structure of `bishop-brand/SKILL.md`:
- Color palette table with hex + RGB + usage rules
- Typography stack with role/primary/fallback
- Smart color selection rules
- python-pptx `RGBColor` code block
- AI image generation prompt block
- Logo reference section with file paths to `assets/logos/promptanything/`
- Brand voice + banned phrases (shared or brand-specific)

Also create `skills/promptanything-brand.md` trigger file (the skill descriptor).

---

## Step 4 — Update Bishop AI branding skill

Edit `C:\Users\richm\.claude\skills\bishop-brand\SKILL.md` to add:
- **Logo section** with file paths to `assets/logos/bishop-ai/` variants
- Logo usage rules (when to use dark vs light version, minimum size, clear space)

---

## Step 5 — Update skill trigger descriptor

Update `C:\Users\richm\.claude\skills\bishop-brand.md` (the trigger file) description to mention logos.

Create `C:\Users\richm\.claude\skills\promptanything-brand.md` trigger file.

---

## Verification

- `/bishop-brand` skill loads and includes logo file paths that resolve on disk
- `/promptanything-brand` skill loads with accurate colors/fonts from the PDF
- Both skills have a logo section pointing to real files in `assets/logos/`
