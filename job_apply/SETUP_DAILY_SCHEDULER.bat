@echo off
REM ============================================================
REM  Setup Daily Job Applications - Windows Task Scheduler
REM ============================================================
REM Run this file AS ADMINISTRATOR to set up daily 10 AM IST cron

REM Step 1: Create the task
schtasks /create /tn "Ayush_Daily_Job_Applications" ^
 /tr "python.exe C:\Users\rakho\.openclaw\workspace\job_apply\run_daily.py" ^
 /sc daily /st 10:00 ^
 /ru SYSTEM ^
 /f

echo.
echo Task created! To verify:
echo   schtasks /query /tn "Ayush_Daily_Job_Applications"
echo.
echo To delete the task:
echo   schtasks /delete /tn "Ayush_Daily_Job_Applications" /f
echo.
pause
