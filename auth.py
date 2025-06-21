# Replacing the login_user function to fix login button functionality and session handling
import streamlit as st
import sqlite3
import hashlib
import secrets
import jwt
import bcrypt
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from functools import wraps
import re

logger = logging.getLogger(__name__)

class AuthManager:
    """Enhanced authentication manager with partner support."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.secret_key = "tradesense_jwt_secret_key_2024"  # In production, use environment variable
        self.init_database()

    def init_database(self):
        """Initialize authentication and partner databases."""
        try:
            # Ensure database directory exists
            import os
            db_dir = os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.'
            os.makedirs(db_dir, exist_ok=True)

            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Enable foreign keys
            cursor.execute('PRAGMA foreign_keys = ON')

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    partner_id INTEGER,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP NULL
                )
            ''')

            # Partners table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    api_key TEXT UNIQUE,
                    settings TEXT,
                    branding TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    billing_plan TEXT DEFAULT 'basic',
                    revenue_share REAL DEFAULT 0.0
                )
            ''')

            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Check if session_token column exists, add if missing
            cursor.execute("PRAGMA table_info(user_sessions)")
            session_columns = [col[1] for col in cursor.fetchall()]
            if 'session_token' not in session_columns:
                cursor.execute('ALTER TABLE user_sessions ADD COLUMN session_token TEXT')

            # Login attempts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    ip_address TEXT,
                    success BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            if 'conn' in locals():
                conn.close()
            raise

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        return True, "Password is strong"

    def register_user(self, username: str, email: str, password: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """Register a new user."""
        conn = None
        try:
            # Validate inputs
            if not username or not email or not password:
                return {"success": False, "message": "All fields are required"}

            if not self.validate_email(email):
                return {"success": False, "message": "Invalid email format"}

            is_strong, strength_msg = self.validate_password_strength(password)
            if not is_strong:
                return {"success": False, "message": strength_msg}

            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            # First, check what columns exist in the users table
            cursor.execute("PRAGMA table_info(users)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Check if user already exists
            if 'username' in column_names:
                cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            else:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))

            if cursor.fetchone():
                return {"success": False, "message": "User with this email already exists"}

            # Hash password and create user
            password_hash = self.hash_password(password)

            # Build insert query based on available columns
            if 'username' in column_names:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, partner_id)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, password_hash, partner_id))
            else:
                # Fallback to email-only registration if username column doesn't exist
                cursor.execute('''
                    INSERT INTO users (email, password_hash, partner_id)
                    VALUES (?, ?, ?)
                ''', (email, password_hash, partner_id))

            user_id = cursor.lastrowid
            conn.commit()

            logger.info(f"User registered successfully: {username}")
            return {"success": True, "message": "User registered successfully", "user_id": user_id}

        except sqlite3.IntegrityError as e:
            logger.error(f"Registration integrity error: {e}")
            return {"success": False, "message": "Username or email already exists"}
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "message": f"Registration failed: {str(e)}"}
        finally:
            if conn:
                conn.close()

    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and create session."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()

            # Get user by username or email
            cursor.execute("""
                SELECT id, username, email, password_hash, role, is_active, created_at 
                FROM users 
                WHERE (username = ? OR email = ?) AND is_active = 1
            """, (username, username))

            user = cursor.fetchone()

            if not user:
                conn.close()
                return {"success": False, "message": "Invalid credentials"}

            user_id, db_username, email, password_hash, role, is_active, created_at = user

            # Verify password
            if not self.verify_password(password, password_hash):
                conn.close()
                return {"success": False, "message": "Invalid credentials"}

            # Create session with retry logic for database locks
            session_token = self.generate_session_token()
            expires_at = datetime.now() + timedelta(days=30)

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cursor.execute("""
                        INSERT INTO user_sessions (user_id, session_token, expires_at, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, session_token, expires_at, datetime.now()))

                    conn.commit()
                    break
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        time.sleep(0.1 * (attempt + 1))  # Progressive backoff
                        continue
                    else:
                        raise e

            conn.close()

            # Store in session state
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.username = db_username
            st.session_state.user_role = role
            st.session_state.session_token = session_token

            logger.info(f"User logged in successfully: {email}")

            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user_id,
                    "username": db_username,
                    "email": email,
                    "role": role
                }
            }

        except sqlite3.Error as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": "Database error occurred"}
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": "An unexpected error occurred"}

    def generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    def _create_session(self, user_id: int) -> str:
        """Create user session token."""
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()

        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE')
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            # Return token anyway, session storage is not critical for basic auth
            if 'conn' in locals():
                try:
                    conn.close()
                except:
                    pass

        return session_token

    def _log_login_attempt(self, username: str, success: bool):
        """Log login attempt."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO login_attempts (username, success, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (username, success, "127.0.0.1", "streamlit"))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging login attempt: {e}")

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user."""
        return st.session_state.get('current_user')

    def logout_user(self):
        """Logout current user."""
        if 'current_user' in st.session_state:
            user = st.session_state.current_user
            session_token = user.get('session_token')

            if session_token:
                # Invalidate session in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
                conn.commit()
                conn.close()

            logger.info(f"User logged out: {user.get('username')}")

        # Clear session state
        for key in ['current_user', 'authenticated', 'trade_data', 'analytics_result']:
            if key in st.session_state:
                del st.session_state[key]

    def create_partner(self, name: str, partner_type: str, settings: Dict = None) -> Dict[str, Any]:
        """Create a new partner."""
        try:
            api_key = f"ts_{secrets.token_urlsafe(32)}"
            settings_json = str(settings or {})

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO partners (name, type, api_key, settings)
                VALUES (?, ?, ?, ?)
            ''', (name, partner_type, api_key, settings_json))

            partner_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {"success": True, "partner_id": partner_id, "api_key": api_key}

        except Exception as e:
            logger.error(f"Partner creation error: {e}")
            return {"success": False, "message": "Partner creation failed"}

    def get_partner(self, partner_id: int) -> Optional[Dict[str, Any]]:
        """Get partner by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM partners WHERE id = ?', (partner_id,))
            partner = cursor.fetchone()
            conn.close()

            if partner:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, partner))
            return None

        except Exception as e:
            logger.error(f"Error getting partner: {e}")
            return None

    def test_database_connection(self) -> Dict[str, Any]:
        """Test database connection and return status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Test basic query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # Check if users table exists and has proper schema
            cursor.execute("PRAGMA table_info(users)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Repair database if needed
            self._repair_database_schema(cursor, column_names)

            # Test users table specifically
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            conn.commit()
            conn.close()

            return {
                "success": True,
                "message": "Database connection successful",
                "tables_found": len(tables),
                "user_count": user_count,
                "columns": column_names
            }

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {
                "success": False,
                "message": f"Database connection failed: {str(e)}"
            }

    def _repair_database_schema(self, cursor, existing_columns):
        """Repair database schema by adding missing columns."""
        required_columns = {
            'username': 'TEXT UNIQUE',
            'email': 'TEXT UNIQUE NOT NULL',
            'password_hash': 'TEXT NOT NULL',
            'partner_id': 'INTEGER',
            'role': 'TEXT DEFAULT "user"',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'last_login': 'TIMESTAMP',
            'is_active': 'BOOLEAN DEFAULT 1',
            'two_factor_enabled': 'BOOLEAN DEFAULT 0',
            'failed_login_attempts': 'INTEGER DEFAULT 0',
            'locked_until': 'TIMESTAMP NULL'
        }

        for column, definition in required_columns.items():
            if column not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE users ADD COLUMN {column} {definition}"
                    cursor.execute(alter_sql)
                    logger.info(f"Added missing column: {column}")
                except Exception as e:
                    logger.warning(f"Could not add column {column}: {e}")
                    # Continue with other columns

def require_auth(func):
    """Decorator to require authentication for functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_manager = AuthManager()
        current_user = auth_manager.get_current_user()

        if not current_user:
            st.warning("🔐 Please login to access this feature")
            return None

        return func(*args, **kwargs)

    return wrapper

def check_partner_access(partner_id: str, user: Dict) -> bool:
    """Check if user has access to partner resources."""
    if not user:
        return False

    # Admin users have access to all partners
    if user.get('role') == 'admin':
        return True

    # Users can only access their own partner
    return user.get('partner_id') == partner_id

def render_auth_sidebar():
    """Render authentication sidebar."""
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()

    with st.sidebar:
        st.markdown("---")

        if current_user:
            st.success(f"👋 Welcome, {current_user['username']}!")

            if current_user.get('partner_id'):
                partner = auth_manager.get_partner(current_user['partner_id'])
                if partner:
                    st.info(f"🏢 {partner['name']}")

            if st.button("🚪 Logout", key="logout_btn"):
                auth_manager.logout_user()
                st.rerun()
        else:
            st.subheader("🔐 Authentication")

            tab1, tab2 = st.tabs(["Login", "Register"])

            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username/Email")
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("Login")

                    if submit and username and password:
                        result = auth_manager.login_user(username, password)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])

            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Username")
                    new_email = st.text_input("Email")
                    new_password = st.text_input("Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    submit_reg = st.form_submit_button("Register")

                    if submit_reg and new_username and new_email and new_password:
                        if new_password != confirm_password:
                            st.error("Passwords don't match")
                        else:
                            result = auth_manager.register_user(new_username, new_email, new_password)
                            if result["success"]:
                                st.success(result["message"])
                            else:
                                st.error(result["message"])
`