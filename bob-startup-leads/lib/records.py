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


def row_key(row: dict) -> str:
    """Stable resume/identity key for a row, shared by every stage that
    checkpoints against a growing output file. RULING C35 introduced this
    fallback chain in signals.py alone; RULING C53 promotes it here so
    site_scrape.py and enrich_tier1.py stop keying resume on a bare
    `company_id`, which is falsy or missing on an older/malformed row and
    would otherwise silently reprocess (site_scrape) or silently DROP
    (enrich_tier1, which had no truthiness guard at all: one output row
    with no company_id put None into its seen-set, and every later idless
    input row then matched that None and was skipped forever) that row.
    Falls back from company_id to domain, then to normalized name plus
    state, so every row gets a stable, non-empty key."""
    cid = row.get("company_id")
    if cid:
        return cid
    return company_id(row.get("name", ""), row.get("state", ""), row.get("domain"))


def ensure_signals(row: dict) -> dict:
    """Return row['signals'] as a mutable dict, creating or replacing it if
    the key is absent OR present with an explicit null. RULING C54:
    row.setdefault("signals", {}) only helps when the key is absent
    entirely; a key that is present with an explicit None (round-tripped
    through JSON, or written by an upstream stage that never filled it in)
    makes setdefault a no-op that returns None, and a caller that then
    does sig[key] = value raises TypeError and aborts the whole batch on
    one bad row. Mutates row in place (matching setdefault's contract)
    and returns the same dict so callers can keep writing into it."""
    sig = row.get("signals")
    if sig is None:
        sig = {}
    row["signals"] = sig
    return sig


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
