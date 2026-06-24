#!/usr/bin/env python3
"""
Entry point for running the CS Agent application.
Properly sets up the Python path and runs the interactive support agent.
"""

import sys
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and execute main
if __name__ == "__main__":
    from app.main import run_conversation
    run_conversation()
