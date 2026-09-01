#!/usr/bin/env python3
"""Design gate: run the impeccable detector with Rich's brand overrides applied.

Exit codes:
    0  clean (or only advisory/overridden findings)  -> safe to deliver
    1  script/setup problem (binary missing, degraded run, bad target)
    2  real findings -> fix them, do not deliver

Usage:
    python check_design.py <file-or-dir-or-url> [more targets...]
    python check_design.py report.html --no-brand      # skip brand overrides
    python check_design.py report.html --mobile        # also run 390x844
    python check_design.py report.html --json          # raw JSON passthrough

Why this wrapper exists instead of calling `impeccable detect` directly:

1. It refuses to pass on a DEGRADED run. Running the detector without its HTML
   parser deps silently undercounts (verified: 1 finding vs 4) and never
   computes contrast. A degraded pass is not a clean bill of health.
2. It applies ~/.claude/design-sources/brand-overrides/config.json, which
   carries the verified cases where a locked brand rule beats a generic
   Impeccable rule (Bishop warm-white #F9F6F0, Open Sans). Without it every
   Bishop AI light-mode deliverable fails.
3. It reports em-dash findings as blocking even though Impeccable files them as
   advisory, because Rich bans em dashes outright.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BRAND_OVERRIDES = Path.home() / ".claude" / "design-sources" / "brand-overrides" / "config.json"
DEGRADED_MARKER = "DEGRADED"

# Impeccable files these as advisory (never changes its exit code). Rich bans
# them outright, so we re-promote them to blocking.
PROMOTE_TO_BLOCKING = {"em-dash-overuse"}


def find_binary() -> str | None:
    for name in ("impeccable", "impeccable.cmd", "impeccable.ps1"):
        found = shutil.which(name)
        if found:
            return found
    # npm global on Windows is not always on PATH for subshells
    guess = Path(os.environ.get("APPDATA", "")) / "npm" / "impeccable.cmd"
    return str(guess) if guess.exists() else None


def build_config_dir(base: Path, use_brand: bool) -> tuple[Path | None, Path | None]:
    """Write .impeccable/config.json at the scan CWD so the CLI picks it up.

    VERIFIED: the detector resolves .impeccable/ from the process CWD, not from
    the target file's directory. run_detect() therefore runs with cwd=base.

    Returns (cfg_dir, backup_path). If the directory already has a real
    config.json (an actual impeccable project), it is moved aside and restored
    afterwards so we never destroy a user's own settings.
    """
    if not use_brand:
        return None, None
    if not BRAND_OVERRIDES.exists():
        print(f"warning: brand overrides not found at {BRAND_OVERRIDES}; "
              "running without them", file=sys.stderr)
        return None, None

    cfg_dir = base / ".impeccable"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "config.json"

    backup = None
    if cfg_file.exists():
        backup = cfg_dir / "config.json.design-sources-bak"
        shutil.move(str(cfg_file), str(backup))

    overrides = json.loads(BRAND_OVERRIDES.read_text(encoding="utf-8"))
    # Strip our annotation keys; the CLI only reads detector/hook.
    payload = {k: v for k, v in overrides.items() if not k.startswith("_")}
    # Strip per-entry annotations too.
    for entry in payload.get("detector", {}).get("ignoreValues", []):
        for k in ("reason", "scope"):
            entry.pop(k, None)
    cfg_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return cfg_dir, backup


def restore_config(cfg_dir: Path | None, backup: Path | None) -> None:
    if not cfg_dir:
        return
    cfg_file = cfg_dir / "config.json"
    try:
        cfg_file.unlink(missing_ok=True)
        if backup and backup.exists():
            shutil.move(str(backup), str(cfg_file))
        else:
            cfg_dir.rmdir()  # only succeeds if we created it and it is empty
    except OSError:
        pass


def run_detect(binary: str, target: str, viewport: str | None,
               cwd: Path | None) -> tuple[int, str, str]:
    cmd = [binary, "detect", target, "--json"]
    if viewport:
        cmd += ["--viewport", viewport]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return proc.returncode, proc.stdout, proc.stderr


def run_detect_raw(binary: str, target: str, viewport: str | None,
                   cwd: Path | None) -> tuple[int, str, str]:
    """Same scan with all project config bypassed, so we can report what the
    brand overrides suppressed."""
    cmd = [binary, "detect", target, "--json", "--no-config"]
    if viewport:
        cmd += ["--viewport", viewport]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=str(cwd) if cwd else None)
    return proc.returncode, proc.stdout, proc.stderr


def parse_findings(stdout: str) -> list[dict]:
    """VERIFIED shape: a top-level JSON array of objects keyed
    antipattern / name / description / severity / category / file / line / snippet.
    The dict branches below are defensive against future CLI versions."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        for key in ("findings", "results", "issues"):
            if key in data and isinstance(data[key], list):
                return data[key]
        files = data.get("files")
        if isinstance(files, list):
            out: list[dict] = []
            for f in files:
                out.extend(f.get("findings", []) or [])
            return out
    return data if isinstance(data, list) else []


def rule_id(f: dict) -> str:
    return f.get("antipattern") or f.get("rule") or f.get("id") or "?"


def describe(f: dict) -> str:
    return f.get("snippet") or f.get("message") or f.get("name") or ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Impeccable design gate with brand overrides")
    ap.add_argument("targets", nargs="+", help="file, directory, or URL")
    ap.add_argument("--no-brand", action="store_true", help="do not apply brand overrides")
    ap.add_argument("--mobile", action="store_true", help="also run a 390x844 pass")
    ap.add_argument("--json", action="store_true", help="print raw detector JSON")
    args = ap.parse_args()

    binary = find_binary()
    if not binary:
        print("FAIL: `impeccable` binary not found. Install it with:\n"
              "  npm install -g impeccable\n"
              "Do NOT fall back to the checkout in ~/.claude/design-sources/impeccable "
              "- it runs DEGRADED and undercounts.", file=sys.stderr)
        return 1

    first = Path(args.targets[0])
    is_url = str(args.targets[0]).startswith(("http://", "https://"))
    if is_url:
        base = Path.cwd()
    elif first.exists():
        base = first.parent if first.is_file() else first
    else:
        print(f"FAIL: target not found: {args.targets[0]}", file=sys.stderr)
        return 1
    base = base.resolve()
    cfg_dir, backup = build_config_dir(base, use_brand=not args.no_brand)

    blocking = 0
    try:
        for target in args.targets:
            # Config resolves from CWD, so run there and address the target
            # relatively when it lives under base.
            tpath = Path(target)
            if not str(target).startswith(("http://", "https://")) and tpath.exists():
                try:
                    rel = str(tpath.resolve().relative_to(base))
                except ValueError:
                    rel = str(tpath.resolve())
            else:
                rel = target

            passes = [(None, "desktop")]
            if args.mobile:
                passes.append(("390x844", "mobile"))

            for viewport, label in passes:
                code, out, err = run_detect(binary, rel, viewport, base)

                if DEGRADED_MARKER in (err or "") or DEGRADED_MARKER in (out or ""):
                    print(f"FAIL: detector ran DEGRADED on {target}. Findings are an "
                          "undercount, not a clean result. Reinstall with "
                          "`npm install -g impeccable`.", file=sys.stderr)
                    return 1

                if args.json:
                    print(out)

                findings = parse_findings(out)
                promoted = [f for f in findings if rule_id(f) in PROMOTE_TO_BLOCKING]

                # Auditability: cream-palette can only be waived rule-wide (it
                # emits no ignoreValue), so show what the waiver hid instead of
                # dropping it silently. A beige page that is NOT a brand ground
                # still needs a human to look at it.
                if cfg_dir:
                    _, raw_out, _ = run_detect_raw(binary, rel, viewport, base)
                    raw = parse_findings(raw_out)
                    kept = {(rule_id(f), describe(f)) for f in findings}
                    hidden = [f for f in raw if (rule_id(f), describe(f)) not in kept]
                    if hidden:
                        print(f"\n[{label}] {target}: {len(hidden)} finding(s) "
                              "overridden by brand (not blocking, shown for review)")
                        for f in hidden:
                            print(f"  ~ [{rule_id(f)}] {describe(f)}")

                if findings or code == 2 or promoted:
                    blocking += max(len(findings), 1 if code == 2 else 0)
                    print(f"\n[{label}] {target}: {len(findings) or 'some'} finding(s)")
                    for f in findings:
                        rid = rule_id(f)
                        line = f.get("line") or 0
                        loc = f" line {line}" if line else ""
                        flag = "  (advisory upstream, blocking here)" if rid in PROMOTE_TO_BLOCKING else ""
                        print(f"  [{rid}]{loc} {describe(f)}{flag}")
                elif code not in (0, 2):
                    print(f"FAIL: detector errored on {target} (exit {code})\n{err}",
                          file=sys.stderr)
                    return 1
    finally:
        restore_config(cfg_dir, backup)

    if blocking:
        print(f"\nGATE FAILED: {blocking} finding(s). Fix them before delivery.\n"
              "If a finding is a genuine locked-brand conflict, add a scoped entry to\n"
              f"{BRAND_OVERRIDES} with a reason - never a blanket ignoreRules entry.")
        return 2

    print("GATE PASSED: no blocking design findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
