@echo off
cd /d C:\Users\richm\.claude\scripts
python linkedin_report.py >> linkedin_report_cron.log 2>&1
