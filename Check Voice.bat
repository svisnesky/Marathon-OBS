@echo off
REM Double-click to see which voice WITNESS will use (and why).
cd /d "%~dp0"
.venv\Scripts\python voice_check.py
