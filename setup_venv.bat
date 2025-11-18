@echo off
echo Setting up GSU CS RAG Chatbot Environment...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo Virtual environment setup complete!
echo ============================================
echo.
echo To activate the environment in the future, run:
echo   venv\Scripts\activate
echo.
echo To deactivate when done, run:
echo   deactivate
echo.
echo Next steps:
echo 1. Make sure Ollama is installed and running
echo 2. Run: python test_system.py
echo 3. If tests pass, run: python app.py
echo.
pause