"""
Scheduled Instagram engagement runner.

Called by the Claude cron job each morning. Handles:
  - Random start delay: 0-60 minutes (keeps start time within ±30 min of 7 AM)
  - Dynamic duration: calculated so the session ends at 5:30 PM ± 30 minutes
  - Runs main.py with the venv Python directly (no activate needed)
"""

import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPT_DIR / "venv" / "Scripts" / "python.exe"
LOG_FILE = SCRIPT_DIR / "scheduler.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# --- Random start delay (0–60 minutes) ---
delay_seconds = random.randint(0, 3600)
log(f"Scheduled run starting. Random delay: {delay_seconds // 60}m {delay_seconds % 60}s")
time.sleep(delay_seconds)

now = datetime.now()

# --- Calculate duration to end at 5:30 PM ± 30 minutes ---
stop_offset_minutes = random.randint(-30, 30)
target_stop = now.replace(hour=17, minute=30, second=0, microsecond=0) + timedelta(minutes=stop_offset_minutes)

duration_minutes = int((target_stop - now).total_seconds() / 60)

if duration_minutes < 60:
    log(f"Not enough time remaining in window ({duration_minutes} min). Skipping today's session.")
    sys.exit(0)

log(f"Starting engagement session. Target stop: {target_stop.strftime('%H:%M')} ({duration_minutes} min)")

if not VENV_PYTHON.exists():
    log(f"ERROR: venv Python not found at {VENV_PYTHON}")
    sys.exit(1)

result = subprocess.run(
    [str(VENV_PYTHON), "main.py",
     "--account", "main_account",
     "--focus", "#AIautomation",
     "--duration", str(duration_minutes)],
    cwd=str(SCRIPT_DIR),
)

log(f"Session ended. Exit code: {result.returncode}")
