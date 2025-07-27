
"""
Verification script for Strategy Lab database requirements
Ensures playbook and trade relationships are properly set up
"""

import sqlite3
import sys
from pathlib import Path

def verify_strategy_lab_setup():
    """Verify that the database has the required tables and relationships for Strategy Lab"""
    
    db_path = Path(__file__).parent.parent / "tradesense.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verifying Strategy Lab database setup...")
        
        # Check if playbooks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='playbooks'")
        if not cursor.fetchone():
            print("❌ Playbooks table not found!")
            return False
        else:
            print("✅ Playbooks table exists")
        
        # Check if trades table has playbook_id column
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'playbook_id' not in columns:
            print("❌ trades.playbook_id column not found!")
            return False
        else:
            print("✅ trades.playbook_id column exists")
        
        # Check for some sample data
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"📊 Found {trade_count} trades in database")
        
        cursor.execute("SELECT COUNT(*) FROM playbooks")
        playbook_count = cursor.fetchone()[0]
        print(f"📊 Found {playbook_count} playbooks in database")
        
        # Check for trades with playbooks
        cursor.execute("SELECT COUNT(*) FROM trades WHERE playbook_id IS NOT NULL")
        linked_trades = cursor.fetchone()[0]
        print(f"📊 Found {linked_trades} trades linked to playbooks")
        
        conn.close()
        print("✅ Strategy Lab database verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_strategy_lab_setup()
    sys.exit(0 if success else 1)
