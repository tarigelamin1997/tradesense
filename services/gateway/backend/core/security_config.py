"""
Security configuration and utilities for production deployment

Implements encryption, hashing, token management, and security best practices
"""

import os
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp
import qrcode
from io import BytesIO
from pydantic import BaseModel, Field
import re

from core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityConfig(BaseModel):
    """Security configuration settings"""
    
    # JWT Configuration
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    
    # Encryption
    master_encryption_key: str = Field(..., min_length=32)
    
    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_history_count: int = 5
    
    # MFA
    mfa_enabled: bool = True
    mfa_issuer: str = "TradeSense"
    
    # Session
    session_timeout_minutes: int = 60
    concurrent_sessions_limit: int = 3
    
    # Security Headers
    enable_hsts: bool = True
    enable_csp: bool = True
    
    # API Security
    api_key_length: int = 32
    api_key_prefix: str = "ts_"


class PasswordValidator:
    """Validate passwords against security policy"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            default="argon2",
            argon2__rounds=4,
            argon2__memory_cost=65536,
            argon2__parallelism=2
        )
    
    def validate_password(self, password: str, username: str = None) -> Tuple[bool, List[str]]:
        """Validate password against policy"""
        errors = []
        
        # Length check
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters")
        
        # Complexity checks
        if self.config.password_require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.password_require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.config.password_require_numbers and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        
        if self.config.password_require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        # Check common passwords
        if self._is_common_password(password):
            errors.append("Password is too common")
        
        # Check if password contains username
        if username and username.lower() in password.lower():
            errors.append("Password cannot contain username")
        
        return len(errors) == 0, errors
    
    def _is_common_password(self, password: str) -> bool:
        """Check against common passwords"""
        common_passwords = {
            "password", "12345678", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        }
        return password.lower() in common_passwords
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """Manage JWT tokens and API keys"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.secret_key = config.jwt_secret_key
        self.algorithm = config.jwt_algorithm
    
    def create_access_token(
        self,
        user_id: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        additional_claims: Dict[str, Any] = None
    ) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.config.jwt_expire_minutes)
        
        claims = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "roles": roles or [],
            "permissions": permissions or []
        }
        
        if additional_claims:
            claims.update(additional_claims)
        
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.config.jwt_refresh_expire_days)
        
        claims = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str, expected_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != expected_type:
                raise JWTError("Invalid token type")
            
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise
    
    def generate_api_key(self) -> Tuple[str, str]:
        """Generate API key and its hash"""
        # Generate random key
        key = secrets.token_urlsafe(self.config.api_key_length)
        api_key = f"{self.config.api_key_prefix}{key}"
        
        # Hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return api_key, key_hash
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return secrets.compare_digest(key_hash, stored_hash)


class DataEncryption:
    """Handle sensitive data encryption"""
    
    def __init__(self, master_key: str):
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tradesense-salt',  # In production, use unique salt per deployment
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary data"""
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt dictionary data"""
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class MFAManager:
    """Multi-factor authentication management"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.issuer = config.mfa_issuer
    
    def generate_secret(self) -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, username: str, secret: str) -> bytes:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=self.issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        
        return buf.getvalue()
    
    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4) for _ in range(count)]


class SecurityAudit:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = get_logger("security_audit")
    
    def log_login_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        mfa_used: bool = False,
        failure_reason: Optional[str] = None
    ):
        """Log login attempt"""
        self.logger.info(
            "Login attempt",
            extra={
                "event_type": "login_attempt",
                "username": username,
                "ip_address": ip_address,
                "success": success,
                "mfa_used": mfa_used,
                "failure_reason": failure_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_permission_check(
        self,
        user_id: str,
        resource: str,
        action: str,
        allowed: bool
    ):
        """Log permission check"""
        self.logger.info(
            "Permission check",
            extra={
                "event_type": "permission_check",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "allowed": allowed,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_data_access(
        self,
        user_id: str,
        data_type: str,
        record_ids: List[str],
        action: str
    ):
        """Log sensitive data access"""
        self.logger.info(
            "Data access",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "data_type": data_type,
                "record_count": len(record_ids),
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Singleton instances
_security_config: Optional[SecurityConfig] = None
_password_validator: Optional[PasswordValidator] = None
_token_manager: Optional[TokenManager] = None
_data_encryption: Optional[DataEncryption] = None
_mfa_manager: Optional[MFAManager] = None
_security_audit: Optional[SecurityAudit] = None


def initialize_security(config: Dict[str, Any]):
    """Initialize security components"""
    global _security_config, _password_validator, _token_manager
    global _data_encryption, _mfa_manager, _security_audit
    
    _security_config = SecurityConfig(**config)
    _password_validator = PasswordValidator(_security_config)
    _token_manager = TokenManager(_security_config)
    _data_encryption = DataEncryption(_security_config.master_encryption_key)
    _mfa_manager = MFAManager(_security_config)
    _security_audit = SecurityAudit()
    
    logger.info("Security components initialized")


def get_password_validator() -> PasswordValidator:
    """Get password validator instance"""
    if not _password_validator:
        raise RuntimeError("Security not initialized")
    return _password_validator


def get_token_manager() -> TokenManager:
    """Get token manager instance"""
    if not _token_manager:
        raise RuntimeError("Security not initialized")
    return _token_manager


def get_data_encryption() -> DataEncryption:
    """Get data encryption instance"""
    if not _data_encryption:
        raise RuntimeError("Security not initialized")
    return _data_encryption


def get_mfa_manager() -> MFAManager:
    """Get MFA manager instance"""
    if not _mfa_manager:
        raise RuntimeError("Security not initialized")
    return _mfa_manager


def get_security_audit() -> SecurityAudit:
    """Get security audit instance"""
    if not _security_audit:
        raise RuntimeError("Security not initialized")
    return _security_audit