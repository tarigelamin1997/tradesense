
"""
Migration to add playbooks table and update trades table
"""
import sqlite3
import uuid
from datetime import datetime

def migrate_database(db_path: str = "backend/tradesense.db"):
    """Add playbooks table and playbook_id column to trades table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create playbooks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playbooks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                entry_criteria TEXT NOT NULL,
                exit_criteria TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Check if playbook_id column exists in trades table
        cursor.execute("PRAGMA table_info(trades)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'playbook_id' not in columns:
            # Add playbook_id column to trades table
            cursor.execute("""
                ALTER TABLE trades 
                ADD COLUMN playbook_id TEXT 
                REFERENCES playbooks(id)
            """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_playbooks_user_id ON playbooks(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_playbooks_status ON playbooks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_playbook_id ON trades(playbook_id)")
        
        conn.commit()
        print("✅ Playbook migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
