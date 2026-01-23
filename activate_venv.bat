@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Virtual environment activated!
echo You can now install requirements with:
echo   pip install -r requirements.txt
echo.
echo Or run the application with:
echo   python app.py
echo.
echo To deactivate, type: deactivate
echo.

cmd /k
