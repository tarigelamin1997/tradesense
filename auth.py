import streamlit as st
import sqlite3
import hashlib
import secrets
import jwt
import bcrypt
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

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
        try:
            # Validate inputs
            if not self.validate_email(email):
                return {"success": False, "message": "Invalid email format"}

            is_strong, strength_msg = self.validate_password_strength(password)
            if not is_strong:
                return {"success": False, "message": strength_msg}

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "message": "Username or email already exists"}

            # Hash password and create user
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, partner_id)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, partner_id))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"User registered successfully: {username}")
            return {"success": True, "message": "User registered successfully", "user_id": user_id}

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "message": "Registration failed"}

    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user login."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get user
            cursor.execute('''
                SELECT id, username, email, password_hash, partner_id, role, is_active, 
                       failed_login_attempts, locked_until
                FROM users WHERE username = ? OR email = ?
            ''', (username, username))

            user = cursor.fetchone()
            if not user:
                self._log_login_attempt(username, False)
                conn.close()
                return {"success": False, "message": "Invalid credentials"}

            user_id, username, email, password_hash, partner_id, role, is_active, failed_attempts, locked_until = user

            # Check if account is locked
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                conn.close()
                return {"success": False, "message": "Account temporarily locked. Try again later."}

            # Check if account is active
            if not is_active:
                conn.close()
                return {"success": False, "message": "Account is disabled"}

            # Verify password
            if not self.verify_password(password, password_hash):
                # Increment failed attempts
                failed_attempts += 1
                lock_time = None
                if failed_attempts >= 5:
                    lock_time = datetime.now() + timedelta(minutes=30)

                cursor.execute('''
                    UPDATE users SET failed_login_attempts = ?, locked_until = ?
                    WHERE id = ?
                ''', (failed_attempts, lock_time, user_id))
                conn.commit()

                self._log_login_attempt(username, False)
                conn.close()
                return {"success": False, "message": "Invalid credentials"}

            # Successful login - reset failed attempts
            cursor.execute('''
                UPDATE users SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE id = ?
            ''', (datetime.now(), user_id))

            # Create session
            session_token = self._create_session(user_id)

            conn.commit()
            conn.close()

            self._log_login_attempt(username, True)

            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "partner_id": partner_id,
                "role": role,
                "session_token": session_token
            }

            # Store in session state
            st.session_state.current_user = user_data
            st.session_state.authenticated = True

            logger.info(f"User logged in successfully: {username}")
            return {"success": True, "message": "Login successful", "user": user_data}

        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": "Login failed"}

    def _create_session(self, user_id: int) -> str:
        """Create user session token."""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        conn.commit()
        conn.close()

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