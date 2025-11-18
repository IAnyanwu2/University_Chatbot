@echo off
REM Background Cache Refresh for GSU CS Chatbot
REM This batch file can be scheduled to run daily via Windows Task Scheduler

cd /d "C:\Users\Ikean\Chatbot"
python refresh_scheduler.py

REM Log the completion
echo %date% %time% - Cache refresh completed >> refresh_log.txt