#!/usr/bin/env python3
"""
Custom script to handle date migration with data conversion
"""
from sqlalchemy import create_engine, text
from datetime import datetime
import re

DATABASE_URL = "postgresql://postgres:postgres@localhost/tradesense"

def convert_date_string(date_str):
    """Convert various date string formats to PostgreSQL timestamp"""
    if not date_str or date_str == 'NULL':
        return None
    
    # Remove any quotes
    date_str = date_str.strip("'\"")
    
    # Try different formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    
    print(f"Warning: Could not parse date '{date_str}'")
    return None

def fix_date_columns():
    """Fix date columns by converting string dates to proper timestamps"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # First, let's check if we have any data in trades
            result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            trade_count = result.scalar()
            print(f"Found {trade_count} trades to process")
            
            if trade_count > 0:
                # Create temporary columns with proper type
                print("Creating temporary columns...")
                conn.execute(text("""
                    ALTER TABLE trades 
                    ADD COLUMN IF NOT EXISTS entry_time_temp TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS exit_time_temp TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS created_at_temp TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS reflection_timestamp_temp TIMESTAMP
                """))
                
                # Copy and convert data
                print("Converting date data...")
                
                # For entry_time
                conn.execute(text("""
                    UPDATE trades 
                    SET entry_time_temp = 
                        CASE 
                            WHEN entry_time IS NOT NULL AND entry_time != '' 
                            THEN entry_time::timestamp
                            ELSE NULL
                        END
                """))
                
                # For exit_time
                conn.execute(text("""
                    UPDATE trades 
                    SET exit_time_temp = 
                        CASE 
                            WHEN exit_time IS NOT NULL AND exit_time != '' 
                            THEN exit_time::timestamp
                            ELSE NULL
                        END
                """))
                
                # For created_at
                conn.execute(text("""
                    UPDATE trades 
                    SET created_at_temp = 
                        CASE 
                            WHEN created_at IS NOT NULL AND created_at != '' 
                            THEN created_at::timestamp
                            ELSE CURRENT_TIMESTAMP
                        END
                """))
                
                # For reflection_timestamp
                conn.execute(text("""
                    UPDATE trades 
                    SET reflection_timestamp_temp = 
                        CASE 
                            WHEN reflection_timestamp IS NOT NULL AND reflection_timestamp != '' 
                            THEN reflection_timestamp::timestamp
                            ELSE NULL
                        END
                """))
                
                # Drop old columns and rename new ones
                print("Replacing columns...")
                conn.execute(text("""
                    ALTER TABLE trades 
                    DROP COLUMN entry_time,
                    DROP COLUMN exit_time,
                    DROP COLUMN created_at,
                    DROP COLUMN reflection_timestamp
                """))
                
                conn.execute(text("ALTER TABLE trades RENAME COLUMN entry_time_temp TO entry_time"))
                conn.execute(text("ALTER TABLE trades RENAME COLUMN exit_time_temp TO exit_time"))
                conn.execute(text("ALTER TABLE trades RENAME COLUMN created_at_temp TO created_at"))
                conn.execute(text("ALTER TABLE trades RENAME COLUMN reflection_timestamp_temp TO reflection_timestamp"))
            
            # Also fix other tables with date columns
            tables_to_fix = [
                ('users', ['created_at', 'updated_at', 'last_login', 'reset_password_expires']),
                ('portfolios', ['created_at', 'updated_at']),
                ('trade_notes', ['created_at', 'updated_at']),
                ('tags', ['created_at', 'updated_at']),
            ]
            
            for table, columns in tables_to_fix:
                # Check if table exists
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                if not result.scalar():
                    continue
                
                print(f"\nFixing {table} table...")
                for col in columns:
                    try:
                        # Check column type
                        result = conn.execute(text(f"""
                            SELECT data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}' AND column_name = '{col}'
                        """))
                        data_type = result.scalar()
                        
                        if data_type and 'char' in data_type.lower():
                            print(f"  Converting {col}...")
                            conn.execute(text(f"""
                                ALTER TABLE {table} 
                                ADD COLUMN IF NOT EXISTS {col}_temp TIMESTAMP
                            """))
                            
                            conn.execute(text(f"""
                                UPDATE {table} 
                                SET {col}_temp = 
                                    CASE 
                                        WHEN {col} IS NOT NULL AND {col} != '' 
                                        THEN {col}::timestamp
                                        ELSE NULL
                                    END
                            """))
                            
                            conn.execute(text(f"""
                                ALTER TABLE {table} 
                                DROP COLUMN {col}
                            """))
                            
                            conn.execute(text(f"""
                                ALTER TABLE {table} 
                                RENAME COLUMN {col}_temp TO {col}
                            """))
                    except Exception as e:
                        print(f"    Warning: Could not convert {table}.{col}: {e}")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Date columns fixed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error: {e}")
            raise

if __name__ == "__main__":
    fix_date_columns()