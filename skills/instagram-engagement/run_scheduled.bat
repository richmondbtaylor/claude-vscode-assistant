@echo off
:: Instagram Engagement — Daily Scheduled Session Launcher
:: Called by Windows Task Scheduler at 6:30 AM.
:: run_scheduled.py handles random start delay (0-60 min) and duration to ~5:30 PM.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python run_scheduled.py >> scheduler.log 2>&1
