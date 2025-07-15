
"""
Migration: Add AI critique fields to trades table
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def upgrade_database():
    """Add AI critique fields to trades table"""
    
    db_path = Path(__file__).parent.parent / "tradesense.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Add AI critique columns
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN ai_critique TEXT
        """)
        
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN critique_generated_at DATETIME
        """)
        
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN critique_confidence INTEGER
        """)
        
        conn.commit()
        logger.info("Successfully added AI critique fields to trades table")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("AI critique fields already exist in trades table")
        else:
            logger.error(f"Error adding AI critique fields: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    upgrade_database()
