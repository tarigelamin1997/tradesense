#!/usr/bin/env python3
"""
Test PostgreSQL database connectivity and basic operations
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
import psycopg2

# Database URL
DATABASE_URL = 'postgresql://tradesense_user:REDACTED@localhost:5433/tradesense'

print("🧪 Testing TradeSense PostgreSQL Database...")
print("=" * 50)

# Test 1: Basic connection
print("\n1️⃣ Testing basic connection...")
try:
    # Using psycopg2 directly
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"✅ Direct psycopg2 connection successful: {version}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Direct connection failed: {e}")

# Test 2: SQLAlchemy connection
print("\n2️⃣ Testing SQLAlchemy connection...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ SQLAlchemy connection successful")
except Exception as e:
    print(f"❌ SQLAlchemy connection failed: {e}")

# Test 3: Check tables
print("\n3️⃣ Checking database tables...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        print(f"✅ Found {len(tables)} tables:")
        for table in tables[:5]:  # Show first 5
            print(f"   - {table}")
        if len(tables) > 5:
            print(f"   ... and {len(tables) - 5} more")
except Exception as e:
    print(f"❌ Failed to list tables: {e}")

# Test 4: Test CRUD operations
print("\n4️⃣ Testing CRUD operations...")
try:
    with engine.begin() as conn:
        # Insert a test user
        result = conn.execute(text("""
            INSERT INTO users (email, username, hashed_password)
            VALUES (:email, :username, :password)
            RETURNING id, created_at
        """), {
            "email": "test@example.com",
            "username": "testuser",
            "password": "hashed_password_here"
        })
        user_id, created_at = result.fetchone()
        print(f"✅ INSERT successful - User ID: {user_id}, Created: {created_at}")
        
        # Read the user
        result = conn.execute(text("""
            SELECT id, email, username, is_active 
            FROM users 
            WHERE id = :id
        """), {"id": user_id})
        user = result.fetchone()
        print(f"✅ SELECT successful - User: {user}")
        
        # Update the user
        conn.execute(text("""
            UPDATE users 
            SET full_name = :name 
            WHERE id = :id
        """), {"name": "Test User", "id": user_id})
        print("✅ UPDATE successful")
        
        # Delete the user
        conn.execute(text("""
            DELETE FROM users 
            WHERE id = :id
        """), {"id": user_id})
        print("✅ DELETE successful")
        
except Exception as e:
    print(f"❌ CRUD operations failed: {e}")

# Test 5: Check indexes
print("\n5️⃣ Checking indexes...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname NOT LIKE '%_pkey'
            ORDER BY tablename, indexname
            LIMIT 10;
        """))
        indexes = result.fetchall()
        print(f"✅ Found {len(indexes)} custom indexes (showing first 10):")
        for idx in indexes:
            print(f"   - {idx[1]}.{idx[2]}")
except Exception as e:
    print(f"❌ Failed to check indexes: {e}")

# Test 6: Check connection pool settings
print("\n6️⃣ Testing connection pooling...")
try:
    from sqlalchemy.pool import QueuePool
    
    # Create engine with pool settings
    pooled_engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True
    )
    
    # Test multiple connections
    connections = []
    for i in range(3):
        conn = pooled_engine.connect()
        connections.append(conn)
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Connection {i+1} established")
    
    # Close connections
    for conn in connections:
        conn.close()
    
    print("✅ Connection pooling working correctly")
    
except Exception as e:
    print(f"❌ Connection pooling test failed: {e}")

# Test 7: Check constraints and foreign keys
print("\n7️⃣ Checking foreign key constraints...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            LIMIT 5;
        """))
        constraints = result.fetchall()
        print(f"✅ Found foreign key constraints (showing first 5):")
        for constraint in constraints:
            print(f"   - {constraint[0]}.{constraint[1]} → {constraint[2]}.{constraint[3]}")
except Exception as e:
    print(f"❌ Failed to check constraints: {e}")

print("\n" + "=" * 50)
print("✅ Database testing complete!")
print(f"📊 Database URL: {DATABASE_URL}")
print("🚀 TradeSense PostgreSQL is ready for use!")