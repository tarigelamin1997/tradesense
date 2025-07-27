#!/usr/bin/env python3
"""Simple backend startup script"""
import os
import sys

# Add backend to path
sys.path.insert(0, "/home/tarigelamin/Desktop/tradesense/src/backend")

# Set environment variables
os.environ["DATABASE_URL"] = "postgresql://tradesense_user:REDACTED@localhost:5433/tradesense"
os.environ["SECRET_KEY"] = "REDACTED"
os.environ["JWT_SECRET_KEY"] = "REDACTED"
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