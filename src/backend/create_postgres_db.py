#!/usr/bin/env python3
"""
Create PostgreSQL database for TradeSense
"""
import psycopg2
from psycopg2 import sql
import sys

def create_database():
    """Create the tradesense database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'tradesense'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier('tradesense')
            ))
            print("✅ Database 'tradesense' created successfully!")
        else:
            print("ℹ️  Database 'tradesense' already exists")
        
        cursor.close()
        conn.close()
        
        # Test connection to the new database
        test_conn = psycopg2.connect(
            host="localhost",
            database="tradesense",
            user="postgres",
            password="postgres"
        )
        test_conn.close()
        print("✅ Successfully connected to tradesense database")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure PostgreSQL is running and the postgres user has password 'postgres'")
        print("You may need to update pg_hba.conf or set the postgres password:")
        print("  sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'postgres';\"")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)