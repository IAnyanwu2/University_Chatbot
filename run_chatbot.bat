@echo off
echo Starting GSU CS RAG Chatbot...
echo.

REM Check if virtual environment exists
if not exist venv\ (
    echo Virtual environment not found. Please run setup_venv.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check if Ollama is running
echo Checking Ollama connection...
python -c "import requests; requests.get('http://localhost:11434/api/tags', timeout=3)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Ollama server not detected!
    echo Please install and start Ollama:
    echo 1. Download from https://ollama.ai
    echo 2. Run: ollama pull mistral:7b
    echo 3. Ollama should start automatically
    echo.
    echo Starting anyway (will use fallback responses)...
)

echo Starting Flask application...
python app.py