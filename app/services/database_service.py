
"""
Database Service
Handles all database operations and connections
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        is_admin BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        entry_time TIMESTAMP NOT NULL,
                        exit_time TIMESTAMP,
                        pnl REAL,
                        commission REAL DEFAULT 0,
                        tags TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        trade_id INTEGER,
                        tags TEXT,
                        mood TEXT,
                        confidence INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (trade_id) REFERENCES trades (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS email_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        email_type TEXT NOT NULL,
                        schedule_time TIME NOT NULL,
                        enabled BOOLEAN DEFAULT 1,
                        recipients TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Get user by username failed: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM users WHERE email = ?", (email,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Get user by email failed: {e}")
            return None

    async def create_user(self, user_data: Dict) -> Dict:
        """Create new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO users (username, email, hashed_password, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_data["username"],
                    user_data["email"],
                    user_data["hashed_password"],
                    user_data["created_at"],
                    user_data["is_active"]
                ))
                
                user_id = cursor.lastrowid
                user_data["id"] = user_id
                return user_data
        except Exception as e:
            logger.error(f"Create user failed: {e}")
            raise

    async def get_user_trades(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get user's trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM trades 
                    WHERE user_id = ? 
                    ORDER BY entry_time DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Get user trades failed: {e}")
            return []

    async def create_trade(self, trade_data: Dict) -> Dict:
        """Create new trade"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO trades (
                        user_id, symbol, side, quantity, entry_price, exit_price,
                        entry_time, exit_time, pnl, commission, tags, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data["user_id"], trade_data["symbol"], trade_data["side"],
                    trade_data["quantity"], trade_data["entry_price"], trade_data.get("exit_price"),
                    trade_data["entry_time"], trade_data.get("exit_time"), trade_data.get("pnl"),
                    trade_data.get("commission", 0), trade_data.get("tags"), trade_data.get("notes")
                ))
                
                trade_id = cursor.lastrowid
                trade_data["id"] = trade_id
                return trade_data
        except Exception as e:
            logger.error(f"Create trade failed: {e}")
            raise

def test_connection() -> bool:
    """Test database connection"""
    try:
        db = DatabaseService()
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
