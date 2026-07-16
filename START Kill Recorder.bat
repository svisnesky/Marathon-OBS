@echo off
REM The real thing: saves an OBS clip and bumps the counter on every kill.
REM See QUICKSTART.md for first-time setup.
call "%~dp0_env.bat"
if errorlevel 1 exit /b 1
echo.
echo   LIVE - saving a clip and counting each kill. Press Ctrl-C to stop.
echo.
python main.py
pause
