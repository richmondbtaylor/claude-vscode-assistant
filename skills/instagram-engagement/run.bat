@echo off
:: Instagram Engagement Automation — Windows launcher
:: Edit ACCOUNT and FOCUS below, then double-click to run.

set ACCOUNT=main_account
set FOCUS=#AIautomation
set DURATION=60

cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py --account %ACCOUNT% --focus "%FOCUS%" --duration %DURATION%
pause
