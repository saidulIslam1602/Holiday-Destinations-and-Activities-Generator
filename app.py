"""
Enterprise Holiday Destinations Generator
Main application entry point for the Streamlit application.

Usage:
    streamlit run app.py

This replaces the old main.py with enterprise-grade architecture.
"""

import os
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the Streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main() 