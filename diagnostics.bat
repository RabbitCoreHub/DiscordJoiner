@echo off
chcp 65001 >nul
title IceHub Diagnostics

echo ========================================
echo    IceHub Diagnostics
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    echo 💡 Install Python from https://python.org
) else (
    echo ✅ Python found
)

echo.
echo [2/4] Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pip not found
    echo 💡 Install pip or run start.bat
) else (
    echo ✅ Pip found
)

echo.
echo [3/4] Checking requirements.txt...
if exist "requirements.txt" (
    echo ✅ requirements.txt found
    echo 📦 Libraries to install:
    type requirements.txt
) else (
    echo ❌ requirements.txt missing
)

echo.
echo [4/4] Checking main.py...
if exist "main.py" (
    echo ✅ main.py found
) else (
    echo ❌ main.py missing
)

echo.
echo ========================================
echo DIAGNOSTICS COMPLETE
echo ========================================
echo.
echo NEXT STEPS:
echo 1. If Python is missing: Run start.bat
echo 2. If Python is installed: Run install_deps.bat
echo 3. Run: python main.py
echo.
pause
