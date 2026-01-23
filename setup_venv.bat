@echo off
echo Creating virtual environment...

python -m venv venv

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create virtual environment!
    echo Make sure Python is installed and in your PATH.
    pause
    exit /b 1
)

echo.
echo Virtual environment created successfully!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate
echo.
echo Then install requirements:
echo   pip install -r requirements.txt
echo.
echo Or run install_requirements.bat to install automatically.
echo.
pause
