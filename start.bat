@echo off
title Company Intelligence System
echo.
echo  ============================================
echo   Company Intelligence System - Starting...
echo  ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python is not installed on this computer.
    echo.
    echo  Please download and install Python from:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, check the box that says
    echo  "Add Python to PATH" at the bottom of the installer.
    echo.
    echo  After installing Python, double-click this file again.
    echo.
    pause
    exit /b 1
)

:: Install dependencies (only runs once, skips if already installed)
echo  Installing required packages (first time only)...
pip install -q -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo  Package installation had issues. Trying again...
    pip install flask pandas openpyxl requests python-dotenv >nul 2>&1
)
echo  Done.
echo.

:: Open the browser after a short delay
echo  Opening your browser...
timeout /t 2 /nobreak >nul
start http://localhost:5000

:: Start the app
echo.
echo  ============================================
echo   App is running at: http://localhost:5000
echo   Upload your Excel file in the browser.
echo.
echo   To stop: close this window or press Ctrl+C
echo  ============================================
echo.
python app.py
pause
