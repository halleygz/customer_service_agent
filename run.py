#!/usr/bin/env python3
"""
Entry point for running the CS Agent application.
Properly sets up the Python path and runs the interactive support agent.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
project_root = Path(__file__).parent
app_dir = project_root / "app"
sys.path.insert(0, str(app_dir))

# Change to app directory
os.chdir(str(app_dir))

# Import and execute main
if __name__ == "__main__":
    from main import run_conversation
    run_conversation()
