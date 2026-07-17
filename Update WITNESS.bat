@echo off
REM Double-click to update WITNESS to the latest version (no typing, no curl).
cd /d "%~dp0"
echo Checking for updates...
echo.
.venv\Scripts\python -c "import updater; print(updater.check_and_update('.'))"
echo.
echo ------------------------------------------------------------
echo Done. Close this window and open WITNESS.
echo ------------------------------------------------------------
pause
