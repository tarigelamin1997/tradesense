import sqlite3
from sqlalchemy import create_engine, text

# Check if database exists and has tables
engine = create_engine('sqlite:///./tradesense.db')

with engine.connect() as conn:
    # Check tables
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    tables = result.fetchall()
    print("Tables in database:", tables)
    
    # Check users table
    try:
        result = conn.execute(text("SELECT COUNT(*) FROM users;"))
        count = result.scalar()
        print(f"Number of users: {count}")
        
        # Show first few users (without passwords)
        result = conn.execute(text("SELECT id, username, email, created_at FROM users LIMIT 5;"))
        users = result.fetchall()
        print("Users in database:")
        for user in users:
            print(f"  - {user}")
    except Exception as e:
        print(f"Error reading users table: {e}")