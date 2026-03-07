"""
cleanup_old_leads.py — Delete leads older than 7 days from Google Sheets.

Reads column A (Timestamp, format "MM/DD/YYYY HH:MM") of the Leads worksheet
and deletes any row whose timestamp is more than 7 days old.

Rows are deleted in descending index order to avoid row-shift issues.
Run automatically at the end of each GitHub Actions workflow run.
"""

import os
import time
from datetime import datetime, timedelta

from sheets_auth import get_sheets_client

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "15PVXkBIr4Xqa2k3dWtygsUjLfXw47wSxhxfyDmw_B_E")
WORKSHEET_NAME = "Leads"
TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M"
CUTOFF_DAYS = 7

# Sleep between delete calls only when removing many rows to stay within
# the Sheets API write quota (60 requests/minute).
DELETE_SLEEP_THRESHOLD = 20
DELETE_SLEEP_SECONDS = 1.0


def main():
    cutoff = datetime.now() - timedelta(days=CUTOFF_DAYS)
    print(f"Cutoff: {cutoff.strftime(TIMESTAMP_FORMAT)} — deleting anything older than this.")

    client = get_sheets_client()
    worksheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

    # Fetch column A as a flat list (1-indexed rows in the sheet = list index + 1)
    col_a = worksheet.col_values(1)

    rows_to_delete = []
    for row_index, cell in enumerate(col_a, start=1):
        if not cell or cell.strip().lower() == "timestamp":
            continue  # skip header and empty cells
        try:
            ts = datetime.strptime(cell.strip(), TIMESTAMP_FORMAT)
        except ValueError:
            print(f"  Warning: unparseable timestamp in row {row_index}: {cell!r} — skipping.")
            continue

        if ts < cutoff:
            rows_to_delete.append(row_index)

    if not rows_to_delete:
        print("No leads older than 7 days. Nothing to delete.")
        return

    print(f"Deleting {len(rows_to_delete)} row(s)...")

    # Delete highest row index first so lower indices remain valid
    use_sleep = len(rows_to_delete) > DELETE_SLEEP_THRESHOLD
    for row_index in sorted(rows_to_delete, reverse=True):
        worksheet.delete_rows(row_index)
        if use_sleep:
            time.sleep(DELETE_SLEEP_SECONDS)

    print(f"Done. Removed {len(rows_to_delete)} lead(s) from '{WORKSHEET_NAME}'.")


if __name__ == "__main__":
    main()
