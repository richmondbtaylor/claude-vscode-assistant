# Plan: Sync ai_automation GitHub → local .claude

## Context
The private GitHub repo `richmondbtaylor/ai_automation` contains the same research bot skills that live in `C:\Users\richm\.claude`. Changes were made on GitHub (primarily: switching hardcoded `C:/Users/docch/` paths to portable `Path.home()` per-skill env paths, plus some feature and bug fixes). This plan syncs those changes back into local `.claude`.

---

## What Changed on GitHub (vs local)

### Global pattern across all files
Every modified file on GitHub has:
- Added `from pathlib import Path`
- Changed `load_dotenv("C:/Users/docch/.claude/security/.env")` → `load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "{skill-name}.env")`

### Substantive content changes (beyond env paths)

| File | What changed |
|------|-------------|
| `skills/bishop-research-agent/main.py` | Adds Upwork polling cycle (`import upwork_monitor` + loop block) |
| `skills/bishop-research-agent/setup_reddit_app.py` | Email default: `docchond@docchondbishop.com` → `richmond@richmondbishop.com` |
| `skills/braincx-research-agent/enrich_sheet.py` | Fixes typo `endocchent`→`enrichment` throughout; adds Apollo fallback block for DM enrichment |
| `skills/Client Skills/braincx-research-agent/enrich_sheet.py` | Adds Apollo fallback block (~36 lines) + different env file name (`braincx-client-research-agent.env`) |
| `ClawdBot-LinkedIn/main.py` | `'docchond'` → `'richmond'` in author checks; failed comment now marks URL processed (no retry) |
| `ClawdBot-LinkedIn/linkedin_commenter.py` | Large: removes `_auto_login()`, replaces with `_wait_for_manual_login()` (browser window); session dir `linkedin_session_v2` → `linkedin_session` |
| `skills/clawdbot-feed/linkedin_commenter.py` | Chrome profile: `feed_session_v4` → `chrome_profile`; login method: `type()` → `fill()`; simplified (removes periodic nav check) |
| `skills/whatsapp-linkedin-pod/main.py` | `'docchond'` → `'richmond'` in two author checks |

### New folder to create locally
- `skills/radley-research-agent/` — entirely new agent (15 files), does not exist locally

### Special case — conquer/backfill_enrichment.py
- GitHub has old hardcoded `C:/Users/docch/` path
- Local has malformed: `load_dotenv(dotenv_path=...).parent / ".env")` (syntax error — result of `load_dotenv()` doesn't return Path)
- **Neither is correct** — fix to use the correct portable pattern matching all other files:
  `load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "conquer-social-prospecting.env")`

### Local-only files — do NOT touch
- `skills/bishop-research-agent/upwork_monitor.py` — exists locally, not pushed to GitHub; referenced by the updated `main.py`
- `skills/bishop-research-agent/setup_logins.py` — exists locally, not on GitHub

---

## Implementation Approach

Clone the repo to a temp dir, then copy files over individually.

### Step 1 — Clone repo to temp
```bash
git clone https://YOUR_GITHUB_TOKEN@github.com/richmondbtaylor/ai_automation.git C:/tmp/ai_automation_sync
```

### Step 2 — Copy all changed files (GitHub → local)

Files to overwrite (26 files):

**bishop-research-agent:**
- `skills/bishop-research-agent/main.py`
- `skills/bishop-research-agent/reply_agent.py`
- `skills/bishop-research-agent/update_sheet_headers.py`
- `skills/bishop-research-agent/setup_sheets.py`
- `skills/bishop-research-agent/setup_reddit_app.py`

**braincx-research-agent:**
- `skills/braincx-research-agent/main.py`
- `skills/braincx-research-agent/update_sheet_headers.py`
- `skills/braincx-research-agent/create_sheet.py`
- `skills/braincx-research-agent/enrich_sheet.py`

**Client Skills / braincx:**
- `skills/Client Skills/braincx-research-agent/main.py`
- `skills/Client Skills/braincx-research-agent/create_sheet.py`
- `skills/Client Skills/braincx-research-agent/enrich_sheet.py`
- `skills/Client Skills/braincx-research-agent/update_sheet_headers.py`

**Client Skills / conquer:**
- `skills/Client Skills/conquer-social-prospecting/main.py`
- `skills/Client Skills/conquer-social-prospecting/setup_sheets.py`
- `skills/Client Skills/conquer-social-prospecting/sort_sheet.py`

**ClawdBot-LinkedIn:**
- `ClawdBot-LinkedIn/main.py`
- `ClawdBot-LinkedIn/do_login.py`
- `ClawdBot-LinkedIn/linkedin_commenter.py`

**linkedin-comment-bot:**
- `linkedin-comment-bot/main.py`
- `linkedin-comment-bot/sheets_logger.py`

**clawdbot-feed:**
- `skills/clawdbot-feed/main.py`
- `skills/clawdbot-feed/do_login.py`
- `skills/clawdbot-feed/linkedin_commenter.py`

**whatsapp-linkedin-pod:**
- `skills/whatsapp-linkedin-pod/main.py`
- `skills/whatsapp-linkedin-pod/linkedin_commenter.py`

### Step 3 — Fix conquer/backfill_enrichment.py manually
Edit line 17 of `skills/Client Skills/conquer-social-prospecting/backfill_enrichment.py`:
```python
# Replace malformed line with:
load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "conquer-social-prospecting.env")
```

### Step 4 — Copy radley-research-agent (new folder)
Copy all 15 files from `C:/tmp/ai_automation_sync/skills/radley-research-agent/` to `C:/Users/richm/.claude/skills/radley-research-agent/`

Files: `analyzer.py`, `brave_monitor.py`, `config.py`, `facebook_monitor.py`, `linkedin_monitor.py`, `main.py`, `notifier.py`, `reddit_monitor.py`, `requirements.txt`, `run.bat`, `setup_sheets.py`, `storage.py`, `twitter_monitor.py`, `update_sheet_headers.py`, `web_monitor.py`

### Step 5 — Cleanup
Delete `C:/tmp/ai_automation_sync` after copying.

---

## Files NOT changed (already same or local-only)
- All `config.py`, `analyzer.py`, `storage.py`, `notifier.py`, `reddit_monitor.py`, `brave_monitor.py`, `web_monitor.py` across agents — confirmed SAME in diff
- `skills/bishop-research-agent/upwork_monitor.py` — local only, keep
- `skills/bishop-research-agent/setup_logins.py` — local only, keep
- `skills/clawdbot-linkedin/` in GitHub — new lowercase folder, but since `ClawdBot-LinkedIn/` already exists locally and has more content, skip for now

---

## Verification
After sync:
1. Run `python skills/bishop-research-agent/main.py --once` — confirm Upwork cycle appears in output
2. Check `ClawdBot-LinkedIn/linkedin_commenter.py` contains `_wait_for_manual_login` (not `_auto_login`)
3. Check `skills/Client Skills/conquer-social-prospecting/backfill_enrichment.py` line 17 has clean `load_dotenv(dotenv_path=...)` — no trailing `.parent / ".env")`
4. Confirm `skills/radley-research-agent/` folder exists with all 15 files
