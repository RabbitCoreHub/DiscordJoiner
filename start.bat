@echo off
chcp 65001 >nul
title IceHub Setup

echo.
echo ========================================
echo    IceHub Setup
echo ========================================
echo.

REM ============================================================================
REM Check Python installation
REM ============================================================================
echo [1/3] Checking Python installation...

python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found on system.
    echo.
    echo Checking for local Python installer...

    if exist "Python\Python.exe" (
        echo Found local Python installer!
        echo.
        echo Opening Python installer for you...
        echo Please install Python with default settings and "Add to PATH" option.
        echo.
        echo After installation is complete, press any key to continue...
        echo.

        start "Python Installer" "Python\Python.exe"
        pause >nul

        REM Check if Python is now installed
        python --version >nul 2>&1
        if errorlevel 1 (
            echo ERROR: Python installation failed or PATH not updated!
            echo Please install Python manually and ensure it's added to PATH.
            echo.
            echo Manual installation instructions:
            echo 1. Go to: https://python.org/downloads/
            echo 2. Download Python 3.11+ installer
            echo 3. Run installer with "Add Python to PATH" option
            echo 4. Run this script again
            pause
            exit /b 1
        )

        echo Python installed successfully!
    ) else (
        echo Local Python installer not found!
        echo.
        echo Please install Python manually:
        echo.
        echo OPTION 1 - Using local installer:
        echo - Place Python installer as Python\Python.exe
        echo - Run this script again
        echo.
        echo OPTION 2 - Download from website:
        echo - Go to: https://python.org/downloads/
        echo - Download Python 3.11+ installer
        echo - Run installer with "Add to PATH" option
        echo - Run this script again
        echo.
        pause
        exit /b 1
    )
) else (
    echo Python is already installed.
)

REM ============================================================================
REM Install pip if needed
REM ============================================================================
echo.
echo [2/3] Setting up pip...

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Pip not found. Installing pip...

    if exist "Python\get-pip.py" (
        python "Python\get-pip.py" --quiet
        if errorlevel 1 (
            echo ERROR: Failed to install pip from local file!
            echo Please install pip manually or check Python installation.
            pause
            exit /b 1
        )
        echo Pip installed from local file.
    ) else (
        echo Downloading get-pip.py...
        curl -L -o "Python\get-pip.py" "https://bootstrap.pypa.io/get-pip.py" >nul 2>&1
        if exist "Python\get-pip.py" (
            python "Python\get-pip.py" --quiet
            echo Pip installed from internet.
        ) else (
            echo ERROR: Could not download get-pip.py!
            echo Please install pip manually.
            pause
            exit /b 1
        )
    )
) else (
    echo Pip is already installed.
)

REM ============================================================================
REM Install required libraries
REM ============================================================================
echo.
echo [3/3] Installing required libraries...

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    echo Please ensure requirements.txt exists in the current directory.
    pause
    exit /b 1
)

echo Installing libraries from requirements.txt...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo ERROR: Failed to install some libraries!
    echo Please check your internet connection or try again.
    pause
    exit /b 1
)

echo.
echo All libraries installed successfully!

echo.
echo ========================================
echo Starting IceHub...
echo ========================================
echo.

REM Run the main application
python main.py

echo.
echo IceHub finished!
echo Press any key to exit...
pause >nul
