#!/usr/bin/env python3
"""
Main entry point for the GhostBack application.
"""

import sys
import os
from pathlib import Path


def main():
    """Main function to run the application."""
    print("Welcome to GhostBack!")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {Path(__file__).parent}")
    
    # Add your application logic here
    print("\nApplication is ready to run!")


if __name__ == "__main__":
    main()
