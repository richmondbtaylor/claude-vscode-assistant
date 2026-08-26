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
    p = pathlib.Path(path)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path, rows: Iterable[dict]) -> int:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n
