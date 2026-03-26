@echo off
cd /d C:\Users\richm\.claude\skills\bishop-research-agent
call venv\Scripts\activate.bat

if not exist logs mkdir logs

echo [%date% %time%] Starting Bishop AI Research Agent >> logs\agent.log 2>&1
python main.py --once >> logs\agent.log 2>&1
echo [%date% %time%] Run complete >> logs\agent.log 2>&1
