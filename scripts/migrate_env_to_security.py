# Migrate all .env files to ~/.claude/security/
# and update all scripts to use Path.home() / ".claude" / "security" / "AGENT.env".
import re
import shutil
from pathlib import Path

BASE = Path.home() / ".claude"
SECURITY = BASE / "security"
SECURITY.mkdir(exist_ok=True)

# ── Mapping: old .env path -> new name in security/ ────────────────────────────
ENV_MAP = {
    BASE / "skills" / "infographic-generator" / ".env":          "infographic-generator.env",
    BASE / "skills" / "captioncraft" / ".env":                   "captioncraft.env",
    BASE / "skills" / "linkedin-dm-assistant" / "automation" / ".env": "linkedin-dm-assistant.env",
    BASE / "skills" / "whatsapp-linkedin-pod" / ".env":          "whatsapp-linkedin-pod.env",
    BASE / "skills" / "bishop-research-agent" / ".env":          "bishop-research-agent.env",
    BASE / "skills" / "instagram-engagement" / ".env":           "instagram-engagement.env",
    BASE / "skills" / "clawdbot-feed" / ".env":                  "clawdbot-feed.env",
    BASE / "skills" / "daily-carousel" / ".env":                 "daily-carousel.env",
    BASE / "ClawdBot-LinkedIn" / ".env":                         "clawdbot-linkedin.env",
    BASE / "ClawdBot-LinkedIn" / "promptanything-live" / ".env": "clawdbot-linkedin-promptanything.env",
    BASE / "skills" / "tarsen" / ".env":                         "tarsen.env",
    BASE / "skills" / "Client Skills" / "conquer-social-prospecting" / ".env": "conquer-social-prospecting.env",
    BASE / "linkedin-comment-bot" / ".env":                      "linkedin-comment-bot.env",
    BASE / "skills" / "braincx-research-agent" / ".env":        "braincx-research-agent.env",
    # The one we already moved to a sub-security folder - same agent, same data
    BASE / "skills" / "Client Skills" / "braincx-research-agent" / "security" / ".env": "braincx-client-research-agent.env",
}

# ── Script folders and which security file they should load ───────────────────
SCRIPT_GROUPS = [
    (BASE / "linkedin-comment-bot",                                          "linkedin-comment-bot.env"),
    (BASE / "ClawdBot-LinkedIn",                                             "clawdbot-linkedin.env"),
    (BASE / "skills" / "braincx-research-agent",                            "braincx-research-agent.env"),
    (BASE / "skills" / "bishop-research-agent",                             "bishop-research-agent.env"),
    (BASE / "skills" / "whatsapp-linkedin-pod",                             "whatsapp-linkedin-pod.env"),
    (BASE / "skills" / "linkedin-dm-assistant" / "automation",             "linkedin-dm-assistant.env"),
    (BASE / "skills" / "tarsen",                                             "tarsen.env"),
    (BASE / "skills" / "instagram-engagement",                              "instagram-engagement.env"),
    (BASE / "skills" / "Client Skills" / "conquer-social-prospecting",     "conquer-social-prospecting.env"),
    (BASE / "skills" / "clawdbot-feed",                                     "clawdbot-feed.env"),
    (BASE / "skills" / "Client Skills" / "braincx-research-agent",        "braincx-client-research-agent.env"),
    (BASE / "skills" / "daily-carousel",                                    "daily-carousel.env"),
]

# ── Step 1: Copy .env files to security/ ─────────────────────────────────────
print("=== Step 1: Copying .env files to security/ ===")
for src, dest_name in ENV_MAP.items():
    dest = SECURITY / dest_name
    if src.exists():
        shutil.copy2(src, dest)
        print(f"  COPIED  {src.relative_to(BASE)}  ->  security/{dest_name}")
    else:
        print(f"  MISSING {src.relative_to(BASE)}  (skipped)")

# ── Step 2: Update scripts ────────────────────────────────────────────────────
print("\n=== Step 2: Updating scripts ===")

# Patterns that match existing load_dotenv calls (with or without dotenv_path)
LOAD_DOTENV_RE = re.compile(
    r'load_dotenv\s*\(.*?\)',
    re.DOTALL
)

def patch_file(py_file: Path, env_name: str) -> bool:
    """Return True if file was changed."""
    text = py_file.read_text(encoding="utf-8")

    # Skip if no load_dotenv call
    if "load_dotenv" not in text:
        return False

    new_call = f'load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "{env_name}")'

    # Replace all load_dotenv(...) calls with the new one
    new_text = LOAD_DOTENV_RE.sub(new_call, text)

    # Ensure `from pathlib import Path` is present
    if "from pathlib import Path" not in new_text:
        # Insert after the last `import` before `from dotenv import`
        new_text = new_text.replace(
            "from dotenv import load_dotenv",
            "from pathlib import Path\nfrom dotenv import load_dotenv",
            1  # only first occurrence
        )

    if new_text != text:
        py_file.write_text(new_text, encoding="utf-8")
        return True
    return False

changed_total = 0
for folder, env_name in SCRIPT_GROUPS:
    if not folder.exists():
        print(f"  MISSING folder {folder.relative_to(BASE)}")
        continue
    py_files = list(folder.glob("*.py"))
    changed_in_group = 0
    for py_file in py_files:
        if patch_file(py_file, env_name):
            print(f"  UPDATED {py_file.relative_to(BASE)}")
            changed_in_group += 1
    changed_total += changed_in_group

print(f"\nTotal scripts updated: {changed_total}")

# ── Step 3: Delete old .env files ────────────────────────────────────────────
print("\n=== Step 3: Deleting old .env files ===")
for src in ENV_MAP:
    if src.exists():
        src.unlink()
        print(f"  DELETED {src.relative_to(BASE)}")

# Also remove the now-empty security subfolder inside Client Skills/braincx
braincx_sec = BASE / "skills" / "Client Skills" / "braincx-research-agent" / "security"
if braincx_sec.exists() and not any(braincx_sec.iterdir()):
    braincx_sec.rmdir()
    print("  REMOVED skills/Client Skills/braincx-research-agent/security/ (now empty)")

print("\nDone!")
