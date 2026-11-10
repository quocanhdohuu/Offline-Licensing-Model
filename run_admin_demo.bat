@echo off
cd /d "%~dp0"
title Tan Hung Ha - OLM Admin Portal
python launcher.py
if %errorlevel% neq 0 (
    echo.
    echo [!] ERROR: Could not run launcher.py with Python!
    echo Please make sure Python is installed and added to PATH.
    pause
)
