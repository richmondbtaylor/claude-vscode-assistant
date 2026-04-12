#!/usr/bin/env python3
"""
LinkedIn Agent Daily Report
Parses Pod Bot activity log + DM Bot threads -> Google Sheets.

Tabs:
  Dashboard          - Key metrics at a glance
  Pod Bot - Activity - Every log entry parsed into structured rows
  Pod Bot - Daily    - Per-day aggregates
  DM Bot - Threads   - All DM threads ever seen

Run manually or via cron. Uses a state file to append only new data.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime

import gspread
from gspread.exceptions import WorksheetNotFound

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)
POD_LOG_PATH    = r"C:\Users\richm\.claude\ClawdBot-LinkedIn\bot_activity.log"
DM_JSON_PATH    = r"C:\Users\richm\.claude\skills\linkedin-dm-assistant\automation\pending_dms.json"
DM_ACTIVITY_LOG = r"C:\Users\richm\.claude\skills\linkedin-dm-assistant\automation\dm_activity.jsonl"
STATE_PATH      = r"C:\Users\richm\.claude\scripts\linkedin_report_state.json"

SHEET_NAME = "LinkedIn Agent Report"

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    return {"sheet_id": None, "pod_last_line": 0, "dm_seen_urls": []}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Pod Bot log parser
# ---------------------------------------------------------------------------
LOG_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.+)$")


def parse_pod_log(start_line=0):
    """Returns (rows, new_line_count).

    rows is a list of dicts ready to be pushed as Sheet rows.
    new_line_count is total lines now in the file (for state tracking).
    """
    if not os.path.exists(POD_LOG_PATH):
        return [], 0

    with open(POD_LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    new_lines = all_lines[start_line:]

    entries = []
    pending = None   # current PROCESSING entry being built

    for raw in new_lines:
        line = raw.strip()
        m = LOG_RE.match(line)
        if not m:
            continue  # continuation line (author name/tier noise)

        ts_str, action, details = m.group(1), m.group(2), m.group(3)
        date_str = ts_str[:10]

        if action == "STARTED":
            entries.append({
                "Timestamp": ts_str,
                "Date": date_str,
                "Post URL": "",
                "Post Author": "",
                "Action": "STARTED",
                "Result": "",
                "Details": details,
            })
            pending = None

        elif action == "COUNTER_RESET":
            entries.append({
                "Timestamp": ts_str,
                "Date": date_str,
                "Post URL": "",
                "Post Author": "",
                "Action": "COUNTER_RESET",
                "Result": "",
                "Details": details,
            })
            pending = None

        elif action == "PROCESSING":
            url = details.replace("New LinkedIn post: ", "").strip()
            pending = {
                "Timestamp": ts_str,
                "Date": date_str,
                "Post URL": url,
                "Post Author": "",
                "Action": "PROCESSING",
                "Result": "",
                "Details": "",
            }
            entries.append(pending)

        elif action == "EXTRACTED" and pending:
            author_m = re.search(r"Post by (.+)", details)
            if author_m:
                pending["Post Author"] = author_m.group(1).strip()

        elif action in ("ERROR", "SKIP", "SUCCESS") and pending:
            pending["Result"] = action
            pending["Details"] = details
            pending = None

    return entries, total_lines


def aggregate_daily(entries):
    """Returns sorted list of daily summary dicts."""
    daily = defaultdict(lambda: {
        "Date": "",
        "Posts Processed": 0,
        "Successfully Extracted": 0,
        "Comments Posted": 0,
        "Own Posts Skipped": 0,
        "Errors - Generation": 0,
        "Errors - Extraction": 0,
        "Bot Restarts": 0,
        "Daily Resets": 0,
        "Success Rate": "0%",
    })

    for e in entries:
        d = e["Date"]
        if not d:
            continue
        daily[d]["Date"] = d
        action = e["Action"]
        result = e["Result"]

        if action == "PROCESSING":
            daily[d]["Posts Processed"] += 1
        if action == "STARTED":
            daily[d]["Bot Restarts"] += 1
        if action == "COUNTER_RESET":
            daily[d]["Daily Resets"] += 1
        if result == "SUCCESS":
            daily[d]["Comments Posted"] += 1
            daily[d]["Successfully Extracted"] += 1
        elif result == "SKIP":
            daily[d]["Own Posts Skipped"] += 1
        elif result == "ERROR":
            det = e.get("Details", "").lower()
            if "generate" in det or "failed to generate" in det:
                daily[d]["Errors - Generation"] += 1
                daily[d]["Successfully Extracted"] += 1  # extracted but generation failed
            else:
                daily[d]["Errors - Extraction"] += 1

    # Compute success rate
    for d, row in daily.items():
        processed = row["Posts Processed"]
        posted = row["Comments Posted"]
        row["Success Rate"] = (
            f"{round(posted / processed * 100)}%" if processed > 0 else "0%"
        )

    return sorted(daily.values(), key=lambda r: r["Date"])


# ---------------------------------------------------------------------------
# DM Bot parsers
# ---------------------------------------------------------------------------

def parse_dm_activity_log(last_line=0):
    """Read dm_activity.jsonl and return (new_rows, total_lines)."""
    if not os.path.exists(DM_ACTIVITY_LOG):
        return [], 0
    rows = []
    with open(DM_ACTIVITY_LOG, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    for raw in all_lines[last_line:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            e = json.loads(raw)
            rows.append({
                "Timestamp": e.get("timestamp", ""),
                "Date": (e.get("timestamp") or "")[:10],
                "Sender": e.get("sender", ""),
                "Thread URL": e.get("thread_url", ""),
                "Fit": e.get("fit", ""),
                "Recommendation": e.get("rec", ""),
                "Draft Preview": e.get("draft_preview", ""),
                "Posted to Slack": "Yes" if e.get("posted_to_slack") else "No",
                "Error": e.get("error") or "",
            })
        except json.JSONDecodeError:
            continue
    return rows, len(all_lines)


def parse_dm_threads(seen_urls):
    """Returns (new_rows, all_seen_urls)."""
    if not os.path.exists(DM_JSON_PATH):
        return [], seen_urls

    with open(DM_JSON_PATH, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read().replace("\ufffd", "'")

    # The file may contain leading plaintext before the JSON array
    json_start = raw.find("[")
    if json_start == -1:
        return [], seen_urls

    try:
        threads = json.loads(raw[json_start:])
    except json.JSONDecodeError:
        return [], seen_urls

    seen_set = set(seen_urls)
    new_rows = []

    for t in threads:
        url = t.get("thread_url", "")
        if url in seen_set:
            continue
        seen_set.add(url)

        messages = t.get("messages", [])
        my_msgs = [m["text"] for m in messages if m.get("is_me")]
        their_msgs = [m["text"] for m in messages if not m.get("is_me")]

        last_time = t.get("last_message_time", "")
        if last_time:
            try:
                last_time = datetime.fromisoformat(last_time).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass

        last_their_msg = their_msgs[-1][:200] if their_msgs else ""
        last_my_msg = my_msgs[-1][:200] if my_msgs else "(none)"

        new_rows.append({
            "Scan Date": datetime.now().strftime("%Y-%m-%d"),
            "Sender": t.get("sender_name", ""),
            "Thread URL": url,
            "Total Messages": len(messages),
            "My Messages": len(my_msgs),
            "Their Messages": len(their_msgs),
            "Last Message Time": last_time,
            "Last Their Message (preview)": last_their_msg,
            "Last My Reply (preview)": last_my_msg,
            "Status": "pending" if not my_msgs else "replied",
        })

    return new_rows, list(seen_set)


# ---------------------------------------------------------------------------
# Sheet helpers
# ---------------------------------------------------------------------------

def get_or_create_worksheet(spreadsheet, name, rows=5000, cols=20):
    try:
        return spreadsheet.worksheet(name)
    except WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)
        return ws


def ensure_headers(ws, headers):
    existing = ws.row_values(1)
    if existing != headers:
        if existing:
            ws.delete_rows(1)
        ws.insert_row(headers, 1)


def append_rows(ws, rows, headers):
    if not rows:
        return
    values = [[str(r.get(h, "")) for h in headers] for r in rows]
    ws.append_rows(values, value_input_option="USER_ENTERED")


def overwrite_tab(ws, headers, rows):
    """Clear and rewrite the entire tab (used for dashboard + daily summary)."""
    ws.clear()
    all_data = [headers] + [[str(r.get(h, "")) for h in headers] for r in rows]
    ws.update(all_data, "A1")


# ---------------------------------------------------------------------------
# Dashboard builder
# ---------------------------------------------------------------------------

def build_dashboard(all_activity, all_dm_threads):
    total_processed = sum(1 for e in all_activity if e["Action"] == "PROCESSING")
    total_posted = sum(1 for e in all_activity if e.get("Result") == "SUCCESS")
    total_skipped = sum(1 for e in all_activity if e.get("Result") == "SKIP")
    total_err_gen = sum(1 for e in all_activity if e.get("Result") == "ERROR" and "generate" in e.get("Details", "").lower())
    total_err_ext = sum(1 for e in all_activity if e.get("Result") == "ERROR" and "generate" not in e.get("Details", "").lower())
    restarts = sum(1 for e in all_activity if e["Action"] == "STARTED")
    days_active = len(set(e["Date"] for e in all_activity if e["Date"]))

    success_rate = f"{round(total_posted / total_processed * 100)}%" if total_processed > 0 else "0%"

    dm_total = len(all_dm_threads)
    dm_sent = sum(1 for t in all_dm_threads if t.get("Posted to Slack") == "Yes")
    dm_skipped = sum(1 for t in all_dm_threads if t.get("Recommendation") == "Skip")
    dm_errors = sum(1 for t in all_dm_threads if t.get("Error"))

    updated = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = [
        {"Metric": "--- POD BOT (LinkedIn Auto-Commenter) ---", "Value": ""},
        {"Metric": "Total posts processed", "Value": total_processed},
        {"Metric": "Comments successfully posted", "Value": total_posted},
        {"Metric": "Own posts skipped", "Value": total_skipped},
        {"Metric": "Errors - comment generation", "Value": total_err_gen},
        {"Metric": "Errors - content extraction", "Value": total_err_ext},
        {"Metric": "Overall success rate", "Value": success_rate},
        {"Metric": "Bot restarts", "Value": restarts},
        {"Metric": "Days with activity", "Value": days_active},
        {"Metric": "", "Value": ""},
        {"Metric": "--- DM BOT (LinkedIn DM Assistant) ---", "Value": ""},
        {"Metric": "Total DM threads processed", "Value": dm_total},
        {"Metric": "Drafts posted to Slack", "Value": dm_sent},
        {"Metric": "Threads skipped (not a fit)", "Value": dm_skipped},
        {"Metric": "Errors", "Value": dm_errors},
        {"Metric": "", "Value": ""},
        {"Metric": "Last report updated", "Value": updated},
    ]
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading state...")
    state = load_state()

    print("Connecting to Google Sheets...")
    gc = gspread.oauth(credentials_filename=CREDS_PATH)

    # Get or create spreadsheet
    if state.get("sheet_id"):
        try:
            spreadsheet = gc.open_by_key(state["sheet_id"])
            print(f"Opened existing sheet: {spreadsheet.url}")
        except Exception:
            print("Sheet not found, creating new one...")
            spreadsheet = gc.create(SHEET_NAME)
            state["sheet_id"] = spreadsheet.id
    else:
        spreadsheet = gc.create(SHEET_NAME)
        state["sheet_id"] = spreadsheet.id
        print(f"Created new sheet: {spreadsheet.url}")

    # Share with user so it's accessible
    try:
        spreadsheet.share(None, perm_type="anyone", role="writer")
    except Exception:
        pass

    # Delete the default empty Sheet1 if it exists
    try:
        sheet1 = spreadsheet.worksheet("Sheet1")
        spreadsheet.del_worksheet(sheet1)
        print("Removed empty Sheet1 tab")
    except WorksheetNotFound:
        pass

    # -----------------------------------------------------------------------
    # Pod Bot - Activity tab
    # -----------------------------------------------------------------------
    print(f"Parsing Pod Bot log (from line {state['pod_last_line']})...")
    new_activity, total_lines = parse_pod_log(state["pod_last_line"])
    print(f"  {len(new_activity)} new entries found (file has {total_lines} lines total)")

    ws_activity = get_or_create_worksheet(spreadsheet, "Pod Bot - Activity")
    activity_headers = ["Timestamp", "Date", "Post URL", "Post Author", "Action", "Result", "Details"]
    ensure_headers(ws_activity, activity_headers)
    append_rows(ws_activity, new_activity, activity_headers)
    state["pod_last_line"] = total_lines

    # -----------------------------------------------------------------------
    # Pod Bot - Daily Summary tab (always rebuild from full log)
    # -----------------------------------------------------------------------
    print("Building daily summary...")
    all_activity, _ = parse_pod_log(0)
    daily_rows = aggregate_daily(all_activity)

    ws_daily = get_or_create_worksheet(spreadsheet, "Pod Bot - Daily")
    daily_headers = [
        "Date", "Posts Processed", "Successfully Extracted", "Comments Posted",
        "Own Posts Skipped", "Errors - Generation", "Errors - Extraction",
        "Bot Restarts", "Daily Resets", "Success Rate",
    ]
    overwrite_tab(ws_daily, daily_headers, daily_rows)
    print(f"  {len(daily_rows)} days summarized")

    # -----------------------------------------------------------------------
    # DM Bot - Activity tab (from dm_activity.jsonl)
    # -----------------------------------------------------------------------
    print("Parsing DM Bot activity log...")
    new_dm_activity, dm_total_lines = parse_dm_activity_log(state.get("dm_last_line", 0))
    print(f"  {len(new_dm_activity)} new DM activity entries")

    ws_dm_activity = get_or_create_worksheet(spreadsheet, "DM Bot - Activity")
    dm_activity_headers = [
        "Timestamp", "Date", "Sender", "Thread URL",
        "Fit", "Recommendation", "Draft Preview", "Posted to Slack", "Error",
    ]
    ensure_headers(ws_dm_activity, dm_activity_headers)
    append_rows(ws_dm_activity, new_dm_activity, dm_activity_headers)
    state["dm_last_line"] = dm_total_lines

    # -----------------------------------------------------------------------
    # DM Bot - Threads tab (snapshot of last pending_dms.json scan)
    # -----------------------------------------------------------------------
    print("Parsing DM Bot threads snapshot...")
    seen_urls = state.get("dm_seen_urls", [])
    new_dm_rows, seen_urls = parse_dm_threads(seen_urls)
    print(f"  {len(new_dm_rows)} new DM threads found")

    ws_dm = get_or_create_worksheet(spreadsheet, "DM Bot - Threads")
    dm_headers = [
        "Scan Date", "Sender", "Thread URL", "Total Messages",
        "My Messages", "Their Messages", "Last Message Time",
        "Last Their Message (preview)", "Last My Reply (preview)", "Status",
    ]
    ensure_headers(ws_dm, dm_headers)
    append_rows(ws_dm, new_dm_rows, dm_headers)
    state["dm_seen_urls"] = seen_urls

    # Rebuild all DM activity rows for dashboard count
    all_dm_activity_rows = ws_dm_activity.get_all_records()

    # -----------------------------------------------------------------------
    # Dashboard tab (always rebuild)
    # -----------------------------------------------------------------------
    print("Building dashboard...")
    dashboard_rows = build_dashboard(all_activity, all_dm_activity_rows)
    ws_dash = get_or_create_worksheet(spreadsheet, "Dashboard")
    dash_headers = ["Metric", "Value"]
    overwrite_tab(ws_dash, dash_headers, dashboard_rows)

    # Move Dashboard to front
    try:
        spreadsheet.reorder_worksheets([ws_dash, ws_daily, ws_activity, ws_dm_activity, ws_dm])
    except Exception:
        pass

    # -----------------------------------------------------------------------
    # Save state and print summary
    # -----------------------------------------------------------------------
    save_state(state)

    print("\n=== DONE ===")
    print(f"Sheet:       {spreadsheet.url}")
    print(f"Pod entries: {len(all_activity)} total, {len(new_activity)} new today")
    print(f"DM activity: {len(all_dm_activity_rows)} total, {len(new_dm_activity)} new today")
    print(f"DM threads:  {len(seen_urls)} unique threads seen")
    print(f"State saved: {STATE_PATH}")


if __name__ == "__main__":
    main()
