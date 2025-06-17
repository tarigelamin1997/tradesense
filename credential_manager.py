
import os
import json
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import sqlite3
import streamlit as st

class CredentialManager:
    """Secure credential storage with encryption and rotation."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.init_credentials_table()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create master encryption key with enhanced persistence."""
        # Check if key exists in environment (Replit Secrets)
        key_b64 = os.environ.get('TRADESENSE_MASTER_KEY')
        
        if key_b64:
            try:
                # Validate the key format and decode
                decoded_key = base64.urlsafe_b64decode(key_b64)
                # Test if key works with Fernet
                test_cipher = Fernet(decoded_key)
                # Key is valid
                return decoded_key
            except Exception as e:
                st.error(f"⚠️ Invalid encryption key in environment: {str(e)}")
                st.warning("Generating new encryption key...")
        
        # Check for backup key in database
        backup_key = self._get_backup_key_from_db()
        if backup_key:
            try:
                decoded_key = base64.urlsafe_b64decode(backup_key)
                test_cipher = Fernet(decoded_key)
                # Update environment with backup key
                os.environ['TRADESENSE_MASTER_KEY'] = backup_key
                st.success("🔑 Restored encryption key from backup")
                return decoded_key
            except:
                st.warning("Backup key is also invalid, generating new key...")
        
        # Generate new key if not found or invalid
        key = Fernet.generate_key()
        key_b64 = base64.urlsafe_b64encode(key).decode()
        
        # Store in environment for this session
        os.environ['TRADESENSE_MASTER_KEY'] = key_b64
        
        # Store backup in database
        self._store_backup_key_in_db(key_b64)
        
        # Store key info in session state for later display
        if hasattr(st, 'session_state'):
            st.session_state.new_encryption_key = key_b64
            st.session_state.show_key_setup = True
        
        return key
    
    def init_credentials_table(self):
        """Initialize encrypted credentials table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encrypted_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credential_id TEXT UNIQUE NOT NULL,
                credential_type TEXT NOT NULL,
                encrypted_data TEXT NOT NULL,
                salt TEXT NOT NULL,
                user_id INTEGER,
                partner_id TEXT,
                expires_at TIMESTAMP,
                rotation_interval_days INTEGER DEFAULT 90,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_rotated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Create backup key storage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encryption_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT UNIQUE NOT NULL,
                encrypted_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Index for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_credential_id 
            ON encrypted_credentials (credential_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_credential_type_user 
            ON encrypted_credentials (credential_type, user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_key_id 
            ON encryption_keys (key_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def _store_backup_key_in_db(self, key_b64: str) -> None:
        """Store backup encryption key in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple obfuscation for backup storage (not encryption, just basic protection)
            obfuscated_key = base64.b64encode(key_b64.encode()).decode()
            
            cursor.execute('''
                INSERT OR REPLACE INTO encryption_keys (key_id, encrypted_key, is_active)
                VALUES (?, ?, ?)
            ''', ('master_backup', obfuscated_key, True))
            
            conn.commit()
            conn.close()
        except Exception as e:
            # Silently fail - backup storage is optional
            pass
    
    def _get_backup_key_from_db(self) -> Optional[str]:
        """Retrieve backup encryption key from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT encrypted_key FROM encryption_keys 
                WHERE key_id = ? AND is_active = TRUE
            ''', ('master_backup',))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Deobfuscate the stored key
                obfuscated_key = result[0]
                return base64.b64decode(obfuscated_key).decode()
            
            return None
        except Exception:
            return None
    
    def store_credential(self, 
                        credential_id: str,
                        credential_type: str,
                        credential_data: Dict[str, Any],
                        user_id: Optional[int] = None,
                        partner_id: Optional[str] = None,
                        expires_at: Optional[datetime] = None,
                        rotation_days: int = 90,
                        metadata: Dict[str, Any] = None) -> bool:
        """Store encrypted credential."""
        try:
            # Generate salt for this credential
            salt = secrets.token_bytes(32)
            
            # Serialize credential data
            data_json = json.dumps(credential_data)
            
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(data_json.encode())
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO encrypted_credentials 
                (credential_id, credential_type, encrypted_data, salt, user_id, 
                 partner_id, expires_at, rotation_interval_days, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                credential_id,
                credential_type,
                base64.b64encode(encrypted_data).decode(),
                base64.b64encode(salt).decode(),
                user_id,
                partner_id,
                expires_at,
                rotation_days,
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to store credential: {str(e)}")
            return False
    
    def retrieve_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt credential."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_data, expires_at, is_active 
            FROM encrypted_credentials 
            WHERE credential_id = ? AND is_active = TRUE
        ''', (credential_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        encrypted_data, expires_at, is_active = result
        
        # Check if credential has expired
        if expires_at:
            expiry_date = datetime.fromisoformat(expires_at)
            if datetime.now() > expiry_date:
                self.deactivate_credential(credential_id)
                return None
        
        try:
            # Decrypt the data
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            
            # Parse JSON
            credential_data = json.loads(decrypted_data.decode())
            
            return credential_data
            
        except Exception as e:
            st.error(f"Failed to decrypt credential: {str(e)}")
            return None
    
    def store_oauth_token(self, 
                         user_id: int,
                         provider: str,
                         access_token: str,
                         refresh_token: Optional[str] = None,
                         expires_in: Optional[int] = None,
                         partner_id: Optional[str] = None) -> str:
        """Store OAuth tokens securely."""
        credential_id = f"oauth_{provider}_{user_id}"
        
        # Calculate expiry
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'provider': provider,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        self.store_credential(
            credential_id=credential_id,
            credential_type='oauth_token',
            credential_data=token_data,
            user_id=user_id,
            partner_id=partner_id,
            expires_at=expires_at,
            rotation_days=30,  # OAuth tokens rotate more frequently
            metadata={'provider': provider}
        )
        
        return credential_id
    
    def store_api_key(self,
                     user_id: int,
                     service_name: str,
                     api_key: str,
                     partner_id: Optional[str] = None,
                     additional_data: Dict[str, Any] = None) -> str:
        """Store API key securely."""
        credential_id = f"api_key_{service_name}_{user_id}"
        
        key_data = {
            'api_key': api_key,
            'service_name': service_name,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        if additional_data:
            key_data.update(additional_data)
        
        self.store_credential(
            credential_id=credential_id,
            credential_type='api_key',
            credential_data=key_data,
            user_id=user_id,
            partner_id=partner_id,
            rotation_days=90,
            metadata={'service': service_name}
        )
        
        return credential_id
    
    def store_broker_credentials(self,
                               user_id: int,
                               broker_name: str,
                               username: str,
                               password: str,
                               api_key: Optional[str] = None,
                               additional_fields: Dict[str, Any] = None) -> str:
        """Store broker credentials securely."""
        credential_id = f"broker_{broker_name}_{user_id}"
        
        broker_data = {
            'broker_name': broker_name,
            'username': username,
            'password': password,
            'api_key': api_key,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        if additional_fields:
            broker_data.update(additional_fields)
        
        self.store_credential(
            credential_id=credential_id,
            credential_type='broker_credentials',
            credential_data=broker_data,
            user_id=user_id,
            rotation_days=180,  # Broker credentials rotate less frequently
            metadata={'broker': broker_name}
        )
        
        return credential_id
    
    def get_oauth_token(self, user_id: int, provider: str) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth token."""
        credential_id = f"oauth_{provider}_{user_id}"
        return self.retrieve_credential(credential_id)
    
    def get_api_key(self, user_id: int, service_name: str) -> Optional[str]:
        """Retrieve API key."""
        credential_id = f"api_key_{service_name}_{user_id}"
        credential_data = self.retrieve_credential(credential_id)
        
        if credential_data:
            return credential_data.get('api_key')
        return None
    
    def get_broker_credentials(self, user_id: int, broker_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve broker credentials."""
        credential_id = f"broker_{broker_name}_{user_id}"
        return self.retrieve_credential(credential_id)
    
    def rotate_credential(self, credential_id: str, new_credential_data: Dict[str, Any]) -> bool:
        """Rotate/update existing credential."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current credential info
        cursor.execute('''
            SELECT credential_type, user_id, partner_id, rotation_interval_days, metadata
            FROM encrypted_credentials 
            WHERE credential_id = ?
        ''', (credential_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        credential_type, user_id, partner_id, rotation_days, metadata = result
        
        # Store new credential data
        success = self.store_credential(
            credential_id=credential_id,
            credential_type=credential_type,
            credential_data=new_credential_data,
            user_id=user_id,
            partner_id=partner_id,
            rotation_days=rotation_days,
            metadata=json.loads(metadata) if metadata else {}
        )
        
        if success:
            # Update rotation timestamp
            cursor.execute('''
                UPDATE encrypted_credentials 
                SET last_rotated = CURRENT_TIMESTAMP 
                WHERE credential_id = ?
            ''', (credential_id,))
            conn.commit()
        
        conn.close()
        return success
    
    def deactivate_credential(self, credential_id: str) -> bool:
        """Deactivate/revoke credential."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE encrypted_credentials 
            SET is_active = FALSE 
            WHERE credential_id = ?
        ''', (credential_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def list_credentials_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """List all credentials for a user (metadata only)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT credential_id, credential_type, expires_at, 
                   last_rotated, is_active, metadata
            FROM encrypted_credentials 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        credentials = []
        for result in results:
            cred_id, cred_type, expires_at, last_rotated, is_active, metadata = result
            
            credentials.append({
                'credential_id': cred_id,
                'credential_type': cred_type,
                'expires_at': expires_at,
                'last_rotated': last_rotated,
                'is_active': bool(is_active),
                'metadata': json.loads(metadata) if metadata else {}
            })
        
        return credentials
    
    def check_expiring_credentials(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Check for credentials expiring soon."""
        future_date = datetime.now() + timedelta(days=days_ahead)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT credential_id, credential_type, expires_at, user_id, metadata
            FROM encrypted_credentials 
            WHERE expires_at IS NOT NULL 
            AND expires_at <= ? 
            AND is_active = TRUE
        ''', (future_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        expiring = []
        for result in results:
            cred_id, cred_type, expires_at, user_id, metadata = result
            
            expiring.append({
                'credential_id': cred_id,
                'credential_type': cred_type,
                'expires_at': expires_at,
                'user_id': user_id,
                'metadata': json.loads(metadata) if metadata else {}
            })
        
        return expiring
    
    def cleanup_expired_credentials(self) -> int:
        """Remove expired credentials."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM encrypted_credentials 
            WHERE expires_at IS NOT NULL 
            AND expires_at < CURRENT_TIMESTAMP
        ''')
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def validate_encryption_key(self) -> Dict[str, any]:
        """Validate the current encryption key and provide status."""
        try:
            # Test encryption/decryption with current key
            test_data = {"test": "validation_data"}
            test_json = json.dumps(test_data)
            
            # Try to encrypt
            encrypted_data = self.cipher_suite.encrypt(test_json.encode())
            
            # Try to decrypt
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            parsed_data = json.loads(decrypted_data.decode())
            
            # Check if data matches
            is_valid = parsed_data == test_data
            
            return {
                "is_valid": is_valid,
                "has_env_key": bool(os.environ.get('TRADESENSE_MASTER_KEY')),
                "has_backup": bool(self._get_backup_key_from_db()),
                "error": None
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "has_env_key": bool(os.environ.get('TRADESENSE_MASTER_KEY')),
                "has_backup": bool(self._get_backup_key_from_db()),
                "error": str(e)
            }
    
    def get_key_status_display(self) -> None:
        """Display current encryption key status in Streamlit."""
        # Check if we need to show key setup
        if hasattr(st, 'session_state') and getattr(st.session_state, 'show_key_setup', False):
            self._display_key_setup_ui()
            return
        
        status = self.validate_encryption_key()
        
        if status["is_valid"]:
            st.success("🔐 Encryption key is valid and working")
            
            col1, col2 = st.columns(2)
            with col1:
                if status["has_env_key"]:
                    st.success("✅ Environment key found")
                else:
                    st.warning("⚠️ No environment key")
            
            with col2:
                if status["has_backup"]:
                    st.info("💾 Backup key available")
                else:
                    st.info("💾 No backup key")
        else:
            st.error("❌ Encryption key validation failed")
            if status["error"]:
                st.error(f"Error: {status['error']}")
            
            if not status["has_env_key"]:
                st.warning("🔑 No encryption key found in environment")
                st.info("Add TRADESENSE_MASTER_KEY to Replit Secrets")
            
            if status["has_backup"]:
                st.info("💾 Backup key available - attempting recovery...")
            else:
                st.warning("💾 No backup key available")
    
    def _display_key_setup_ui(self) -> None:
        """Display the key setup UI when a new key is generated."""
        key_b64 = getattr(st.session_state, 'new_encryption_key', None)
        
        if key_b64:
            st.warning("🔐 **New encryption key generated**")
            st.code(key_b64, language="text")
            st.error("🚨 **IMPORTANT**: Add this key to Replit Secrets as `TRADESENSE_MASTER_KEY`")
            st.info("1. Click the 🔒 Secrets tool in the sidebar")
            st.info("2. Add secret: Key=`TRADESENSE_MASTER_KEY`, Value=`(copy key above)`")
            st.info("3. This key will encrypt all your stored credentials")
            
            if st.button("✅ I've added the key to Secrets"):
                st.session_state.show_key_setup = False
                if hasattr(st.session_state, 'new_encryption_key'):
                    del st.session_state.new_encryption_key
                st.rerun()


# Integration with existing auth system
def integrate_credential_manager():
    """Initialize credential manager for the application."""
    if 'credential_manager' not in st.session_state:
        st.session_state.credential_manager = CredentialManager()
    
    return st.session_state.credential_manager


def render_credential_management_ui(current_user: Dict):
    """Render credential management interface."""
    st.subheader("🔐 Credential Management")
    
    credential_manager = integrate_credential_manager()
    
    # Check for expiring credentials
    expiring = credential_manager.check_expiring_credentials()
    if expiring:
        st.warning(f"⚠️ {len(expiring)} credentials expiring soon!")
        with st.expander("View Expiring Credentials"):
            for cred in expiring:
                st.write(f"• {cred['credential_type']}: {cred['credential_id']}")
    
    tabs = st.tabs(["OAuth Tokens", "API Keys", "Broker Credentials", "Manage"])
    
    with tabs[0]:
        render_oauth_management(credential_manager, current_user)
    
    with tabs[1]:
        render_api_key_management(credential_manager, current_user)
    
    with tabs[2]:
        render_broker_credential_management(credential_manager, current_user)
    
    with tabs[3]:
        render_credential_list(credential_manager, current_user)


def render_oauth_management(credential_manager: CredentialManager, current_user: Dict):
    """Render OAuth token management."""
    st.subheader("🔗 OAuth Tokens")
    
    # Add new OAuth token
    with st.expander("➕ Add OAuth Token"):
        with st.form("oauth_form"):
            provider = st.selectbox("Provider", ["google", "discord", "github", "custom"])
            access_token = st.text_input("Access Token", type="password")
            refresh_token = st.text_input("Refresh Token (Optional)", type="password")
            expires_in = st.number_input("Expires In (seconds)", min_value=0, value=3600)
            
            if st.form_submit_button("Store Token"):
                if access_token:
                    credential_id = credential_manager.store_oauth_token(
                        user_id=current_user['id'],
                        provider=provider,
                        access_token=access_token,
                        refresh_token=refresh_token if refresh_token else None,
                        expires_in=expires_in if expires_in > 0 else None
                    )
                    st.success(f"OAuth token stored: {credential_id}")


def render_api_key_management(credential_manager: CredentialManager, current_user: Dict):
    """Render API key management."""
    st.subheader("🔑 API Keys")
    
    # Add new API key
    with st.expander("➕ Add API Key"):
        with st.form("api_key_form"):
            service_name = st.text_input("Service Name")
            api_key = st.text_input("API Key", type="password")
            endpoint = st.text_input("API Endpoint (Optional)")
            
            if st.form_submit_button("Store API Key"):
                if service_name and api_key:
                    additional_data = {}
                    if endpoint:
                        additional_data['endpoint'] = endpoint
                    
                    credential_id = credential_manager.store_api_key(
                        user_id=current_user['id'],
                        service_name=service_name,
                        api_key=api_key,
                        additional_data=additional_data
                    )
                    st.success(f"API key stored: {credential_id}")


def render_broker_credential_management(credential_manager: CredentialManager, current_user: Dict):
    """Render broker credential management."""
    st.subheader("🏦 Broker Credentials")
    
    # Add new broker credentials
    with st.expander("➕ Add Broker Credentials"):
        with st.form("broker_form"):
            broker_name = st.selectbox("Broker", ["Interactive Brokers", "TD Ameritrade", "E*TRADE", "Charles Schwab", "Other"])
            if broker_name == "Other":
                broker_name = st.text_input("Custom Broker Name")
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            api_key = st.text_input("API Key (Optional)", type="password")
            
            if st.form_submit_button("Store Credentials"):
                if broker_name and username and password:
                    credential_id = credential_manager.store_broker_credentials(
                        user_id=current_user['id'],
                        broker_name=broker_name,
                        username=username,
                        password=password,
                        api_key=api_key if api_key else None
                    )
                    st.success(f"Broker credentials stored: {credential_id}")


def render_credential_list(credential_manager: CredentialManager, current_user: Dict):
    """Render list of user's credentials."""
    st.subheader("📋 Your Credentials")
    
    credentials = credential_manager.list_credentials_for_user(current_user['id'])
    
    if credentials:
        for cred in credentials:
            with st.expander(f"{cred['credential_type']}: {cred['credential_id']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Type:** {cred['credential_type']}")
                    st.write(f"**Active:** {'✅' if cred['is_active'] else '❌'}")
                
                with col2:
                    if cred['expires_at']:
                        st.write(f"**Expires:** {cred['expires_at']}")
                    st.write(f"**Last Rotated:** {cred['last_rotated']}")
                
                with col3:
                    if st.button(f"🔄 Rotate", key=f"rotate_{cred['credential_id']}"):
                        st.info("Credential rotation initiated")
                    
                    if st.button(f"🗑️ Deactivate", key=f"deactivate_{cred['credential_id']}"):
                        if credential_manager.deactivate_credential(cred['credential_id']):
                            st.success("Credential deactivated")
                            st.rerun()
    else:
        st.info("No credentials stored yet")
    
    # Key Management Section
    st.subheader("🔑 Encryption Key Management")
    credential_manager.get_key_status_display()
    
    with st.expander("🔧 Advanced Key Management"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Validate Key"):
                status = credential_manager.validate_encryption_key()
                if status["is_valid"]:
                    st.success("✅ Key validation successful")
                else:
                    st.error(f"❌ Key validation failed: {status.get('error', 'Unknown error')}")
        
        with col2:
            if st.button("🔄 Regenerate Key", help="Generate new encryption key (will require re-entering all credentials)"):
                # This is a dangerous operation - require confirmation
                st.error("⚠️ **WARNING**: This will invalidate all stored credentials!")
                st.error("You will need to re-enter all OAuth tokens, API keys, and broker credentials.")
                
                confirm = st.checkbox("I understand and want to proceed", key="confirm_key_regen")
                if confirm and st.button("🔥 CONFIRM REGENERATE", type="primary"):
                    # Generate new key
                    new_key = Fernet.generate_key()
                    new_key_b64 = base64.urlsafe_b64encode(new_key).decode()
                    
                    # Store backup
                    credential_manager._store_backup_key_in_db(new_key_b64)
                    
                    # Update environment
                    os.environ['TRADESENSE_MASTER_KEY'] = new_key_b64
                    
                    st.success("🔑 New encryption key generated!")
                    st.code(new_key_b64, language="text")
                    st.error("🚨 **UPDATE YOUR SECRETS**: Replace TRADESENSE_MASTER_KEY in Replit Secrets with the key above")
                    st.warning("🔄 All existing credentials have been invalidated")
    
    # Cleanup expired credentials
    if st.button("🧹 Cleanup Expired Credentials"):
        deleted_count = credential_manager.cleanup_expired_credentials()
        if deleted_count > 0:
            st.success(f"Cleaned up {deleted_count} expired credentials")
        else:
            st.info("No expired credentials to clean up")
