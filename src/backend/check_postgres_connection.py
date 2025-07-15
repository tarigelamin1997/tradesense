#!/usr/bin/env python3
"""Check PostgreSQL connection and verify data"""
from sqlalchemy import create_engine, text
from core.config import settings
import os

print("=== PostgreSQL Connection Check ===")
print(f"Database URL from settings: {settings.database_url}")
print(f"DATABASE_URL env var: {os.getenv('DATABASE_URL', 'Not set')}")
print()

try:
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        # Test connection
        result = conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL connection successful")
        
        # Check PostgreSQL version
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"PostgreSQL version: {version.split(',')[0]}")
        print()
        
        # Check tables
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"Tables in database ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")
        print()
        
        # Check users
        if 'users' in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"Users in database: {count}")
            
            if count > 0:
                result = conn.execute(text("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC LIMIT 5"))
                print("\nUsers found:")
                for row in result:
                    print(f"  - {row[1]} ({row[2]}) - Created: {row[3]}")
                    
                # Check password hash format
                result = conn.execute(text("SELECT username, LEFT(hashed_password, 10) as pwd_start FROM users LIMIT 1"))
                row = result.fetchone()
                if row:
                    print(f"\nPassword hash format check:")
                    print(f"  User: {row[0]}")
                    print(f"  Hash starts with: {row[1]}... (should start with $2b$ for bcrypt)")
            else:
                print("⚠️  No users found in database!")
        else:
            print("❌ Users table not found!")
            
        # Check if there's a specific schema issue
        result = conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'users'
        """))
        schemas = result.fetchall()
        if schemas:
            print(f"\nUsers table found in schemas: {schemas}")
            
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()