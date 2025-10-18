#!/usr/bin/env python3
"""
Launch script for GhostBack.ai API server
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the FastAPI application."""
    
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
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("⚠️  WARNING: OpenAI API key not configured!")
        print("   Please edit .env file and add your OpenAI API key")
        print("   The API will still start but chat features won't work without it.")
        print()
    
    # Launch FastAPI server
    print("Starting GhostBack.ai API server...")
    print("   API Documentation: http://localhost:8000/docs")
    print("   Alternative docs: http://localhost:8000/redoc")
    print("   Health check: http://localhost:8000/health")
    print("   Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nGhostBack.ai API server stopped. Thank you for using the application!")
    except subprocess.CalledProcessError as e:
        print(f"ERROR starting the API server: {e}")
        print("   Make sure uvicorn is installed: pip install uvicorn")
        sys.exit(1)

if __name__ == "__main__":
    main()
