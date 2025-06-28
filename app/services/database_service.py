"""
Database Service
Handles all database operations and connections
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

from app.config.settings import settings
from app.models.user import User

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.db_path = settings.DATABASE_URL or "tradesense.db"
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    entry_time DATETIME NOT NULL,
                    exit_time DATETIME,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    pnl REAL,
                    side TEXT NOT NULL,
                    strategy TEXT,
                    notes TEXT,
                    user_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            conn.commit()
            logger.info("Database initialized successfully")

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    hashed_password=row['hashed_password'],
                    is_active=bool(row['is_active']),
                    is_admin=bool(row['is_admin']),
                    created_at=row['created_at']
                )
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    hashed_password=row['hashed_password'],
                    is_active=bool(row['is_active']),
                    is_admin=bool(row['is_admin']),
                    created_at=row['created_at']
                )
            return None

    async def create_user(self, user_data: dict) -> User:
        """Create new user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, hashed_password, is_active, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                user_data['email'],
                user_data['hashed_password'],
                user_data.get('is_active', True),
                user_data.get('is_admin', False)
            ))

            user_id = cursor.lastrowid
            conn.commit()

            return User(
                id=user_id,
                username=user_data['username'],
                email=user_data['email'],
                hashed_password=user_data['hashed_password'],
                is_active=user_data.get('is_active', True),
                is_admin=user_data.get('is_admin', False),
                created_at=datetime.now()
            )

def test_connection() -> bool:
    """Test database connection"""
    try:
        db = DatabaseService()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False