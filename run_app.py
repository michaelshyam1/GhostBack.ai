#!/usr/bin/env python3
"""
Launch script for GhostBack.ai
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit application."""
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("WARNING: It appears you're not in a virtual environment.")
        print("   Consider activating your virtual environment first:")
        print("   Windows: venv\\Scripts\\activate")
        print("   macOS/Linux: source venv/bin/activate")
        print()
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file from template...")
        env_example = Path("env_example.txt")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("   Please edit .env file and add your OpenAI API key")
        else:
            print("   env_example.txt not found, creating basic .env file...")
            env_file.write_text("OPENAI_API_KEY=your_openai_api_key_here\n")
    
    # Launch Streamlit
    print("Starting GhostBack.ai...")
    print("   The app will open in your default web browser")
    print("   Press Ctrl+C to stop the application")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\nGhostBack.ai stopped. Thank you for using the application!")
    except subprocess.CalledProcessError as e:
        print(f"ERROR starting the application: {e}")
        print("   Make sure Streamlit is installed: pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()
