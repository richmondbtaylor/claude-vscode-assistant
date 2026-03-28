@echo off
echo Creating Bishop AI scheduled tasks...
echo (This requires Administrator privileges)
echo.

REM Daily LinkedIn DM Scan at 9:00 AM
schtasks /create ^
  /tn "BishopAI LinkedIn DM Scan" ^
  /tr "\"C:\Users\richm\AppData\Local\Programs\Python\Python311\python.exe\" \"C:\Users\richm\.claude\skills\linkedin-dm-assistant\automation\daily_scan.py\"" ^
  /sc daily ^
  /st 09:00 ^
  /f ^
  /rl HIGHEST

if %errorlevel% equ 0 (
    echo [OK] Daily DM scan scheduled at 9:00 AM
) else (
    echo [FAIL] Could not create DM scan task
)

echo.

REM Start server + ngrok at login
schtasks /create ^
  /tn "BishopAI DM Server Startup" ^
  /tr "\"C:\Users\richm\.claude\skills\linkedin-dm-assistant\automation\start.bat\"" ^
  /sc onlogon ^
  /f ^
  /rl HIGHEST

if %errorlevel% equ 0 (
    echo [OK] Server startup scheduled at login
) else (
    echo [FAIL] Could not create server startup task
)

echo.
echo Done. Run "schtasks /query /tn BishopAI*" to verify.
pause
