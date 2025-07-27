#!/usr/bin/env python3
"""
Initialize PostgreSQL database for TradeSense
Creates all tables and applies initial configuration
"""

import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set environment variable before importing
os.environ['DATABASE_URL'] = 'postgresql://tradesense_user:REDACTED@localhost:5433/tradesense'
os.environ['JWT_SECRET_KEY'] = 'REDACTED'
os.environ['DEBUG'] = 'False'

print("🚀 Initializing TradeSense PostgreSQL Database...")
print("=" * 50)

try:
    from core.db.session import engine, Base, create_tables, get_registered_models
    from sqlalchemy import text
    
    # Test connection
    print("🔍 Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to PostgreSQL: {version}")
    
    # Create all tables
    print("\n📊 Creating database tables...")
    create_tables()
    
    # List created tables
    print("\n📋 Created tables:")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"  ✓ {table}")
    
    print(f"\n✅ Database initialized successfully with {len(tables)} tables!")
    
except Exception as e:
    print(f"\n❌ Error initializing database: {e}")
    sys.exit(1)