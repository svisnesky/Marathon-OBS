@echo off
REM Double-click WHILE Marathon is on screen (ideally with a RUNNER DOWN /
REM PRECISION DOWN popup showing) to see exactly what WITNESS captures.
cd /d "%~dp0"
.venv\Scripts\python diagnose.py
