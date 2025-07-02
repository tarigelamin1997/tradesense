import os
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
import sqlite3
import streamlit as st
import logging
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)


class AuthDatabase:
    """Simplified database manager for authentication."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the authentication database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Simple users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # Simple sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")

    def create_user(self, email: str, password: str, first_name: str = "", last_name: str = "") -> Dict:
        """Create a new user account."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            password_hash = pwd_context.hash(password)

            cursor.execute('''
                INSERT INTO users (email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (email.lower().strip(), password_hash, first_name, last_name))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {"success": True, "user_id": user_id}

        except sqlite3.IntegrityError:
            return {"success": False, "error": "Email already exists"}
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            return {"success": False, "error": "Registration failed"}

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password."""
        try:
            email = email.strip().lower()
            if not self._is_valid_email(email):
                return None

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, email, password_hash, first_name, last_name, is_active
                FROM users WHERE email = ? AND is_active = TRUE
            ''', (email,))

            user = cursor.fetchone()
            conn.close()

            if user and pwd_context.verify(password, user[2]):
                return {
                    "id": user[0],
                    "email": user[1],
                    "first_name": user[3],
                    "last_name": user[4]
                }
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")

        return None

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def create_session(self, user_id: int) -> str:
        """Create a new user session."""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO user_sessions (id, user_id, expires_at)
                VALUES (?, ?, ?)
            ''', (session_id, user_id, expires_at))

            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()

            return session_id
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            return ""

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate a user session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT s.user_id, u.email, u.first_name, u.last_name
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.id = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = TRUE
            ''', (session_id,))

            session = cursor.fetchone()
            conn.close()

            if session:
                return {
                    "id": session[0],
                    "user_id": session[0],
                    "email": session[1],
                    "first_name": session[2],
                    "last_name": session[3]
                }
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")

        return None


class AuthManager:
    """Simplified authentication manager."""

    def __init__(self):
        try:
            self.db = AuthDatabase()
        except Exception as e:
            logger.error(f"Auth manager initialization error: {str(e)}")
            self.db = None

    def register_user(self, email: str, password: str, first_name: str = "", last_name: str = "") -> Dict:
        """Register a new user."""
        if not self.db:
            return {"success": False, "error": "Authentication system unavailable"}

        # Basic password validation
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}

        return self.db.create_user(email, password, first_name, last_name)

    def login_user(self, email: str, password: str) -> Dict:
        """Login user with email and password."""
        if not self.db:
            return {"success": False, "error": "Authentication system unavailable"}

        user = self.db.authenticate_user(email, password)

        if user:
            session_id = self.db.create_session(user["id"])
            if session_id:
                return {"success": True, "session_id": session_id, "user": user}

        return {"success": False, "error": "Invalid credentials"}

    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user."""
        if not self.db:
            return None

        session_id = st.session_state.get('session_id')
        if session_id:
            return self.db.validate_session(session_id)
        return None


def render_auth_interface():
    """Render the main authentication interface."""
    try:
        auth_manager = AuthManager()

        # Check if user is already authenticated
        current_user = auth_manager.get_current_user()

        if current_user:
            return current_user

        # Show login/register interface
        st.title("🔐 TradeSense Authentication")
        st.write("Please log in to access the trading analytics dashboard.")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            render_login_form(auth_manager)

        with tab2:
            render_register_form(auth_manager)

        return None

    except Exception as e:
        st.error(f"Authentication system error: {str(e)}")
        st.info("Please refresh the page to retry.")
        return None


def render_login_form(auth_manager: AuthManager):
    """Render login form."""
    with st.form("login_form"):
        st.subheader("Login to Your Account")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.form_submit_button("🔓 Login", type="primary"):
            if email and password:
                result = auth_manager.login_user(email, password)

                if result['success']:
                    st.session_state.session_id = result['session_id']
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result['error'])
            else:
                st.error("Please enter both email and password")


def render_register_form(auth_manager: AuthManager):
    """Render registration form."""
    with st.form("register_form"):
        st.subheader("Create New Account")

        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
        with col2:
            last_name = st.text_input("Last Name")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.form_submit_button("🚀 Create Account", type="primary"):
            if not all([first_name, last_name, email, password, confirm_password]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                result = auth_manager.register_user(email, password, first_name, last_name)

                if result['success']:
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error(result['error'])