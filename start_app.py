#!/usr/bin/env python3
"""
Holiday Destinations Generator - Python Startup Script
This script properly configures the Python path and starts the Streamlit application.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    print("🌍 Holiday Destinations Generator - Enterprise Edition")
    print("=" * 60)
    
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set PYTHONPATH environment variable for subprocesses
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    if current_pythonpath:
        os.environ['PYTHONPATH'] = f"{project_root}{os.pathsep}{current_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = str(project_root)
    
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path configured: {project_root}")
    
    # Verify dependencies
    print("\n🔍 Checking dependencies...")
    try:
        import streamlit
        import openai
        import langchain
        print("✅ All required packages found")
        
        # Check Streamlit version for badge compatibility
        import streamlit as st_check
        st_version = st_check.__version__
        print(f"📦 Streamlit version: {st_version}")
        
        # Parse version to check if it's >= 1.29.0
        version_parts = st_version.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major < 1 or (major == 1 and minor < 29):
            print("⚠️  Streamlit version is older than 1.29.0")
            print("   Some features may use fallback implementations")
            print("💡 To upgrade: pip install --upgrade streamlit>=1.29.0")
        else:
            print("✅ Streamlit version supports all features")
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n💡 To fix this, run:")
        print("   pip install -r requirements.txt")
        return 1
    
    # Verify configuration
    print("\n🔧 Checking configuration...")
    try:
        from src.config.settings import settings
        if settings.openai_api_key:
            print("✅ OpenAI API key configured")
        else:
            print("⚠️  No OpenAI API key found")
            print("\n💡 To fix this:")
            print("   1. Create a file named 'api_key.txt' with your OpenAI API key")
            print("   2. Or set the OPENAI_API_KEY environment variable")
            return 1
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1
    
    # Start Streamlit application
    print("\n🚀 Starting application...")
    print("🌐 Opening browser at: http://localhost:8501")
    print("\n💡 Press Ctrl+C to stop the application")
    print("=" * 60)
    
    try:
        # Build streamlit command
        streamlit_app_path = project_root / "src" / "ui" / "streamlit_app.py"
        cmd = [sys.executable, "-m", "streamlit", "run", str(streamlit_app_path)]
        
        # Run streamlit
        subprocess.run(cmd, cwd=project_root)
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 