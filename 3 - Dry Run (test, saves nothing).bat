@echo off
REM Step 3: full live rehearsal. Detects kills and prints them, but does NOT
REM save clips. Great for confirming it counts correctly before going live.
call "%~dp0_env.bat"
if errorlevel 1 exit /b 1
echo.
echo   DRY RUN - detecting kills but saving nothing. Press Ctrl-C to stop.
echo.
python main.py --dry-run
pause
