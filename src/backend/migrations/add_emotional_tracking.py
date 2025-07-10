
#!/usr/bin/env python3
"""
Add emotional tracking fields to trades table
"""

import sqlite3
import os
from pathlib import Path

def add_emotional_tracking_columns():
    """Add emotional tracking columns to trades table"""
    
    # Get database path
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "tradesense.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🧠 Adding emotional tracking columns to trades table...")
        
        # Add emotional tracking columns
        columns_to_add = [
            ("emotional_tags", "TEXT"),  # JSON array of emotional states
            ("reflection_notes", "TEXT"),  # Written reflection
            ("emotional_score", "INTEGER"),  # 1-10 emotional control score
            ("executed_plan", "BOOLEAN"),  # Did trader follow plan?
            ("post_trade_mood", "TEXT"),  # Post-trade mood
            ("reflection_timestamp", "TIMESTAMP")  # When reflection was added
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  Column {column_name} already exists")
                else:
                    print(f"❌ Error adding column {column_name}: {e}")
        
        # Create index for better performance on emotional queries
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_emotional_tags ON trades(emotional_tags)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_executed_plan ON trades(executed_plan)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_emotional_score ON trades(emotional_score)")
            print("✅ Created indexes for emotional tracking")
        except sqlite3.OperationalError as e:
            print(f"⚠️  Indexes may already exist: {e}")
        
        conn.commit()
        print("✅ Emotional tracking migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_emotional_tracking_columns()
