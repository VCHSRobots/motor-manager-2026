#!/usr/bin/env python3
"""
Run the FastAPI server from the project root.
"""

import uvicorn
import os
import sys

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add current directory to path
sys.path.insert(0, '.')

# Set PYTHONPATH for subprocess
os.environ['PYTHONPATH'] = '.'

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)