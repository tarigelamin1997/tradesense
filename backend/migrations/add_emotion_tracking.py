"""
Migration to add emotion tracking columns to trade_notes table
"""
from sqlalchemy import text
from backend.core.db.session import get_db

def migrate_emotion_tracking():
    """Add emotion tracking columns to trade_notes table"""
    
    db = next(get_db())
    
    try:
        # Add emotion tracking columns
        db.execute(text("""
            ALTER TABLE trade_notes 
            ADD COLUMN emotion VARCHAR(50);
        """))
        
        db.execute(text("""
            ALTER TABLE trade_notes 
            ADD COLUMN confidence_score INTEGER;
        """))
        
        db.execute(text("""
            ALTER TABLE trade_notes 
            ADD COLUMN mental_triggers TEXT;
        """))
        
        # Add indexes for better performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trade_notes_emotion 
            ON trade_notes(emotion);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trade_notes_confidence 
            ON trade_notes(confidence_score);
        """))
        
        db.commit()
        print("✅ Successfully added emotion tracking columns")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_emotion_tracking()
