"""Company record identity and JSONL persistence."""
import hashlib
import json
import pathlib
from typing import Iterable, Iterator

from lib.normalize import norm_name

# Canonical company record keys. Every stage reads and writes this shape.
FIELDS = (
    "company_id", "name", "domain", "website", "phone", "email",
    "email_status", "address", "city", "state", "zip", "naics",
    "category", "sources", "signals", "score", "tier",
)


def company_id(name: str, state: str, domain: str | None) -> str:
    """Stable id. Domain wins when present, otherwise normalized name plus state."""
    key = domain.lower() if domain else f"{norm_name(name)}|{(state or '').upper()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def read_jsonl(path) -> Iterator[dict]:
    """Yield each well-formed row. A malformed trailing line (a process killed
    mid-append can leave one) is skipped rather than raising, so a file that
    is 99.9% good does not break every downstream stage. The skip is not
    silent: it is printed so a truncated file is still visible to whoever is
    watching the run.
    """
    p = pathlib.Path(path)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"[read_jsonl] skipped malformed line {lineno} in {p}", flush=True)


def write_jsonl(path, rows: Iterable[dict]) -> int:
    """Overwrite path with exactly these rows. Full rewrite - do not use this
    for incremental checkpointing of a growing file; use append_jsonl."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def append_jsonl(path, rows: Iterable[dict]) -> int:
    """Append rows to path, creating it (and parent dirs) if needed.

    O(1) per call regardless of how large the file already is - the correct
    checkpoint primitive for a long-running scrape, where write_jsonl's full
    rewrite would cost O(n) I/O per checkpoint and, because it opens in "w"
    mode, would truncate the file first and risk losing already-durable rows
    if the process is killed mid-write.
    """
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
        fh.flush()
    return n
