#!/usr/bin/env python3
"""
Run the Memento Box FastAPI server.
Usage: python run_server.py
"""
import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name} server...")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Server will be available at: http://localhost:8000")
    print(f"API docs will be available at: http://localhost:8000/docs")
    print(f"Alternative docs at: http://localhost:8000/redoc")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )