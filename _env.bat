@echo off
REM Shared setup/activation used by the other .bat launchers.
REM First run: creates the Python environment and installs dependencies.
REM Later runs: just activates it. Not meant to be run on its own.

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo   Python is not installed, or not on your PATH.
    echo   Install Python 3.10+ from https://www.python.org/downloads/windows/
    echo   and CHECK the box "Add python.exe to PATH" during install.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo   First-time setup: creating the environment and installing dependencies.
    echo   This downloads a lot (PyTorch for OCR) and can take several minutes.
    echo   Please leave this window open until it finishes.
    echo.
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo.
    echo   Setup complete.
    echo.
) else (
    call ".venv\Scripts\activate.bat"
)
