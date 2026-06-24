#!/usr/bin/env python3
"""Run the FastAPI web server for customer/admin support interfaces."""

import sys
from pathlib import Path

import uvicorn


project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    uvicorn.run("app.api.server:app", host="0.0.0.0", port=8000, reload=True)
