#!/usr/bin/env python3
"""
Session archive hook — fires on Claude Code Stop event.
Reads the session transcript and writes a dated summary to:
  C:\Users\richm\.claude\transcripts\YYYY-MM-DD_HHMMSS.md
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

TRANSCRIPTS_DIR = Path(r"C:\Users\richm\.claude\transcripts")
TRANSCRIPTS_DIR.mkdir(exist_ok=True)


def extract_summary(transcript: list) -> str:
    """Pull user messages and a one-line topic from the transcript."""
    user_messages = []
    for entry in transcript:
        role = entry.get("role", "")
        if role == "user":
            content = entry.get("content", "")
            if isinstance(content, list):
                # Content blocks
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text and len(text) < 500:
                            user_messages.append(text)
            elif isinstance(content, str) and content.strip():
                if len(content) < 500:
                    user_messages.append(content.strip())

    return user_messages


def main():
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return

    transcript_path = data.get("transcript_path", "")
    session_id = data.get("session_id", "unknown")

    # Try to read the transcript file
    transcript = []
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript = json.load(f)
        except Exception:
            pass

    user_messages = extract_summary(transcript)
    if not user_messages:
        return  # Nothing worth archiving (empty session)

    # Determine working directory from transcript if available
    cwd = data.get("cwd", "")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = TRANSCRIPTS_DIR / f"{timestamp}.md"

    lines = [
        f"# Session {timestamp}",
        f"",
        f"**Session ID:** {session_id}",
    ]
    if cwd:
        lines.append(f"**Working dir:** {cwd}")
    lines += [
        f"",
        f"## User messages",
        f"",
    ]
    for i, msg in enumerate(user_messages, 1):
        # Truncate very long messages
        display = msg[:300] + "..." if len(msg) > 300 else msg
        lines.append(f"{i}. {display}")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
