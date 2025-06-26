
#!/usr/bin/env python3
"""
Add Portfolio and EquitySnapshot models to database
"""
import sqlite3
import os
from datetime import datetime

def add_portfolio_tables():
    """Add portfolio-related tables to the database"""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'tradesense.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create portfolios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                initial_balance REAL DEFAULT 10000.0,
                current_balance REAL DEFAULT 10000.0,
                total_pnl REAL DEFAULT 0.0,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create equity_snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity_snapshots (
                id TEXT PRIMARY KEY,
                portfolio_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                balance REAL NOT NULL,
                daily_pnl REAL DEFAULT 0.0,
                total_pnl REAL DEFAULT 0.0,
                trade_count INTEGER DEFAULT 0,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
            )
        ''')
        
        # Create indices for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios (user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_equity_snapshots_portfolio_id ON equity_snapshots (portfolio_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_equity_snapshots_timestamp ON equity_snapshots (timestamp)
        ''')
        
        conn.commit()
        print("✅ Portfolio tables created successfully")
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if 'portfolios' in table_names and 'equity_snapshots' in table_names:
            print("✅ Tables verified successfully")
        else:
            print("❌ Table verification failed")
            
    except Exception as e:
        print(f"❌ Error creating portfolio tables: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🏦 Adding Portfolio Management Tables...")
    add_portfolio_tables()
    print("✅ Portfolio migration completed!")
