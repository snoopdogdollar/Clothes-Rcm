@echo off
echo Installing requirements in virtual environment...

if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup_venv.bat first to create it.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing packages from requirements.txt...
echo This may take several minutes...
echo.

venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install some requirements!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo All requirements installed successfully!
echo ========================================
echo.
echo You can now run the application with run.bat
echo.
pause
