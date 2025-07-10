
#!/usr/bin/env python3
"""
Migration to add playbooks table
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def create_playbooks_table():
    """Create the playbooks table"""
    # Database path relative to backend directory
    db_path = backend_dir / "tradesense.db"
    
    # Ensure the database file exists
    if not db_path.exists():
        print(f"Creating database at: {db_path}")
        # Touch the file to create it
        db_path.touch()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Creating playbooks table...")
        
        # Create playbooks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playbooks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                entry_criteria TEXT NOT NULL,
                exit_criteria TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add playbook_id column to trades table if it doesn't exist
        print("Adding playbook_id column to trades table...")
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN playbook_id TEXT")
            print("✅ Added playbook_id column to trades table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✅ playbook_id column already exists in trades table")
            else:
                raise
        
        # Create index for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_playbooks_user_id ON playbooks(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_playbook_id ON trades(playbook_id)")
        
        conn.commit()
        print("✅ Playbooks migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_playbooks_table()
    sys.exit(0 if success else 1)
