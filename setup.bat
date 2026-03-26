@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Fashion Wardrobe - Setup ^& Run (Windows)
echo ========================================
echo.

REM 1) Create venv if missing
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment in .\venv ...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python is installed and on PATH.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM 2) Install requirements
echo.
echo Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

REM 3) Start API
echo.
echo Starting API server...
echo - Docs: http://localhost:8000/docs
echo - If you changed API_PORT in .env, use that port instead.
echo.
venv\Scripts\python.exe api.py

echo.
echo API stopped.
pause
