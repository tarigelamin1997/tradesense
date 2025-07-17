"""
Multi-Factor Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import re

from core.db.session import get_db
from core.auth import get_current_user
from models.user import User
from auth.mfa_service import mfa_service, MFAMethod
from monitoring.metrics import security_metrics
import hashlib
import secrets


router = APIRouter(prefix="/api/v1/mfa")


class SetupTOTPRequest(BaseModel):
    """Request to set up TOTP authentication."""
    pass


class VerifyTOTPSetupRequest(BaseModel):
    """Request to verify TOTP setup."""
    code: str = Field(..., min_length=6, max_length=6, regex="^[0-9]{6}$")


class SetupSMSRequest(BaseModel):
    """Request to set up SMS authentication."""
    phone_number: str = Field(..., min_length=10, max_length=20)
    
    @validator('phone_number')
    def validate_phone(cls, v):
        # Basic phone validation
        if not re.match(r'^\+?[1-9]\d{1,14}$', v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid phone number format')
        return v.replace(' ', '').replace('-', '')


class VerifySMSSetupRequest(BaseModel):
    """Request to verify SMS setup."""
    code: str = Field(..., min_length=6, max_length=6, regex="^[0-9]{6}$")


class MFAChallengeRequest(BaseModel):
    """Request for MFA challenge during login."""
    method: str = Field(..., regex="^(totp|sms|email|backup_codes)$")


class MFAVerificationRequest(BaseModel):
    """Request to verify MFA code."""
    method: str = Field(..., regex="^(totp|sms|email|backup_codes)$")
    code: str = Field(..., min_length=1, max_length=20)
    trust_device: bool = False
    device_name: Optional[str] = None


class RemoveMFADeviceRequest(BaseModel):
    """Request to remove an MFA device."""
    device_id: str
    password: str  # Require password for security


class TrustDeviceRequest(BaseModel):
    """Request to trust a device."""
    device_name: str = Field(..., min_length=1, max_length=100)
    trust_duration_days: int = Field(default=30, ge=1, le=365)


@router.get("/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get MFA status for current user."""
    devices = await mfa_service.list_mfa_devices(current_user, db)
    
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "methods": current_user.mfa_methods or [],
        "devices": devices,
        "backup_codes_available": any(d["type"] == MFAMethod.BACKUP_CODES for d in devices)
    }


@router.post("/totp/setup")
async def setup_totp(
    request: SetupTOTPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Set up TOTP authentication."""
    # Check if already has active TOTP
    devices = await mfa_service.list_mfa_devices(current_user, db)
    if any(d["type"] == MFAMethod.TOTP and d["status"] == "active" for d in devices):
        raise HTTPException(400, "TOTP already configured")
    
    result = await mfa_service.setup_totp(current_user, db)
    
    # Track metric
    security_metrics.mfa_setup_started.labels(method=MFAMethod.TOTP).inc()
    
    return {
        "qr_code": result["qr_code"],
        "manual_entry_key": result["manual_entry_key"],
        "manual_entry_setup": result["manual_entry_setup"]
    }


@router.post("/totp/verify")
async def verify_totp_setup(
    request: VerifyTOTPSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Verify TOTP setup."""
    success = await mfa_service.verify_totp_setup(current_user, request.code, db)
    
    if not success:
        raise HTTPException(400, "Invalid verification code")
    
    # Get backup codes
    backup_codes = await mfa_service.generate_backup_codes(current_user, db)
    
    return {
        "success": True,
        "message": "TOTP authentication enabled successfully",
        "backup_codes": backup_codes,
        "backup_codes_warning": "Save these backup codes in a secure place. Each code can only be used once."
    }


@router.post("/sms/setup")
async def setup_sms(
    request: SetupSMSRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Set up SMS authentication."""
    # Check if already has active SMS
    devices = await mfa_service.list_mfa_devices(current_user, db)
    if any(d["type"] == MFAMethod.SMS and d["status"] == "active" for d in devices):
        raise HTTPException(400, "SMS authentication already configured")
    
    success = await mfa_service.setup_sms(current_user, request.phone_number, db)
    
    if not success:
        raise HTTPException(500, "Failed to send SMS verification code")
    
    # Track metric
    security_metrics.mfa_setup_started.labels(method=MFAMethod.SMS).inc()
    
    return {
        "success": True,
        "message": f"Verification code sent to {request.phone_number[-4:]}",
        "phone_hint": f"***{request.phone_number[-4:]}"
    }


@router.post("/sms/verify")
async def verify_sms_setup(
    request: VerifySMSSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Verify SMS setup."""
    success = await mfa_service.verify_sms_setup(current_user, request.code, db)
    
    if not success:
        raise HTTPException(400, "Invalid verification code")
    
    return {
        "success": True,
        "message": "SMS authentication enabled successfully"
    }


@router.post("/challenge")
async def send_mfa_challenge(
    request: MFAChallengeRequest,
    session_id: str,  # From login session
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Send MFA challenge during login."""
    # Get user from session
    from core.cache import redis_client
    user_data = await redis_client.get(f"mfa_session:{session_id}")
    if not user_data:
        raise HTTPException(401, "Invalid session")
    
    user_id = user_data.get("user_id")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    # Send challenge
    result = await mfa_service.send_mfa_challenge(user, request.method, db)
    
    return result


@router.post("/verify")
async def verify_mfa(
    request: MFAVerificationRequest,
    session_id: str,  # From login session
    req: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Verify MFA code during login."""
    # Get user from session
    from core.cache import redis_client
    user_data = await redis_client.get(f"mfa_session:{session_id}")
    if not user_data:
        raise HTTPException(401, "Invalid session")
    
    user_id = user_data.get("user_id")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    # Verify code
    is_valid, error_message = await mfa_service.verify_mfa_code(
        user, request.method, request.code, db
    )
    
    if not is_valid:
        raise HTTPException(400, error_message or "Invalid code")
    
    # Handle device trust
    if request.trust_device:
        # Generate device fingerprint
        user_agent = req.headers.get("user-agent", "")
        ip_address = req.client.host
        device_fingerprint = hashlib.sha256(
            f"{user_agent}{ip_address}".encode()
        ).hexdigest()[:64]
        
        # Generate trust token
        trust_token = secrets.token_urlsafe(32)
        
        # Store trusted device
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        trust_duration = request.trust_duration_days or 30
        expires_at = datetime.utcnow() + timedelta(days=trust_duration)
        
        await db.execute(
            text("""
                INSERT INTO mfa_trusted_devices (
                    user_id, device_fingerprint, device_name,
                    trust_token, last_ip_address, last_user_agent,
                    expires_at
                ) VALUES (
                    :user_id, :device_fingerprint, :device_name,
                    :trust_token, :ip_address, :user_agent,
                    :expires_at
                )
                ON CONFLICT (user_id, device_fingerprint)
                DO UPDATE SET
                    trust_token = :trust_token,
                    last_ip_address = :ip_address,
                    last_user_agent = :user_agent,
                    last_used_at = NOW(),
                    expires_at = :expires_at
            """),
            {
                "user_id": user.id,
                "device_fingerprint": device_fingerprint,
                "device_name": request.device_name or f"Device {ip_address}",
                "trust_token": trust_token,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "expires_at": expires_at
            }
        )
        await db.commit()
    
    # Clear MFA session
    await redis_client.delete(f"mfa_session:{session_id}")
    
    # Generate auth token
    from core.auth import create_access_token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "trust_token": trust_token if request.trust_device else None
    }


@router.post("/backup-codes/regenerate")
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Regenerate backup codes."""
    # Disable old codes
    from sqlalchemy import text
    await db.execute(
        text("""
            UPDATE mfa_backup_codes
            SET status = 'disabled'
            WHERE user_id = :user_id
            AND status = 'active'
        """),
        {"user_id": current_user.id}
    )
    
    # Generate new codes
    backup_codes = await mfa_service.generate_backup_codes(current_user, db)
    
    return {
        "backup_codes": backup_codes,
        "warning": "Your old backup codes have been disabled. Save these new codes in a secure place."
    }


@router.delete("/disable")
async def disable_mfa(
    password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Disable all MFA for user."""
    # Verify password
    from core.auth import verify_password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(400, "Invalid password")
    
    success = await mfa_service.disable_mfa(current_user, db)
    
    if not success:
        raise HTTPException(500, "Failed to disable MFA")
    
    return {
        "success": True,
        "message": "Multi-factor authentication has been disabled"
    }


@router.delete("/device")
async def remove_mfa_device(
    request: RemoveMFADeviceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Remove a specific MFA device."""
    # Verify password
    from core.auth import verify_password
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(400, "Invalid password")
    
    # Check if this is the last active device
    devices = await mfa_service.list_mfa_devices(current_user, db)
    active_devices = [d for d in devices if d["status"] == "active" and d["id"] != request.device_id]
    
    if len(active_devices) == 0:
        raise HTTPException(
            400, 
            "Cannot remove the last MFA device. Disable MFA completely instead."
        )
    
    # Remove device
    from sqlalchemy import text
    result = await db.execute(
        text("""
            UPDATE mfa_devices
            SET status = 'disabled',
                disabled_at = NOW()
            WHERE id = :device_id
            AND user_id = :user_id
            AND status = 'active'
        """),
        {
            "device_id": request.device_id,
            "user_id": current_user.id
        }
    )
    
    if result.rowcount == 0:
        raise HTTPException(404, "Device not found")
    
    await db.commit()
    
    # Track metric
    security_metrics.mfa_device_removed.inc()
    
    return {
        "success": True,
        "message": "MFA device removed successfully"
    }


@router.get("/trusted-devices")
async def list_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """List trusted devices."""
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            SELECT 
                id, device_name, last_ip_address,
                created_at, last_used_at, expires_at
            FROM mfa_trusted_devices
            WHERE user_id = :user_id
            AND expires_at > NOW()
            ORDER BY last_used_at DESC
        """),
        {"user_id": current_user.id}
    )
    
    devices = []
    for row in result:
        devices.append({
            "id": str(row.id),
            "name": row.device_name,
            "last_ip": row.last_ip_address,
            "created_at": row.created_at,
            "last_used_at": row.last_used_at,
            "expires_at": row.expires_at
        })
    
    return {"trusted_devices": devices}


@router.delete("/trusted-devices/{device_id}")
async def remove_trusted_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Remove a trusted device."""
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            DELETE FROM mfa_trusted_devices
            WHERE id = :device_id
            AND user_id = :user_id
        """),
        {
            "device_id": device_id,
            "user_id": current_user.id
        }
    )
    
    if result.rowcount == 0:
        raise HTTPException(404, "Device not found")
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Trusted device removed"
    }


@router.get("/admin/stats", dependencies=[Depends(get_current_user)])
async def get_mfa_admin_stats(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get MFA statistics for admin dashboard."""
    from sqlalchemy import text
    
    # Get stats from view
    result = await db.execute(text("SELECT * FROM mfa_admin_stats"))
    stats = result.first()
    
    # Get recent events
    events_result = await db.execute(
        text("""
            SELECT event_type, COUNT(*) as count
            FROM mfa_security_events
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 10
        """)
    )
    
    recent_events = [
        {"type": row.event_type, "count": row.count}
        for row in events_result
    ]
    
    return {
        "users_with_mfa": stats.users_with_mfa,
        "users_without_mfa": stats.users_without_mfa,
        "mfa_adoption_rate": round(
            stats.users_with_mfa / (stats.users_with_mfa + stats.users_without_mfa) * 100, 2
        ) if (stats.users_with_mfa + stats.users_without_mfa) > 0 else 0,
        "devices": {
            "totp": stats.totp_devices,
            "sms": stats.sms_devices,
            "email": stats.email_devices
        },
        "backup_codes": {
            "users_with_codes": stats.users_with_backup_codes
        },
        "auth_attempts_24h": {
            "successful": stats.successful_auths_24h,
            "failed": stats.failed_auths_24h,
            "success_rate": round(
                stats.successful_auths_24h / (stats.successful_auths_24h + stats.failed_auths_24h) * 100, 2
            ) if (stats.successful_auths_24h + stats.failed_auths_24h) > 0 else 0
        },
        "recent_events": recent_events
    }


# Add MFA metrics to security_metrics
security_metrics.mfa_setup_started = Counter(
    'tradesense_mfa_setup_started_total',
    'MFA setup attempts started',
    ['method']
)

security_metrics.mfa_enabled = Counter(
    'tradesense_mfa_enabled_total',
    'MFA enabled by users',
    ['method']
)

security_metrics.mfa_disabled = Counter(
    'tradesense_mfa_disabled_total',
    'MFA disabled by users'
)

security_metrics.mfa_verifications = Counter(
    'tradesense_mfa_verifications_total',
    'MFA verification attempts',
    ['method', 'result']
)

security_metrics.mfa_codes_sent = Counter(
    'tradesense_mfa_codes_sent_total',
    'MFA codes sent',
    ['method']
)

security_metrics.backup_codes_used = Counter(
    'tradesense_mfa_backup_codes_used_total',
    'Backup codes used'
)

security_metrics.mfa_device_removed = Counter(
    'tradesense_mfa_device_removed_total',
    'MFA devices removed'
)