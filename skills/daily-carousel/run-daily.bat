@echo off
cd /d C:\Users\richm\.claude\skills\daily-carousel
call venv\Scripts\activate.bat

if not exist logs mkdir logs

echo [%date% %time%] Starting Daily Carousel Pipeline >> logs\agent.log 2>&1
python main.py >> logs\agent.log 2>&1
echo [%date% %time%] Run complete >> logs\agent.log 2>&1
