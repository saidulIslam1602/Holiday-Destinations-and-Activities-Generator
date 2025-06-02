@echo off
REM Holiday Destinations Generator - Startup Script
REM Sets up Python path and runs the Streamlit application

echo.
echo ========================================
echo   Holiday Destinations Generator
echo   Enterprise Travel AI Assistant
echo ========================================
echo.

REM Set the Python path to include the current directory
set PYTHONPATH=%cd%

REM Check if required packages are installed
echo Checking dependencies...
python -c "import streamlit, openai, langchain" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Missing required packages!
    echo Please install dependencies:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if API key is configured
python -c "from src.config.settings import settings; print('API Key configured:', bool(settings.openai_api_key))" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Configuration issue!
    echo Please ensure your OpenAI API key is set in api_key.txt or environment variable.
    echo.
    pause
    exit /b 1
)

echo Dependencies OK!
echo Starting application...
echo.

REM Start the Streamlit application
streamlit run src/ui/streamlit_app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application stopped with error.
    pause
) 