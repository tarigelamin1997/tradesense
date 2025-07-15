
#!/usr/bin/env python3
"""
Migration to add trade_reviews table
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def create_trade_reviews_table():
    """Create the trade_reviews table"""
    # Database path relative to backend directory
    db_path = backend_dir / "tradesense.db"
    
    # Ensure the database file exists
    if not db_path.exists():
        print(f"Creating database at: {db_path}")
        db_path.touch()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Creating trade_reviews table...")
        
        # Create trade_reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_reviews (
                id TEXT PRIMARY KEY,
                trade_id TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                quality_score INTEGER NOT NULL,
                mistakes TEXT,  -- JSON array of mistake tags
                mood TEXT,
                lesson_learned TEXT,
                execution_vs_plan INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_reviews_user_id ON trade_reviews(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_reviews_quality ON trade_reviews(user_id, quality_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_reviews_mood ON trade_reviews(user_id, mood)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_reviews_date ON trade_reviews(user_id, created_at)")
        
        conn.commit()
        print("✅ Trade reviews migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_trade_reviews_table()
    sys.exit(0 if success else 1)
