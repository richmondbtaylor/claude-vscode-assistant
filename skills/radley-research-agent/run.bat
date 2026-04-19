@echo off
echo ==========================================
echo      Radley Lead Finder Agent
echo      radley.tax — R&D Tax Credits
echo ==========================================
echo.
echo NOTE: Close Claude Code first — they share the same rate limit.
echo.
cd /d "C:\Users\docch\.claude\skills\radley-research-agent"
call venv\Scripts\activate
python main.py --once
echo.
echo Done! Check your Google Sheet:
echo https://docs.google.com/spreadsheets/d/11aPWsKKXMPlLS04xYv2dcitixgX5_GMblxhXsfGylak/edit
pause
