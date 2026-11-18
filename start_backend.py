#!/usr/bin/env python3
"""Simple backend startup script"""
import os
import sys

# Add backend to path
sys.path.insert(0, "/home/tarigelamin/Desktop/tradesense/src/backend")

# Set environment variables
if not os.environ.get('DATABASE_URL'):
    raise SystemExit('Set DATABASE_URL in your environment or .env (see docs/configuration.md)')
if not os.environ.get('SECRET_KEY'):
    raise SystemExit('Set SECRET_KEY in your environment or .env (see docs/configuration.md)')
if not os.environ.get('JWT_SECRET_KEY'):
    raise SystemExit('Set JWT_SECRET_KEY in your environment or .env (see docs/configuration.md)')
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