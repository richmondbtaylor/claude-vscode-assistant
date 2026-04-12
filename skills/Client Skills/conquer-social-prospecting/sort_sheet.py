"""
Sort the Leads sheet:
- Strips existing separator rows
- Auto-detects all run boundaries by finding timestamp gaps > MIN_GAP_MINUTES
- Sorts each run by Intent Score descending
- Writes back with clean "== Run N ==" separators (no em dashes)
- Removes all em dashes from every cell
"""

import os
import sys
from datetime import datetime, timedelta

import gspread
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))
from config import SHEET_COLUMNS

SHEET_ID   = os.environ["GOOGLE_SHEET_ID"]
SHEET_NAME = "Leads"
CREDS_PATH = os.environ.get("GOOGLE_OAUTH_CREDENTIALS", "./credentials.json")

# A gap larger than this (minutes) between consecutive rows marks a new run
MIN_GAP_MINUTES = 45


def _parse_ts(ts_str: str) -> datetime | None:
    for fmt in ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def _score(row: list[str], score_col: int) -> int:
    try:
        return int(row[score_col])
    except (ValueError, IndexError):
        return -1


def _strip_em_dashes(row: list[str]) -> list[str]:
    return [cell.replace("\u2014", "-").replace("\u2013", "-") for cell in row]


def main():
    gc = gspread.oauth(credentials_filename=CREDS_PATH)
    ss = gc.open_by_key(SHEET_ID)
    ws = ss.worksheet(SHEET_NAME)

    all_values = ws.get_all_values()
    if not all_values:
        print("Sheet is empty.")
        return

    header = all_values[0]
    ts_col    = header.index("Timestamp")
    score_col = header.index("Intent Score")

    # Strip separator rows
    data_rows = [r for r in all_values[1:] if not r[ts_col].startswith("===") and not r[ts_col].startswith("---") and not r[ts_col].startswith("***") and not r[ts_col].startswith("#ERROR")]
    print(f"Data rows after stripping separators: {len(data_rows)}")

    # Sort all rows chronologically
    timed: list[tuple[datetime | None, list[str]]] = [
        (_parse_ts(r[ts_col]), r) for r in data_rows
    ]
    timed.sort(key=lambda x: x[0] or datetime.max)

    # Split into runs by finding all gaps > MIN_GAP_MINUTES
    runs: list[list[list[str]]] = []
    current_run: list[list[str]] = []
    prev_ts: datetime | None = None

    for ts, row in timed:
        if ts is not None and prev_ts is not None:
            gap = (ts - prev_ts).total_seconds() / 60
            if gap > MIN_GAP_MINUTES:
                if current_run:
                    runs.append(current_run)
                current_run = []
        current_run.append(row)
        if ts is not None:
            prev_ts = ts

    if current_run:
        runs.append(current_run)

    print(f"Detected {len(runs)} run(s): {[len(r) for r in runs]}")

    # Sort each run by score descending, strip em dashes from all cells
    sorted_runs = [
        [_strip_em_dashes(row) for row in sorted(run, key=lambda r: _score(r, score_col), reverse=True)]
        for run in runs
    ]

    # Build output with separators (plain dashes only, no em dashes)
    def sep(label: str) -> list[str]:
        row = [""] * len(header)
        row[ts_col] = label
        return row

    new_rows: list[list[str]] = []
    for i, run in enumerate(sorted_runs, start=1):
        new_rows.append(sep(f"*** Run {i} ({len(run)} leads) ***"))
        new_rows.extend(run)

    # Write back
    total = len(new_rows) + 1
    ws.clear()
    if ws.row_count < total + 5:
        ws.add_rows(total + 5 - ws.row_count)

    ws.update(values=[header] + new_rows, range_name="A1", value_input_option="USER_ENTERED")

    print(f"Done. {sum(len(r) for r in sorted_runs)} leads across {len(sorted_runs)} runs.")
    for i, run in enumerate(sorted_runs, start=1):
        scores = [_score(r, score_col) for r in run]
        high = sum(1 for s in scores if s >= 50)
        med  = sum(1 for s in scores if 25 <= s < 50)
        top  = max(scores) if scores else 0
        print(f"  Run {i}: {len(run)} leads | top={top} | High(50+): {high} | Medium(25-49): {med}")


if __name__ == "__main__":
    main()
