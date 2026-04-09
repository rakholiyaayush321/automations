@echo off
REM Daily Job Application Runner - 10 AM IST
REM Add this to Windows Task Scheduler to run daily

cd /d "%~dp0"
echo [%DATE% %TIME%] Starting job application pipeline...
python run_daily.py >> logs\cron_run.log 2>&1
echo [%DATE% %TIME%] Pipeline finished.
