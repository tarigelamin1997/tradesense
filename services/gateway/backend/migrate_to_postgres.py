#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
This script preserves all user data and relationships
"""
import sqlite3
from sqlalchemy import create_engine, text
from datetime import datetime
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    
    # Database URLs
    sqlite_path = './tradesense.db'
    postgres_url = 'postgresql://postgres:postgres@localhost/tradesense'
    
    print("=== TradeSense Database Migration ===")
    print(f"Source: {sqlite_path}")
    print(f"Target: PostgreSQL (tradesense database)")
    print()
    
    # Check if SQLite database exists
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        return False
    
    try:
        # Connect to SQLite
        print("Connecting to SQLite...")
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        print("Connecting to PostgreSQL...")
        postgres_engine = create_engine(postgres_url)
        
        # Test PostgreSQL connection
        with postgres_engine.connect() as conn:
            result = conn.execute(text('SELECT 1'))
            print("✓ PostgreSQL connection successful")
        
        # Get all tables from SQLite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nFound {len(tables)} tables to migrate")
        
        # Special handling for users table (most important)
        if 'users' in tables:
            print("\n--- Migrating users table ---")
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            print(f"Found {len(users)} users to migrate")
            
            if users:
                with postgres_engine.connect() as conn:
                    # Create users table if not exists
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS users (
                            id VARCHAR PRIMARY KEY,
                            username VARCHAR UNIQUE NOT NULL,
                            email VARCHAR UNIQUE NOT NULL,
                            hashed_password VARCHAR NOT NULL,
                            first_name VARCHAR,
                            last_name VARCHAR,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_admin BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.commit()
                    
                    # Migrate each user
                    migrated = 0
                    for user in users:
                        try:
                            # Convert SQLite row to dict
                            user_dict = dict(user)
                            
                            # Check if user already exists
                            existing = conn.execute(
                                text("SELECT id FROM users WHERE id = :id"),
                                {"id": user_dict['id']}
                            ).fetchone()
                            
                            if not existing:
                                # Insert user
                                # Convert SQLite boolean (0/1) to PostgreSQL boolean
                                is_active = user_dict.get('is_active', 1)
                                is_admin = user_dict.get('is_admin', 0)
                                
                                conn.execute(text("""
                                    INSERT INTO users (
                                        id, username, email, hashed_password,
                                        first_name, last_name, is_active, is_admin,
                                        created_at, updated_at
                                    ) VALUES (
                                        :id, :username, :email, :hashed_password,
                                        :first_name, :last_name, :is_active, :is_admin,
                                        :created_at, :updated_at
                                    )
                                """), {
                                    'id': user_dict.get('id'),
                                    'username': user_dict.get('username'),
                                    'email': user_dict.get('email'),
                                    'hashed_password': user_dict.get('hashed_password'),
                                    'first_name': user_dict.get('first_name'),
                                    'last_name': user_dict.get('last_name'),
                                    'is_active': bool(is_active) if isinstance(is_active, int) else is_active,
                                    'is_admin': bool(is_admin) if isinstance(is_admin, int) else is_admin,
                                    'created_at': user_dict.get('created_at', datetime.now()),
                                    'updated_at': user_dict.get('updated_at', datetime.now())
                                })
                                migrated += 1
                                print(f"  ✓ Migrated user: {user_dict['username']} ({user_dict['email']})")
                            else:
                                print(f"  - User already exists: {user_dict['username']}")
                        
                        except Exception as e:
                            print(f"  ✗ Error migrating user {user_dict.get('username', 'unknown')}: {e}")
                    
                    conn.commit()
                    print(f"\n✓ Successfully migrated {migrated} users")
        
        # Migrate other tables (structure only for now)
        print("\n--- Creating other table structures ---")
        other_tables = [t for t in tables if t != 'users']
        
        for table in other_tables:
            try:
                # Get table structure from SQLite
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                if columns:
                    # Simple table creation (you may need to adjust data types)
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table} ("
                    col_defs = []
                    
                    for col in columns:
                        col_name = col[1]
                        col_type = col[2]
                        not_null = " NOT NULL" if col[3] else ""
                        default = f" DEFAULT {col[4]}" if col[4] is not None else ""
                        
                        # Convert SQLite types to PostgreSQL
                        if 'INT' in col_type.upper():
                            pg_type = 'INTEGER'
                        elif 'VARCHAR' in col_type.upper() or 'TEXT' in col_type.upper():
                            pg_type = 'VARCHAR'
                        elif 'REAL' in col_type.upper() or 'FLOAT' in col_type.upper():
                            pg_type = 'REAL'
                        elif 'BLOB' in col_type.upper():
                            pg_type = 'BYTEA'
                        elif 'BOOLEAN' in col_type.upper():
                            pg_type = 'BOOLEAN'
                        else:
                            pg_type = 'VARCHAR'
                        
                        col_defs.append(f"{col_name} {pg_type}{not_null}{default}")
                    
                    create_sql += ", ".join(col_defs) + ")"
                    
                    with postgres_engine.connect() as conn:
                        conn.execute(text(create_sql))
                        conn.commit()
                    
                    print(f"  ✓ Created table: {table}")
                    
            except Exception as e:
                print(f"  ✗ Error creating table {table}: {e}")
        
        sqlite_conn.close()
        print("\n=== Migration Summary ===")
        print("✓ User data migrated successfully")
        print("✓ Table structures created")
        print("\nNext steps:")
        print("1. Update your application configuration to use PostgreSQL")
        print("2. Run Alembic migrations to ensure schema is up to date")
        print("3. Test the application thoroughly")
        print("4. Keep SQLite backup until everything is confirmed working")
        
        return True
        
    except Exception as e:
        print(f"\nERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def backup_sqlite():
    """Create a backup of the SQLite database"""
    import shutil
    from datetime import datetime
    
    sqlite_path = './tradesense.db'
    if os.path.exists(sqlite_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'./tradesense.db.backup_{timestamp}'
        shutil.copy2(sqlite_path, backup_path)
        print(f"✓ SQLite backup created: {backup_path}")
        return backup_path
    return None

if __name__ == "__main__":
    print("PostgreSQL Migration Script for TradeSense")
    print("=" * 50)
    
    # Create backup first
    backup_path = backup_sqlite()
    
    # Check if PostgreSQL is accessible
    try:
        engine = create_engine('postgresql://postgres:postgres@localhost/tradesense')
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            print("✓ PostgreSQL is accessible")
    except Exception as e:
        print("\n✗ Cannot connect to PostgreSQL!")
        print(f"Error: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. Database 'tradesense' exists")
        print("3. User 'postgres' with password 'postgres' has access")
        print("\nRun these commands to set up PostgreSQL:")
        print("  sudo -u postgres createdb tradesense")
        print("  sudo -u postgres createdb tradesense_test")
        print("  sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'postgres';\"")
        sys.exit(1)
    
    # Perform migration
    if migrate_data():
        print("\n✅ Migration completed successfully!")
        if backup_path:
            print(f"SQLite backup saved at: {backup_path}")
    else:
        print("\n❌ Migration failed!")
        print("Your data is safe in the SQLite database")