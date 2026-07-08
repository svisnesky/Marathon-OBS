@echo off
REM Step 1: pick where the "RUNNER DOWN +XP" popup appears on screen.
REM Make sure OBS Virtual Camera is running first.
call "%~dp0_env.bat"
if errorlevel 1 exit /b 1
echo.
echo   Drag a box around the center RUNNER DOWN / +XP popup area, then press ENTER.
echo.
python calibrate.py
pause
