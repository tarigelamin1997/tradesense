#!/usr/bin/env python3
"""Add missing columns to PostgreSQL users table"""
from sqlalchemy import create_engine, text
from core.config import settings
from datetime import datetime

def add_missing_columns():
    """Add missing columns to match User model"""
    engine = create_engine(settings.database_url)
    
    print("=== Fixing PostgreSQL Schema ===")
    
    with engine.connect() as conn:
        # List of columns to add with their types
        columns_to_add = [
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("verification_token", "VARCHAR"),
            ("reset_password_token", "VARCHAR"),
            ("reset_password_expires", "TIMESTAMP"),
            ("last_login", "TIMESTAMP"),
            ("trading_experience", "VARCHAR"),
            ("preferred_markets", "TEXT"),
            ("timezone", "VARCHAR DEFAULT 'UTC'"),
            ("is_admin", "BOOLEAN DEFAULT FALSE")  # Also add is_admin if missing
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = '{column_name}'
                """))
                
                if not result.fetchone():
                    # Add column
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"⏭️  Column already exists: {column_name}")
                    
            except Exception as e:
                print(f"❌ Error adding {column_name}: {e}")
                conn.rollback()
        
        # Verify columns
        print("\n=== Verifying Users Table Schema ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        
        print("Current columns:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
            
        # Test a query
        print("\n=== Testing Query ===")
        try:
            result = conn.execute(text("""
                SELECT id, username, email, is_verified, is_admin 
                FROM users 
                LIMIT 1
            """))
            row = result.fetchone()
            if row:
                print(f"✅ Query successful: {row[1]} ({row[2]})")
            else:
                print("⚠️  No users found")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            
        print("\n✅ Schema fix complete!")

if __name__ == "__main__":
    add_missing_columns()