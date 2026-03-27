@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python setup_session.py --account main_account
pause
