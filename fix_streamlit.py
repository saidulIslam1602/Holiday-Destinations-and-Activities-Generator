#!/usr/bin/env python3
"""
Quick fix script for Streamlit badge compatibility issue.
Upgrades Streamlit to a compatible version.
"""

import subprocess
import sys

def main():
    print("🔧 Streamlit Compatibility Fix")
    print("=" * 40)
    
    try:
        import streamlit as st
        current_version = st.__version__
        print(f"📦 Current Streamlit version: {current_version}")
        
        # Parse version
        version_parts = current_version.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major < 1 or (major == 1 and minor < 29):
            print("⚠️  This version doesn't support st.badge()")
            print("🚀 Upgrading Streamlit...")
            
            # Upgrade Streamlit
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "streamlit>=1.29.0"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Streamlit upgraded successfully!")
                print("🔄 Please restart the application")
            else:
                print("❌ Failed to upgrade Streamlit")
                print(f"Error: {result.stderr}")
                return 1
        else:
            print("✅ Streamlit version is compatible!")
            
    except ImportError:
        print("❌ Streamlit not found")
        print("🚀 Installing Streamlit...")
        
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "streamlit>=1.29.0"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Streamlit installed successfully!")
        else:
            print("❌ Failed to install Streamlit")
            print(f"Error: {result.stderr}")
            return 1
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("\n💡 You can now start the application with:")
    print("   python start_app.py")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 