#!/usr/bin/env python3
"""Simple backend startup script"""
import os
import sys

# Add backend to path
sys.path.insert(0, "/home/tarigelamin/Desktop/tradesense/src/backend")

# Set environment variables
os.environ["DATABASE_URL"] = "postgresql://tradesense_user:2ca9bfcf1a40257caa7b4be903c7fe22@localhost:5433/tradesense"
os.environ["SECRET_KEY"] = "9e7d6c8a1f4b2e5a7c3d9f6b8e2a5c7d9f1b4e6a8c3d9f6b2e5a7c1d9f6b8e3a"
os.environ["JWT_SECRET_KEY"] = "3f8b7e2a1d6c9e4f7a2b5d8e1c4f7a9b2e5d8c1f4a7b9e2d5c8f1a4b7e9d2c5f"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# Run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )