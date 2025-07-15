#!/usr/bin/env python3
"""Test PostgreSQL connection and verify migration"""
from sqlalchemy import create_engine, text
import sys

def test_postgres_connection():
    """Test PostgreSQL connection and check migrated data"""
    postgres_url = 'postgresql://postgres:postgres@localhost/tradesense'
    
    try:
        print("Testing PostgreSQL connection...")
        engine = create_engine(postgres_url)
        
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text('SELECT version()'))
            version = result.scalar()
            print(f"✓ Connected to PostgreSQL")
            print(f"  Version: {version}")
            
            # Check for tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"\n✓ Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("\n⚠ No tables found. Database might be empty.")
            
            # Check users table specifically
            if 'users' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"\n✓ Users table found with {user_count} users")
                
                if user_count > 0:
                    result = conn.execute(text("""
                        SELECT id, username, email 
                        FROM users 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """))
                    users = result.fetchall()
                    print("\nSample users:")
                    for user in users:
                        print(f"  - {user[1]} ({user[2]})")
            
            return True
            
    except Exception as e:
        print(f"\n✗ PostgreSQL connection failed!")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Is PostgreSQL installed? Run: psql --version")
        print("2. Is PostgreSQL running? Run: sudo systemctl status postgresql")
        print("3. Does the database exist? Run: sudo -u postgres psql -l | grep tradesense")
        print("4. Check connection settings in .env file")
        return False

if __name__ == "__main__":
    print("PostgreSQL Connection Test for TradeSense")
    print("=" * 50)
    
    if test_postgres_connection():
        print("\n✅ PostgreSQL is ready for TradeSense!")
    else:
        print("\n❌ PostgreSQL setup needed")
        sys.exit(1)