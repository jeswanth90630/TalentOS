@echo off
title TalentOS - AI Talent Intelligence & Hiring Platform Launcher
color 0A
cls
echo =========================================================================
echo                    🎯 TalentOS Hiring Platform
echo      Open-source AI-powered Talent Intelligence Infrastructure
echo =========================================================================
echo.
echo [1/3] Checking environment & installing dependencies...
python -m pip install -q -r requirements.txt

echo.
echo [2/3] Starting TalentOS Application Server on http://localhost:8000 ...
start "" "http://localhost:8000"

echo.
echo [3/3] Launching web browser...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
