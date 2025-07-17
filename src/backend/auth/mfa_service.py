"""
Multi-Factor Authentication (MFA) service for TradeSense.
Supports TOTP, SMS, and backup codes.
"""

import secrets
import qrcode
import io
import base64
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pyotp
from twilio.rest import Client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from core.config import settings
from models.user import User
from core.db.session import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from services.email_service import email_service
from src.backend.monitoring.metrics import security_metrics


class MFAMethod:
    """Supported MFA methods."""
    TOTP = "totp"  # Time-based One-Time Password (Google Authenticator)
    SMS = "sms"    # SMS verification
    EMAIL = "email"  # Email verification
    BACKUP_CODES = "backup_codes"  # Backup recovery codes


class MFAService:
    """Manages multi-factor authentication for users."""
    
    def __init__(self):
        # Twilio configuration for SMS
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            self.twilio_from_number = settings.TWILIO_PHONE_NUMBER
        
        # TOTP configuration
        self.totp_issuer = "TradeSense"
        self.totp_period = 30  # seconds
        self.totp_digits = 6
        
        # Backup codes configuration
        self.backup_codes_count = 10
        self.backup_code_length = 8
        
        # Rate limiting
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    async def setup_totp(self, user: User, db: AsyncSession) -> Dict[str, any]:
        """Set up TOTP authentication for a user."""
        # Generate secret key
        secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(
            secret,
            issuer=self.totp_issuer,
            interval=self.totp_period,
            digits=self.totp_digits
        )
        
        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=self.totp_issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert QR code to base64 image
        img_buffer = io.BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        qr_code_b64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Store encrypted secret temporarily (not active yet)
        await db.execute(
            text("""
                INSERT INTO mfa_devices (
                    user_id, device_type, device_name,
                    secret_encrypted, status, metadata
                ) VALUES (
                    :user_id, :device_type, :device_name,
                    :secret, 'pending', :metadata
                )
                ON CONFLICT (user_id, device_type) 
                WHERE device_type = 'totp' AND status = 'pending'
                DO UPDATE SET 
                    secret_encrypted = :secret,
                    updated_at = NOW()
                RETURNING id
            """),
            {
                "user_id": user.id,
                "device_type": MFAMethod.TOTP,
                "device_name": "Authenticator App",
                "secret": self._encrypt_secret(secret),
                "metadata": {"issuer": self.totp_issuer}
            }
        )
        await db.commit()
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_b64}",
            "manual_entry_key": secret,
            "manual_entry_setup": {
                "issuer": self.totp_issuer,
                "account": user.email,
                "period": self.totp_period,
                "digits": self.totp_digits
            }
        }
    
    async def verify_totp_setup(self, user: User, code: str, db: AsyncSession) -> bool:
        """Verify TOTP setup with initial code."""
        # Get pending TOTP device
        result = await db.execute(
            text("""
                SELECT id, secret_encrypted
                FROM mfa_devices
                WHERE user_id = :user_id
                AND device_type = :device_type
                AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {
                "user_id": user.id,
                "device_type": MFAMethod.TOTP
            }
        )
        
        device = result.first()
        if not device:
            return False
        
        # Verify code
        secret = self._decrypt_secret(device.secret_encrypted)
        totp = pyotp.TOTP(secret)
        
        if totp.verify(code, valid_window=1):
            # Activate device
            await db.execute(
                text("""
                    UPDATE mfa_devices
                    SET status = 'active',
                        verified_at = NOW(),
                        last_used_at = NOW()
                    WHERE id = :device_id
                """),
                {"device_id": device.id}
            )
            
            # Enable MFA for user
            await db.execute(
                text("""
                    UPDATE users
                    SET mfa_enabled = TRUE,
                        mfa_methods = array_append(
                            COALESCE(mfa_methods, ARRAY[]::varchar[]), 
                            :method
                        )
                    WHERE id = :user_id
                """),
                {
                    "user_id": user.id,
                    "method": MFAMethod.TOTP
                }
            )
            
            # Generate backup codes
            backup_codes = await self.generate_backup_codes(user, db)
            
            await db.commit()
            
            # Track metric
            security_metrics.mfa_enabled.labels(method=MFAMethod.TOTP).inc()
            
            return True
        
        return False
    
    async def setup_sms(self, user: User, phone_number: str, db: AsyncSession) -> bool:
        """Set up SMS authentication for a user."""
        if not self.twilio_client:
            raise ValueError("SMS service not configured")
        
        # Validate phone number
        if not phone_number.startswith('+'):
            phone_number = f"+1{phone_number}"  # Default to US
        
        # Store phone number (pending verification)
        await db.execute(
            text("""
                INSERT INTO mfa_devices (
                    user_id, device_type, device_name,
                    phone_number, status
                ) VALUES (
                    :user_id, :device_type, :device_name,
                    :phone_number, 'pending'
                )
                ON CONFLICT (user_id, device_type)
                WHERE device_type = 'sms' AND status = 'pending'
                DO UPDATE SET
                    phone_number = :phone_number,
                    updated_at = NOW()
            """),
            {
                "user_id": user.id,
                "device_type": MFAMethod.SMS,
                "device_name": f"SMS to {phone_number[-4:]}",
                "phone_number": phone_number
            }
        )
        await db.commit()
        
        # Send verification code
        code = await self._send_sms_code(user, phone_number, db)
        
        return code is not None
    
    async def verify_sms_setup(self, user: User, code: str, db: AsyncSession) -> bool:
        """Verify SMS setup with code."""
        # Verify code
        is_valid = await self._verify_code(user, MFAMethod.SMS, code, db)
        
        if is_valid:
            # Activate SMS device
            await db.execute(
                text("""
                    UPDATE mfa_devices
                    SET status = 'active',
                        verified_at = NOW()
                    WHERE user_id = :user_id
                    AND device_type = :device_type
                    AND status = 'pending'
                """),
                {
                    "user_id": user.id,
                    "device_type": MFAMethod.SMS
                }
            )
            
            # Enable MFA for user
            await db.execute(
                text("""
                    UPDATE users
                    SET mfa_enabled = TRUE,
                        mfa_methods = array_append(
                            COALESCE(mfa_methods, ARRAY[]::varchar[]), 
                            :method
                        )
                    WHERE id = :user_id
                """),
                {
                    "user_id": user.id,
                    "method": MFAMethod.SMS
                }
            )
            
            await db.commit()
            
            # Track metric
            security_metrics.mfa_enabled.labels(method=MFAMethod.SMS).inc()
            
            return True
        
        return False
    
    async def generate_backup_codes(self, user: User, db: AsyncSession) -> List[str]:
        """Generate backup recovery codes for a user."""
        codes = []
        
        # Generate codes
        for _ in range(self.backup_codes_count):
            code = ''.join(secrets.choice('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ') 
                          for _ in range(self.backup_code_length))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        # Store hashed codes
        for code in codes:
            await db.execute(
                text("""
                    INSERT INTO mfa_backup_codes (
                        user_id, code_hash, status
                    ) VALUES (
                        :user_id, :code_hash, 'active'
                    )
                """),
                {
                    "user_id": user.id,
                    "code_hash": self._hash_code(code)
                }
            )
        
        await db.commit()
        
        return codes
    
    async def send_mfa_challenge(self, user: User, method: str, db: AsyncSession) -> Dict[str, any]:
        """Send MFA challenge to user."""
        if method == MFAMethod.TOTP:
            # No action needed, user generates code
            return {
                "method": MFAMethod.TOTP,
                "message": "Enter the 6-digit code from your authenticator app"
            }
        
        elif method == MFAMethod.SMS:
            # Get phone number
            result = await db.execute(
                text("""
                    SELECT phone_number
                    FROM mfa_devices
                    WHERE user_id = :user_id
                    AND device_type = :device_type
                    AND status = 'active'
                    LIMIT 1
                """),
                {
                    "user_id": user.id,
                    "device_type": MFAMethod.SMS
                }
            )
            
            device = result.first()
            if not device:
                raise ValueError("SMS device not found")
            
            # Send code
            await self._send_sms_code(user, device.phone_number, db)
            
            return {
                "method": MFAMethod.SMS,
                "message": f"Enter the code sent to {device.phone_number[-4:]}",
                "phone_hint": f"***{device.phone_number[-4:]}"
            }
        
        elif method == MFAMethod.EMAIL:
            # Send email code
            await self._send_email_code(user, db)
            
            return {
                "method": MFAMethod.EMAIL,
                "message": f"Enter the code sent to {user.email}"
            }
        
        elif method == MFAMethod.BACKUP_CODES:
            return {
                "method": MFAMethod.BACKUP_CODES,
                "message": "Enter one of your backup codes"
            }
        
        else:
            raise ValueError(f"Unsupported MFA method: {method}")
    
    async def verify_mfa_code(
        self, 
        user: User, 
        method: str, 
        code: str, 
        db: AsyncSession
    ) -> Tuple[bool, Optional[str]]:
        """Verify MFA code."""
        # Check rate limiting
        if await self._is_rate_limited(user, db):
            return False, "Too many attempts. Please try again later."
        
        if method == MFAMethod.TOTP:
            # Get TOTP secret
            result = await db.execute(
                text("""
                    SELECT secret_encrypted
                    FROM mfa_devices
                    WHERE user_id = :user_id
                    AND device_type = :device_type
                    AND status = 'active'
                    LIMIT 1
                """),
                {
                    "user_id": user.id,
                    "device_type": MFAMethod.TOTP
                }
            )
            
            device = result.first()
            if not device:
                return False, "TOTP not configured"
            
            # Verify TOTP code
            secret = self._decrypt_secret(device.secret_encrypted)
            totp = pyotp.TOTP(secret)
            
            if totp.verify(code, valid_window=1):
                await self._record_successful_auth(user, method, db)
                return True, None
            
        elif method in [MFAMethod.SMS, MFAMethod.EMAIL]:
            # Verify time-based code
            is_valid = await self._verify_code(user, method, code, db)
            if is_valid:
                await self._record_successful_auth(user, method, db)
                return True, None
            
        elif method == MFAMethod.BACKUP_CODES:
            # Verify backup code
            is_valid = await self._verify_backup_code(user, code, db)
            if is_valid:
                await self._record_successful_auth(user, method, db)
                return True, None
        
        # Record failed attempt
        await self._record_failed_attempt(user, method, db)
        
        return False, "Invalid code"
    
    async def disable_mfa(self, user: User, db: AsyncSession) -> bool:
        """Disable all MFA for a user."""
        # Deactivate all devices
        await db.execute(
            text("""
                UPDATE mfa_devices
                SET status = 'disabled',
                    disabled_at = NOW()
                WHERE user_id = :user_id
                AND status = 'active'
            """),
            {"user_id": user.id}
        )
        
        # Deactivate backup codes
        await db.execute(
            text("""
                UPDATE mfa_backup_codes
                SET status = 'disabled'
                WHERE user_id = :user_id
                AND status = 'active'
            """),
            {"user_id": user.id}
        )
        
        # Update user
        await db.execute(
            text("""
                UPDATE users
                SET mfa_enabled = FALSE,
                    mfa_methods = ARRAY[]::varchar[]
                WHERE id = :user_id
            """),
            {"user_id": user.id}
        )
        
        await db.commit()
        
        # Track metric
        security_metrics.mfa_disabled.inc()
        
        return True
    
    async def list_mfa_devices(self, user: User, db: AsyncSession) -> List[Dict[str, any]]:
        """List all MFA devices for a user."""
        result = await db.execute(
            text("""
                SELECT 
                    id, device_type, device_name, status,
                    created_at, verified_at, last_used_at,
                    CASE 
                        WHEN phone_number IS NOT NULL 
                        THEN CONCAT('***', RIGHT(phone_number, 4))
                        ELSE NULL
                    END as phone_hint
                FROM mfa_devices
                WHERE user_id = :user_id
                AND status IN ('active', 'pending')
                ORDER BY created_at DESC
            """),
            {"user_id": user.id}
        )
        
        devices = []
        for row in result:
            devices.append({
                "id": str(row.id),
                "type": row.device_type,
                "name": row.device_name,
                "status": row.status,
                "created_at": row.created_at,
                "verified_at": row.verified_at,
                "last_used_at": row.last_used_at,
                "phone_hint": row.phone_hint
            })
        
        # Check backup codes
        result = await db.execute(
            text("""
                SELECT COUNT(*) as unused_codes
                FROM mfa_backup_codes
                WHERE user_id = :user_id
                AND status = 'active'
            """),
            {"user_id": user.id}
        )
        
        backup_codes_count = result.scalar()
        if backup_codes_count > 0:
            devices.append({
                "id": "backup_codes",
                "type": MFAMethod.BACKUP_CODES,
                "name": f"Backup Codes ({backup_codes_count} remaining)",
                "status": "active"
            })
        
        return devices
    
    # Helper methods
    async def _send_sms_code(self, user: User, phone_number: str, db: AsyncSession) -> Optional[str]:
        """Send SMS verification code."""
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        
        # Store code
        await db.execute(
            text("""
                INSERT INTO mfa_verification_codes (
                    user_id, code_hash, method, expires_at
                ) VALUES (
                    :user_id, :code_hash, :method, :expires_at
                )
            """),
            {
                "user_id": user.id,
                "code_hash": self._hash_code(code),
                "method": MFAMethod.SMS,
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
        )
        await db.commit()
        
        # Send SMS
        try:
            message = self.twilio_client.messages.create(
                body=f"Your TradeSense verification code is: {code}\n\nThis code expires in 10 minutes.",
                from_=self.twilio_from_number,
                to=phone_number
            )
            
            # Track metric
            security_metrics.mfa_codes_sent.labels(method=MFAMethod.SMS).inc()
            
            return code
            
        except Exception as e:
            print(f"SMS send error: {e}")
            return None
    
    async def _send_email_code(self, user: User, db: AsyncSession) -> Optional[str]:
        """Send email verification code."""
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        
        # Store code
        await db.execute(
            text("""
                INSERT INTO mfa_verification_codes (
                    user_id, code_hash, method, expires_at
                ) VALUES (
                    :user_id, :code_hash, :method, :expires_at
                )
            """),
            {
                "user_id": user.id,
                "code_hash": self._hash_code(code),
                "method": MFAMethod.EMAIL,
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
        )
        await db.commit()
        
        # Send email
        subject = "TradeSense Verification Code"
        body = f"""
        <h2>Verification Code</h2>
        <p>Your TradeSense verification code is:</p>
        <h1 style="font-size: 32px; letter-spacing: 8px; text-align: center;">{code}</h1>
        <p>This code expires in 10 minutes.</p>
        <p>If you didn't request this code, please ignore this email.</p>
        """
        
        await email_service.send_email(
            to_email=user.email,
            subject=subject,
            body=body,
            is_html=True
        )
        
        # Track metric
        security_metrics.mfa_codes_sent.labels(method=MFAMethod.EMAIL).inc()
        
        return code
    
    async def _verify_code(self, user: User, method: str, code: str, db: AsyncSession) -> bool:
        """Verify a time-based code."""
        result = await db.execute(
            text("""
                SELECT id
                FROM mfa_verification_codes
                WHERE user_id = :user_id
                AND method = :method
                AND code_hash = :code_hash
                AND expires_at > NOW()
                AND used_at IS NULL
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {
                "user_id": user.id,
                "method": method,
                "code_hash": self._hash_code(code)
            }
        )
        
        code_record = result.first()
        if code_record:
            # Mark as used
            await db.execute(
                text("""
                    UPDATE mfa_verification_codes
                    SET used_at = NOW()
                    WHERE id = :id
                """),
                {"id": code_record.id}
            )
            await db.commit()
            return True
        
        return False
    
    async def _verify_backup_code(self, user: User, code: str, db: AsyncSession) -> bool:
        """Verify a backup code."""
        # Normalize code (remove dashes)
        normalized_code = code.replace('-', '').upper()
        
        result = await db.execute(
            text("""
                SELECT id
                FROM mfa_backup_codes
                WHERE user_id = :user_id
                AND code_hash = :code_hash
                AND status = 'active'
                LIMIT 1
            """),
            {
                "user_id": user.id,
                "code_hash": self._hash_code(f"{normalized_code[:4]}-{normalized_code[4:]}")
            }
        )
        
        backup_code = result.first()
        if backup_code:
            # Mark as used
            await db.execute(
                text("""
                    UPDATE mfa_backup_codes
                    SET status = 'used',
                        used_at = NOW()
                    WHERE id = :id
                """),
                {"id": backup_code.id}
            )
            await db.commit()
            
            # Track metric
            security_metrics.backup_codes_used.inc()
            
            return True
        
        return False
    
    async def _is_rate_limited(self, user: User, db: AsyncSession) -> bool:
        """Check if user is rate limited."""
        cutoff_time = datetime.utcnow() - self.lockout_duration
        
        result = await db.execute(
            text("""
                SELECT COUNT(*) as failed_attempts
                FROM mfa_auth_attempts
                WHERE user_id = :user_id
                AND success = FALSE
                AND attempted_at > :cutoff_time
            """),
            {
                "user_id": user.id,
                "cutoff_time": cutoff_time
            }
        )
        
        failed_attempts = result.scalar()
        return failed_attempts >= self.max_attempts
    
    async def _record_successful_auth(self, user: User, method: str, db: AsyncSession):
        """Record successful MFA authentication."""
        await db.execute(
            text("""
                INSERT INTO mfa_auth_attempts (
                    user_id, method, success, attempted_at
                ) VALUES (
                    :user_id, :method, TRUE, NOW()
                )
            """),
            {
                "user_id": user.id,
                "method": method
            }
        )
        
        # Update device last used
        await db.execute(
            text("""
                UPDATE mfa_devices
                SET last_used_at = NOW()
                WHERE user_id = :user_id
                AND device_type = :device_type
                AND status = 'active'
            """),
            {
                "user_id": user.id,
                "device_type": method
            }
        )
        
        await db.commit()
        
        # Track metric
        security_metrics.mfa_verifications.labels(
            method=method,
            result="success"
        ).inc()
    
    async def _record_failed_attempt(self, user: User, method: str, db: AsyncSession):
        """Record failed MFA attempt."""
        await db.execute(
            text("""
                INSERT INTO mfa_auth_attempts (
                    user_id, method, success, attempted_at
                ) VALUES (
                    :user_id, :method, FALSE, NOW()
                )
            """),
            {
                "user_id": user.id,
                "method": method
            }
        )
        await db.commit()
        
        # Track metric
        security_metrics.mfa_verifications.labels(
            method=method,
            result="failed"
        ).inc()
    
    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret."""
        # In production, use proper encryption (e.g., Fernet)
        from cryptography.fernet import Fernet
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.encrypt(secret.encode()).decode()
    
    def _decrypt_secret(self, encrypted: str) -> str:
        """Decrypt TOTP secret."""
        from cryptography.fernet import Fernet
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(encrypted.encode()).decode()
    
    def _hash_code(self, code: str) -> str:
        """Hash verification code or backup code."""
        import hashlib
        return hashlib.sha256(f"{code}{settings.SECRET_KEY}".encode()).hexdigest()


# Initialize service
mfa_service = MFAService()