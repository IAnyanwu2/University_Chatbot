@echo off
echo ======================================
echo GSU CS RAG Chatbot Setup Script
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama is not installed or not in PATH
    echo Please install Ollama from https://ollama.ai
    echo.
    echo After installing Ollama, run:
    echo   ollama pull mistral:7b
    echo.
    pause
    exit /b 1
)

echo ✓ Python detected
echo ✓ Ollama detected
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ======================================
echo Setup completed successfully!
echo ======================================
echo.
echo To start the chatbot:
echo   1. Make sure Ollama is running: ollama serve
echo   2. Pull a model if you haven't: ollama pull mistral:7b
echo   3. Activate environment: venv\Scripts\activate
echo   4. Start chatbot: python app.py
echo   5. Open browser: http://localhost:5000
echo.
pause