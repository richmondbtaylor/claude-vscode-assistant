@echo off
echo =======================================
echo  Bishop AI LinkedIn DM Automation
echo =======================================
echo.

REM Check that .env exists
if not exist "%~dp0.env" (
    echo ERROR: .env file not found.
    echo Copy .env.example to .env and fill in your values first.
    pause
    exit /b 1
)

REM Check that linkedin_cookies.json exists
if not exist "%~dp0linkedin_cookies.json" (
    echo LinkedIn cookies not found. Running save_cookies.py first...
    echo A browser window will open. Log in to LinkedIn, then press Enter here.
    echo.
    "C:\Users\richm\AppData\Local\Programs\Python\Python311\python.exe" "%~dp0save_cookies.py"
    echo.
)

REM Start ngrok in a new window
echo Starting ngrok tunnel on port 3001...
start "ngrok" cmd /k "ngrok http 3001"

REM Wait a moment for ngrok to start
timeout /t 3 /nobreak >nul

REM Start the FastAPI server in a new window
echo Starting FastAPI server...
start "Bishop DM Server" cmd /k "cd /d "%~dp0" && "C:\Users\richm\AppData\Local\Programs\Python\Python311\python.exe" -m uvicorn server:app --port 3001"

echo.
echo =======================================
echo  Both windows are now running.
echo.
echo  IMPORTANT: Copy the ngrok URL from
echo  the ngrok window (https://xxxx.ngrok...)
echo  and paste it into your .env file as:
echo  LOCAL_SERVER_PUBLIC_URL=https://xxxx...
echo.
echo  Then update n8n with the same URL.
echo =======================================
echo.
pause
