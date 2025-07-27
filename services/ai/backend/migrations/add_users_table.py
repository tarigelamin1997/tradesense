
#!/usr/bin/env python3
"""
Create users table for authentication system
"""
import sqlite3
import os
import sys

def add_users_table():
    """Add users table to the database"""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'tradesense.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                reset_password_token TEXT,
                reset_password_expires DATETIME,
                last_login DATETIME,
                trading_experience TEXT,
                preferred_markets TEXT,
                timezone TEXT DEFAULT 'UTC',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active)
        ''')
        
        conn.commit()
        print("✅ Users table created successfully")
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("✅ Users table verified successfully")
        else:
            print("❌ Users table verification failed")
            
    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("👤 Creating Users Authentication System...")
    add_users_table()
    print("✅ Authentication migration completed!")
