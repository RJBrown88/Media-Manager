@echo off
REM Build script for Windows
REM Compiles Video Manager into a standalone .exe

echo ============================================================
echo Video Manager - Windows Build Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not available
    pause
    exit /b 1
)

REM Install/upgrade PyInstaller if needed
echo Installing/upgrading build dependencies...
python -m pip install --upgrade PyInstaller>=5.0.0
echo.

REM Run the build script
echo Starting build process...
python build.py

echo.
echo ============================================================
echo Build process completed
echo ============================================================
echo.

pause
