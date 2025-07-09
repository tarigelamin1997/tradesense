
"""
Migration to add daily_emotion_reflections table
"""
from sqlalchemy import text
from backend.core.db.session import get_db

def migrate_daily_reflections():
    """Create daily_emotion_reflections table"""
    
    db = next(get_db())
    
    try:
        # Create daily reflections table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_emotion_reflections (
                id VARCHAR PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id VARCHAR NOT NULL,
                reflection_date DATE NOT NULL,
                mood_score INTEGER,
                summary TEXT,
                dominant_emotion VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Add indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reflections_user_id 
            ON daily_emotion_reflections(user_id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reflections_user_date 
            ON daily_emotion_reflections(user_id, reflection_date);
        """))
        
        # Add unique constraint on user_id + reflection_date
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_reflections_unique_user_date 
            ON daily_emotion_reflections(user_id, reflection_date);
        """))
        
        db.commit()
        print("✅ Successfully created daily_emotion_reflections table")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_daily_reflections()
