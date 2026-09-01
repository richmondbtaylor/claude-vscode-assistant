#!/usr/bin/env python3
"""Add, update, and prune GitHub design-resource repos in the design-sources registry.

    python sync.py list
    python sync.py update [name]          # git pull + re-prune every source, or one
    python sync.py add <name> <repo-url>  # clone, prune, register
    python sync.py prune [name]           # re-apply the prune list only

Adding a repo is deliberately two steps: this script fetches and registers it,
then YOU write the digest at design-sources/digests/<name>.md by reading the
checkout. A digest written by hand from the actual repo is the whole point; an
auto-generated one would just be the README with extra steps.

Why pruning matters: impeccable ships a prebuilt copy of itself for ~15 harnesses
as hidden dot-dirs. Unpruned it is 75.6MB / 2699 files; pruned it is 11.7MB / 386.
Rich already has an Explorer-slowness problem in ~/.claude from folder bloat, so
every source gets a prune list.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / ".claude" / "design-sources"
REGISTRY = ROOT / "sources.json"

# Applied to every new source unless its entry overrides it. Provider dot-dirs
# are prebuilt duplicates of the skill; heavy dirs are not needed for reading.
DEFAULT_PRUNE = [
    "tests", "demos", "extension", "docs", "plugin", "node_modules",
    ".claude", ".claude-plugin", ".codex", ".cursor", ".gemini", ".github",
    ".grok", ".hermes", ".kiro", ".opencode", ".pi", ".qoder", ".trae",
    ".trae-cn", ".vibe", ".agents",
]


def load() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    REGISTRY.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def measure(path: Path) -> str:
    files = [f for f in path.rglob("*") if f.is_file()]
    mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
    return f"{mb:.1f} MB / {len(files)} files"


def do_prune(path: Path, prune: list[str]) -> None:
    for rel in prune:
        target = path / rel
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)


def cmd_list(data: dict) -> int:
    for s in data["sources"]:
        path = ROOT / s["name"]
        state = measure(path) if path.exists() else "NOT CLONED"
        print(f"{s['name']:<14} {s.get('pinned_version','?'):<8} {state}")
        print(f"  {s['repo']}")
        print(f"  digest: {s['digest']}   cli: {s.get('has_cli', False)}")
    return 0


def cmd_update(data: dict, only: str | None) -> int:
    for s in data["sources"]:
        if only and s["name"] != only:
            continue
        path = ROOT / s["name"]
        if not path.exists():
            # Checkouts are gitignored, so a fresh clone of ~/.claude has the
            # registry but no sources. Restore from the manifest rather than
            # making the user hand-clone what sources.json already describes.
            print(f"{s['name']}: not present, restoring from {s['repo']}")
            code, out = run(["git", "clone", "--depth", "1", s["repo"], str(path)])
            if code != 0:
                print(f"{s['name']}: clone failed\n{out}", file=sys.stderr)
                continue
            do_prune(path, s.get("prune", DEFAULT_PRUNE))
            _, sha = run(["git", "rev-parse", "HEAD"], cwd=path)
            print(f"{s['name']}: restored at {sha[:8]} ({measure(path)})")
            if s.get("has_cli"):
                print(f"  NOTE: also run `npm install -g {s['name']}` for the "
                      "gate, and re-copy the skill build per SKILL.md.")
            continue
        code, out = run(["git", "pull", "--ff-only"], cwd=path)
        if code != 0:
            print(f"{s['name']}: pull failed\n{out}", file=sys.stderr)
            continue
        do_prune(path, s.get("prune", DEFAULT_PRUNE))
        _, sha = run(["git", "rev-parse", "HEAD"], cwd=path)
        changed = sha[:40] != s.get("pinned_commit", "")
        s["pinned_commit"] = sha[:40]
        print(f"{s['name']}: {sha[:8]} {measure(path)}")
        if changed:
            print(f"  UPSTREAM CHANGED - re-read the checkout and refresh "
                  f"{s['digest']}; the digest is now potentially stale.")
    save(data)
    return 0


def cmd_add(data: dict, name: str, repo: str) -> int:
    if any(s["name"] == name for s in data["sources"]):
        print(f"{name} already registered", file=sys.stderr)
        return 1
    path = ROOT / name
    code, out = run(["git", "clone", "--depth", "1", repo, str(path)])
    if code != 0:
        print(f"clone failed\n{out}", file=sys.stderr)
        return 1
    do_prune(path, DEFAULT_PRUNE)
    _, sha = run(["git", "rev-parse", "HEAD"], cwd=path)
    data["sources"].append({
        "name": name,
        "repo": repo,
        "pinned_commit": sha[:40],
        "digest": f"digests/{name}.md",
        "kind": "craft-rules",
        "has_cli": False,
        "applies_to": {"web-ui": "full", "deck-doc": "full",
                       "brand-graphics": "guidance-only",
                       "video-motion": "type-craft-only"},
        "prune": DEFAULT_PRUNE,
    })
    save(data)
    print(f"added {name} at {sha[:8]} ({measure(path)})")
    print(f"NEXT: read {path} and write design-sources/digests/{name}.md by hand,")
    print("then add it to the routing table in skills/design-sources/SKILL.md.")
    return 0


def cmd_prune(data: dict, only: str | None) -> int:
    for s in data["sources"]:
        if only and s["name"] != only:
            continue
        path = ROOT / s["name"]
        if not path.exists():
            continue
        before = measure(path)
        do_prune(path, s.get("prune", DEFAULT_PRUNE))
        print(f"{s['name']}: {before} -> {measure(path)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    u = sub.add_parser("update"); u.add_argument("name", nargs="?")
    a = sub.add_parser("add"); a.add_argument("name"); a.add_argument("repo")
    p = sub.add_parser("prune"); p.add_argument("name", nargs="?")
    args = ap.parse_args()

    if not REGISTRY.exists():
        print(f"registry missing: {REGISTRY}", file=sys.stderr)
        return 1
    data = load()

    if args.cmd == "list":
        return cmd_list(data)
    if args.cmd == "update":
        return cmd_update(data, args.name)
    if args.cmd == "add":
        return cmd_add(data, args.name, args.repo)
    if args.cmd == "prune":
        return cmd_prune(data, args.name)
    return 1


if __name__ == "__main__":
    sys.exit(main())
