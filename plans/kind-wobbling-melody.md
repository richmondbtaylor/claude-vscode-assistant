# Plan: Add context-mode Globally to .claude

## Context
context-mode is an MCP server + hook system that keeps large tool outputs out of the context
window by routing them through a SQLite sandbox. Claims 96% context savings. Rich's agents
(LinkedIn, radley-research, carousel, TARSEN) all deal with large CSVs, Playwright snapshots,
and API responses that bloat context. Installing globally means all agents benefit automatically.

## What Gets Installed
- MCP server with 6 sandbox tools: `ctx_execute`, `ctx_execute_file`, `ctx_batch_execute`,
  `ctx_index`, `ctx_search`, `ctx_fetch_and_index`
- 5 hook types registered via hooks.json (plugin system manages, NOT settings.json):
  - `SessionStart` — injects routing rules + session continuity context at every session open
  - `UserPromptSubmit` — captures each prompt to SQLite for post-compact continuity
  - `PostToolUse` — captures file edits, git ops, tasks, errors (13 categories) to SQLite
  - `PreCompact` — builds a <2KB XML resume snapshot before context compaction
  - `PreToolUse` — intercepts Bash/Read/WebFetch/Grep/Agent and routes large outputs to sandbox
- 5 slash commands: `/context-mode:ctx-stats`, `ctx-doctor`, `ctx-upgrade`, `ctx-purge`, `ctx-insight`

## Conflict Check
- Rich's existing `Stop` hook (session_archive.py) — **NO CONFLICT**. context-mode only uses
  PostToolUse, PreToolUse, PreCompact, SessionStart, UserPromptSubmit. The `Stop` type is untouched.
- No existing MCP servers configured — clean slate.
- CLAUDE.md routing instructions are injected dynamically by the SessionStart hook via `ROUTING_BLOCK`
  — no manual CLAUDE.md edits needed.

## Installation Steps

### Step 1: Install via Plugin Marketplace (in Claude Code terminal)
```
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
```
The plugin system automatically:
- Installs the MCP server and sets `CLAUDE_PLUGIN_ROOT`
- Registers all hooks via hooks.json (not settings.json, so no manual merge needed)
- Registers the 5 slash commands

### Step 2: Verify Installation
```
/context-mode:ctx-doctor
```
Should show: runtimes OK, hooks registered, FTS5 available, plugin registered.

### Step 3: Spot-Check Hook Registration
After install, confirm settings.json still has the Stop hook intact and context-mode hooks
were NOT written to settings.json (the plugin system uses hooks.json instead):
```bash
cat ~/.claude/settings.json
```

## What Changes in settings.json
**Nothing** — the plugin system registers hooks via its own hooks.json mechanism, separate
from settings.json. Rich's existing `Stop` hook remains the only entry in settings.json.

## Files Modified
- `~/.claude/settings.json` — no changes expected (plugin system handles hooks separately)
- `~/.claude/CLAUDE.md` — no changes needed (routing rules injected by SessionStart hook)
- New: `~/.claude/plugins/` — plugin cache + installed_plugins.json (created by plugin system)
- New: `~/.claude/context-mode/` — SQLite session DB, logs

## Verification
1. `/context-mode:ctx-doctor` — all green
2. Run a session, then `/context-mode:ctx-stats` — should show savings data
3. Trigger a large Bash output (e.g., list all leads in radley CSV) and confirm it gets
   routed through ctx_execute instead of flooding context
4. Confirm Stop hook still fires at session end: check session_archive output is still created
