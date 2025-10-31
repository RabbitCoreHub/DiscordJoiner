@echo off
chcp 65001 >nul
title IceHub Dependencies Installer

echo.
echo ========================================
echo    IceHub Dependencies Installer
echo ========================================
echo.

REM ============================================================================
REM Check Python installation
REM ============================================================================
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please run start.bat first to install Python.
    echo Or install Python manually from https://python.org
    echo.
    echo After installing Python, run this script again.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM ============================================================================
REM Update pip and install requirements
REM ============================================================================
echo [1/2] Updating pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo WARNING: Failed to update pip, but continuing...
)

echo.
echo [2/2] Installing libraries from requirements.txt...

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    echo Please ensure requirements.txt exists in the current directory.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo ERROR: Failed to install some libraries!
    echo Please check your internet connection or try again.
    echo.
    echo You can also try installing libraries one by one:
    echo python -m pip install keyboard
    echo python -m pip install websockets
    echo python -m pip install colorama
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo You can now run:
echo   - python main.py (run the application)
echo   - python -m PyInstaller main.py (build executable)
echo.

pause
