@echo off
echo Checking virtual environment...

if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup_venv.bat first to create it.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Checking if requirements are installed...
venv\Scripts\python.exe -c "import rembg, onnxruntime" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Required packages not found!
    echo Please run install_requirements.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo Running U-2-Net Segmentation Application...
echo.
echo Using Python: %VIRTUAL_ENV%\Scripts\python.exe
echo.

venv\Scripts\python.exe app.py

echo.
echo Application finished.
pause
