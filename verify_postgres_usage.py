#!/usr/bin/env python3
"""Verify that the backend is actually using PostgreSQL"""
import os
import sys
sys.path.append('src/backend')

from core.config import settings
from core.db.session import DATABASE_URL, engine

print("=== Verifying Database Configuration ===")
print()

# Check environment
print("Environment Variables:")
print(f"  DATABASE_URL from env: {os.getenv('DATABASE_URL', 'Not set')}")
print()

# Check settings
print("Settings Configuration:")
print(f"  settings.database_url: {settings.database_url}")
print()

# Check actual database connection
print("Active Database Connection:")
print(f"  DATABASE_URL in session.py: {DATABASE_URL}")
print(f"  Engine URL: {engine.url}")
print()

# Test connection
try:
    with engine.connect() as conn:
        if "postgresql" in str(engine.url):
            from sqlalchemy import text
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("✅ Connected to PostgreSQL!")
            print(f"   Version: {version}")
            
            # Count users
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"   Users in database: {count}")
        else:
            print("⚠️  Connected to SQLite (not PostgreSQL)")
            print(f"   Database file: {engine.url}")
except Exception as e:
    print(f"❌ Connection error: {e}")

print()
print("Recommendation:")
if "postgresql" not in str(engine.url):
    print("The backend is still using SQLite. To use PostgreSQL:")
    print("1. Make sure DATABASE_URL is set in your environment")
    print("2. Restart the backend server")
    print("3. You can set it with: export DATABASE_URL=postgresql://postgres:postgres@localhost/tradesense")
else:
    print("✅ Backend is correctly configured to use PostgreSQL!")