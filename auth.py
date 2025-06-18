import os
import json
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import sqlite3
import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import jwt
import logging
from passlib.context import CryptContext
from credential_manager import CredentialManager
from logging_manager import log_error, LogCategory

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RateLimiter:
    """Simple rate limiter for authentication attempts."""

    def __init__(self):
        self.attempts = {}  # email -> {'count': int, 'last_attempt': datetime}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes

    def is_rate_limited(self, email: str) -> bool:
        """Check if email is rate limited."""
        now = datetime.now()

        if email not in self.attempts:
            return False

        attempt_data = self.attempts[email]

        # Reset if lockout period has passed
        if (now - attempt_data['last_attempt']).seconds > self.lockout_duration:
            del self.attempts[email]
            return False

        return attempt_data['count'] >= self.max_attempts

    def record_attempt(self, email: str, success: bool):
        """Record authentication attempt."""
        now = datetime.now()

        if success:
            # Clear attempts on successful login
            if email in self.attempts:
                del self.attempts[email]
        else:
            # Increment failed attempts
            if email not in self.attempts:
                self.attempts[email] = {'count': 1, 'last_attempt': now}
            else:
                self.attempts[email]['count'] += 1
                self.attempts[email]['last_attempt'] = now


class AuthDatabase:
    """Database manager for authentication and user management."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the authentication database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                first_name TEXT,
                last_name TEXT,
                partner_id TEXT,
                partner_role TEXT DEFAULT 'user',
                oauth_provider TEXT,
                oauth_id TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                subscription_tier TEXT DEFAULT 'free',
                api_key TEXT UNIQUE,
                UNIQUE(oauth_provider, oauth_id)
            )
        ''')

        # Partners table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partners (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                contact_email TEXT,
                api_key TEXT UNIQUE,
                webhook_url TEXT,
                settings JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                partner_id TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')

        # User trades table (partner-aware)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                partner_id TEXT,
                trade_data JSON NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_user(self, email: str, password: Optional[str] = None, 
                   first_name: str = "", last_name: str = "",
                   partner_id: Optional[str] = None, oauth_provider: Optional[str] = None,
                   oauth_id: Optional[str] = None) -> Dict:
        """Create a new user account."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            password_hash = None
            if password:
                password_hash = pwd_context.hash(password)

            api_key = self.generate_api_key()

            cursor.execute('''
                INSERT INTO users (email, password_hash, first_name, last_name, 
                                 partner_id, oauth_provider, oauth_id, api_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (email, password_hash, first_name, last_name, 
                  partner_id, oauth_provider, oauth_id, api_key))

            user_id = cursor.lastrowid
            conn.commit()

            # Track affiliate conversion if applicable
            try:
                from affiliate_integration import track_new_user_conversion
                track_new_user_conversion(user_id)
            except:
                pass  # Fail silently if affiliate system not available

            return {"success": True, "user_id": user_id, "api_key": api_key}

        except sqlite3.IntegrityError as e:
            return {"success": False, "error": "Email already exists"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password."""
        # Input validation
        if not email or not password:
            return None

        # Sanitize email input
        email = email.strip().lower()
        if not self._is_valid_email(email):
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, email, password_hash, first_name, last_name, 
                       partner_id, partner_role, is_active, subscription_tier
                FROM users WHERE email = ? AND is_active = TRUE
            ''', (email,))

            user = cursor.fetchone()

            if user and pwd_context.verify(password, user[2]):
                return {
                    "id": user[0],
                    "email": user[1],
                    "first_name": user[3],
                    "last_name": user[4],
                    "partner_id": user[5],
                    "partner_role": user[6],
                    "subscription_tier": user[8]
                }
        except Exception as e:
            log_error(f"Authentication error: {str(e)}", category=LogCategory.SYSTEM_ERROR)
        finally:
            conn.close()

        return None

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[Dict]:
        """Get user by OAuth provider and ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, email, first_name, last_name, partner_id, 
                   partner_role, is_active, subscription_tier
            FROM users WHERE oauth_provider = ? AND oauth_id = ? AND is_active = TRUE
        ''', (provider, oauth_id))

        user = cursor.fetchone()
        conn.close()

        if user:
            return {
                "id": user[0],
                "email": user[1],
                "first_name": user[2],
                "last_name": user[3],
                "partner_id": user[4],
                "partner_role": user[5],
                "subscription_tier": user[7]
            }
        return None

    def create_session(self, user_id: int, partner_id: Optional[str] = None) -> str:
        """Create a new user session."""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=30)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_sessions (id, user_id, partner_id, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, partner_id, expires_at))

        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))

        conn.commit()
        conn.close()

        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate a user session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.user_id, s.partner_id, u.email, u.first_name, u.last_name,
                   u.partner_role, u.subscription_tier
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = TRUE
        ''', (session_id,))

        session = cursor.fetchone()
        conn.close()

        if session:
            return {
                "user_id": session[0],
                "partner_id": session[1],
                "email": session[2],
                "first_name": session[3],
                "last_name": session[4],
                "partner_role": session[5],
                "subscription_tier": session[6]
            }
        return None

    def create_partner(self, partner_id: str, name: str, partner_type: str,
                      contact_email: str, settings: Dict = None) -> Dict:
        """Create a new partner."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            api_key = self.generate_api_key()
            settings_json = json.dumps(settings or {})

            cursor.execute('''
                INSERT INTO partners (id, name, type, contact_email, api_key, settings)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (partner_id, name, partner_type, contact_email, api_key, settings_json))

            conn.commit()
            return {"success": True, "api_key": api_key}

        except sqlite3.IntegrityError:
            return {"success": False, "error": "Partner ID already exists"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_partner(self, partner_id: str) -> Optional[Dict]:
        """Get partner information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, type, contact_email, settings, is_active
            FROM partners WHERE id = ?
        ''', (partner_id,))

        partner = cursor.fetchone()
        conn.close()

        if partner:
            return {
                "id": partner[0],
                "name": partner[1],
                "type": partner[2],
                "contact_email": partner[3],
                "settings": json.loads(partner[4]) if partner[4] else {},
                "is_active": partner[5]
            }
        return None

    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return f"ts_{secrets.token_urlsafe(32)}"


class AuthManager:
    """Main authentication manager."""

    def __init__(self):
        self.db = AuthDatabase()
        self.rate_limiter = RateLimiter()
        self.setup_oauth()
        # Initialize credential manager after OAuth setup to avoid blocking
        try:
            self.credential_manager = CredentialManager(self.db.db_path)
        except Exception as e:
            # If credential manager fails to initialize, create a minimal version
            self.credential_manager = None
            if hasattr(st, 'session_state'):
                st.session_state.credential_manager_error = str(e)
            # Log the error but don't stop the app
            print(f"Warning: Credential manager initialization failed: {str(e)}")

    def setup_oauth(self):
        """Setup OAuth2 configuration - disabled for individual users."""
        # OAuth disabled - using email/password authentication only
        self.oauth_flow = None

    def register_user(self, email: str, password: str, first_name: str = "",
                     last_name: str = "", partner_id: Optional[str] = None) -> Dict:
        """Register a new user."""
        # Validate password strength
        password_validation = self._validate_password_strength(password)
        if not password_validation['valid']:
            return {"success": False, "error": password_validation['error']}

        # Sanitize inputs
        from data_validation import InputSanitizer
        email = InputSanitizer.sanitize_string(email).lower()
        first_name = InputSanitizer.sanitize_string(first_name)
        last_name = InputSanitizer.sanitize_string(last_name)

        return self.db.create_user(email, password, first_name, last_name, partner_id)

    def _validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password meets security requirements."""
        if len(password) < 12:
            return {"valid": False, "error": "Password must be at least 12 characters"}

        if not re.search(r'[A-Z]', password):
            return {"valid": False, "error": "Password must contain at least one uppercase letter"}

        if not re.search(r'[a-z]', password):
            return {"valid": False, "error": "Password must contain at least one lowercase letter"}

        if not re.search(r'\d', password):
            return {"valid": False, "error": "Password must contain at least one number"}

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return {"valid": False, "error": "Password must contain at least one special character"}

        # Check for common weak passwords
        weak_patterns = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if any(weak in password.lower() for weak in weak_patterns):
            return {"valid": False, "error": "Password contains common weak patterns"}

        return {"valid": True, "error": None}

    def login_user(self, email: str, password: str) -> Dict:
        """Login user with email and password."""
        # Check rate limiting
        if self.rate_limiter.is_rate_limited(email):
            return {"success": False, "error": "Too many failed attempts. Please try again later."}

        user = self.db.authenticate_user(email, password)

        if user:
            self.rate_limiter.record_attempt(email, True)
            session_id = self.db.create_session(user["id"], user["partner_id"])
            return {"success": True, "session_id": session_id, "user": user}
        else:
            self.rate_limiter.record_attempt(email, False)
            return {"success": False, "error": "Invalid credentials"}

    def oauth_login_url(self, redirect_uri: str, partner_id: Optional[str] = None) -> Optional[str]:
        """Get OAuth login URL."""
        if not self.oauth_flow:
            return None

        self.oauth_flow.redirect_uri = redirect_uri
        authorization_url, state = self.oauth_flow.authorization_url()

        # Store state and partner_id in session
        st.session_state.oauth_state = state
        if partner_id:
            st.session_state.oauth_partner_id = partner_id

        return authorization_url

    def handle_oauth_callback(self, authorization_response: str, state: str) -> Dict:
        """Handle OAuth callback."""
        if not self.oauth_flow or state != st.session_state.get('oauth_state'):
            return {"success": False, "error": "Invalid OAuth state"}

        try:
            self.oauth_flow.fetch_token(authorization_response=authorization_response)
            credentials = self.oauth_flow.credentials

            # Get user info from Google
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()

            email = user_info.get('email')
            oauth_id = user_info.get('id')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')

            # Check if user exists
            user = self.db.get_user_by_oauth('google', oauth_id)

            if not user:
                # Create new user
                partner_id = st.session_state.get('oauth_partner_id')
                result = self.db.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    partner_id=partner_id,
                    oauth_provider='google',
                    oauth_id=oauth_id
                )

                if not result["success"]:
                    return result

                user = self.db.get_user_by_oauth('google', oauth_id)

            # Store OAuth tokens securely
            self.credential_manager.store_oauth_token(
                user_id=user["id"],
                provider='google',
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expires_in=credentials.expiry.timestamp() - datetime.now().timestamp() if credentials.expiry else None,
                partner_id=user.get("partner_id")
            )

            # Create session
            session_id = self.db.create_session(user["id"], user["partner_id"])

            return {"success": True, "session_id": session_id, "user": user}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user."""
        session_id = st.session_state.get('session_id')
        if session_id:
            return self.db.validate_session(session_id)
        return None

    def logout_user(self) -> None:
        """Logout current user."""
        # Clear session state
        for key in list(st.session_state.keys()):
            if key.startswith(('session_', 'oauth_', 'user_')):
                del st.session_state[key]


def require_auth(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        auth_manager = AuthManager()
        user = auth_manager.get_current_user()

        if not user:
            st.error("🔒 Authentication required")
            st.stop()

        # Add user to kwargs
        kwargs['current_user'] = user
        return func(*args, **kwargs)

    return wrapper


def check_partner_access(required_role: str = 'user'):
    """Decorator to check partner access level."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                st.error("🔒 Authentication required")
                st.stop()

            user_role = current_user.get('partner_role', 'user')
            role_hierarchy = {'user': 0, 'admin': 1, 'super_admin': 2}

            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                st.error("🚫 Insufficient permissions")
                st.stop()

            return func(*args, **kwargs)
        return wrapper
    return decorator


def render_auth_interface():
    """Render the main authentication interface."""
    auth_manager = AuthManager()

    # Check if user is already authenticated
    current_user = auth_manager.get_current_user()

    if current_user:
        # User is authenticated, return user info
        return current_user

    else:
        # User not authenticated, show login/register
        st.title("🔐 TradeSense Authentication")
        st.write("Please log in to access the trading analytics dashboard.")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            render_login_form(auth_manager)

        with tab2:
            render_register_form(auth_manager)

        st.stop()


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

        # Partner invitation code
        partner_code = st.text_input("Partner Code (Optional)", 
                                   help="Enter if you have a partner invitation code")

        if st.form_submit_button("🚀 Create Account", type="primary"):
            if not all([first_name, last_name, email, password, confirm_password]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                result = auth_manager.register_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    partner_id=partner_code if partner_code else None
                )

                if result['success']:
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error(result['error'])