#!/usr/bin/env python3
"""Check SQLite database for existing data before PostgreSQL migration"""
import sqlite3
import os
from pathlib import Path

def check_database(db_path):
    """Check SQLite database for tables and data"""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    print(f"\n=== Checking database: {db_path} ===")
    print(f"File size: {os.path.getsize(db_path) / 1024:.2f} KB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database")
            conn.close()
            return
        
        print(f"Tables found: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
            
            # Show sample data for users table
            if table_name == 'users' and count > 0:
                cursor.execute(f"SELECT id, username, email FROM {table_name} LIMIT 5")
                users = cursor.fetchall()
                print("    Sample users:")
                for user in users:
                    print(f"      ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error reading database: {e}")

# Check all possible database locations
db_locations = [
    "./tradesense.db",
    "./src/backend/tradesense.db",
    "./data/tradesense.db"
]

for db_path in db_locations:
    if os.path.exists(db_path):
        check_database(db_path)
    else:
        print(f"\nDatabase not found: {db_path}")