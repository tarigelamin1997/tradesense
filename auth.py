
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import sqlite3
import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import jwt
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
            
            return {"success": True, "user_id": user_id, "api_key": api_key}
        
        except sqlite3.IntegrityError as e:
            return {"success": False, "error": "Email already exists"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, password_hash, first_name, last_name, 
                   partner_id, partner_role, is_active, subscription_tier
            FROM users WHERE email = ? AND is_active = TRUE
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        
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
        return None
    
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
        self.setup_oauth()
    
    def setup_oauth(self):
        """Setup OAuth2 configuration."""
        try:
            oauth_config = json.loads(os.environ.get('GOOGLE_OAUTH_SECRETS', '{}'))
            if oauth_config:
                self.oauth_flow = google_auth_oauthlib.flow.Flow.from_client_config(
                    oauth_config,
                    scopes=[
                        "https://www.googleapis.com/auth/userinfo.email",
                        "openid",
                        "https://www.googleapis.com/auth/userinfo.profile"
                    ]
                )
            else:
                self.oauth_flow = None
        except:
            self.oauth_flow = None
    
    def register_user(self, email: str, password: str, first_name: str = "",
                     last_name: str = "", partner_id: Optional[str] = None) -> Dict:
        """Register a new user."""
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}
        
        return self.db.create_user(email, password, first_name, last_name, partner_id)
    
    def login_user(self, email: str, password: str) -> Dict:
        """Login user with email and password."""
        user = self.db.authenticate_user(email, password)
        if user:
            session_id = self.db.create_session(user["id"], user["partner_id"])
            return {"success": True, "session_id": session_id, "user": user}
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
