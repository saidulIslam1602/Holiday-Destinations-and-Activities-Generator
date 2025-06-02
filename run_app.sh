#!/bin/bash

# Holiday Destinations Generator - Startup Script
# Sets up Python path and runs the Streamlit application

echo ""
echo "========================================"
echo "  Holiday Destinations Generator"
echo "  Enterprise Travel AI Assistant"
echo "========================================"
echo ""

# Set the Python path to include the current directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if required packages are installed
echo "Checking dependencies..."
if ! python -c "import streamlit, openai, langchain" 2>/dev/null; then
    echo ""
    echo "ERROR: Missing required packages!"
    echo "Please install dependencies:"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Check if API key is configured
if ! python -c "from src.config.settings import settings; print('API Key configured:', bool(settings.openai_api_key))" 2>/dev/null; then
    echo ""
    echo "ERROR: Configuration issue!"
    echo "Please ensure your OpenAI API key is set in api_key.txt or environment variable."
    echo ""
    exit 1
fi

echo "Dependencies OK!"
echo "Starting application..."
echo ""

# Start the Streamlit application
streamlit run src/ui/streamlit_app.py

# Check if there was an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Application stopped with error."
    read -p "Press any key to continue..."
fi 