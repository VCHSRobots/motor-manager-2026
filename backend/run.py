#!/usr/bin/env python3
"""
Run the FastAPI server.
"""

import uvicorn
import os
import sys

# Change to project root
os.chdir(os.path.dirname(__file__))
os.chdir('..')

# Add current directory to path
sys.path.insert(0, '.')

# Set PYTHONPATH for subprocess
os.environ['PYTHONPATH'] = '.'

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)