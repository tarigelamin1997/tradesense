"""
Mobile-optimized authentication endpoints.
Includes device registration, biometric auth support, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
import secrets
import uuid

from core.db.session import get_db
from core.auth import get_current_user, create_access_token, verify_password
from models.user import User
from src.backend.api.mobile.base import (
    MobileResponse, MobileErrorResponse, DeviceInfo,
    get_device_info, RequireAuth, OptionalAuth
)
from services.auth_service import AuthService
from sqlalchemy import text


router = APIRouter(prefix="/api/mobile/v1/auth")


class MobileLoginRequest(BaseModel):
    """Mobile login request."""
    username: str
    password: str
    device_info: DeviceInfo
    biometric_token: Optional[str] = None  # For subsequent biometric logins


class MobileLoginResponse(BaseModel):
    """Mobile login response."""
    access_token: str
    refresh_token: str
    expires_in: int
    user: Dict[str, Any]
    requires_mfa: bool = False
    mfa_session_id: Optional[str] = None
    biometric_token: Optional[str] = None  # For enabling biometric auth


class MobileRegisterRequest(BaseModel):
    """Mobile registration request."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    device_info: DeviceInfo
    referral_code: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str
    device_id: str


class BiometricSetupRequest(BaseModel):
    """Biometric authentication setup."""
    device_id: str
    biometric_type: str  # face_id, touch_id, fingerprint
    public_key: str  # For cryptographic verification


class DeviceRegistrationRequest(BaseModel):
    """Device registration/update request."""
    device_info: DeviceInfo
    enable_notifications: bool = True


@router.post("/login", response_model=MobileResponse[MobileLoginResponse])
async def mobile_login(
    request: MobileLoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MobileLoginResponse]:
    """Mobile-optimized login endpoint."""
    try:
        auth_service = AuthService(db)
        
        # Check for biometric login
        if request.biometric_token:
            user = await _verify_biometric_login(
                request.biometric_token,
                request.device_info.device_id,
                db
            )
            if not user:
                raise HTTPException(401, "Invalid biometric token")
        else:
            # Standard username/password login
            user = auth_service.authenticate_user(request.username, request.password)
            if not user:
                raise HTTPException(401, "Invalid credentials")
        
        # Check if MFA is required
        if user.mfa_enabled and not request.biometric_token:
            # Create MFA session
            session_id = await _create_mfa_session(user, request.device_info, db)
            
            return MobileResponse(
                data=MobileLoginResponse(
                    access_token="",
                    refresh_token="",
                    expires_in=0,
                    user={},
                    requires_mfa=True,
                    mfa_session_id=session_id
                )
            )
        
        # Register/update device
        await _register_device(user, request.device_info, db)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = await _create_refresh_token(user, request.device_info.device_id, db)
        
        # Generate biometric token if this is first login from device
        biometric_token = None
        if not request.biometric_token:
            biometric_token = await _create_biometric_token(
                user, 
                request.device_info.device_id, 
                db
            )
        
        # Prepare user data
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "subscription_tier": user.subscription_tier,
            "settings": user.settings or {},
            "features": await _get_user_features(user)
        }
        
        return MobileResponse(
            data=MobileLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600,  # 1 hour
                user=user_data,
                biometric_token=biometric_token
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login failed: {str(e)}")


@router.post("/register", response_model=MobileResponse[MobileLoginResponse])
async def mobile_register(
    request: MobileRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MobileLoginResponse]:
    """Mobile registration endpoint."""
    try:
        auth_service = AuthService(db)
        
        # Check if user exists
        existing = auth_service.get_user_by_email(request.email)
        if existing:
            raise HTTPException(400, "Email already registered")
        
        existing = auth_service.get_user_by_username(request.username)
        if existing:
            raise HTTPException(400, "Username already taken")
        
        # Create user
        from api.v1.auth.schemas import UserRegistration
        registration_data = UserRegistration(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )
        
        user = auth_service.create_user(registration_data)
        
        # Apply referral code if provided
        if request.referral_code:
            await _apply_referral_code(user, request.referral_code, db)
        
        # Register device
        await _register_device(user, request.device_info, db)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = await _create_refresh_token(user, request.device_info.device_id, db)
        biometric_token = await _create_biometric_token(user, request.device_info.device_id, db)
        
        # Prepare user data
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "subscription_tier": user.subscription_tier,
            "settings": user.settings or {},
            "features": await _get_user_features(user)
        }
        
        return MobileResponse(
            data=MobileLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600,
                user=user_data,
                biometric_token=biometric_token
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Registration failed: {str(e)}")


@router.post("/refresh", response_model=MobileResponse[MobileLoginResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MobileLoginResponse]:
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        result = await db.execute(
            text("""
                SELECT u.*, mrt.id as token_id
                FROM mobile_refresh_tokens mrt
                JOIN users u ON mrt.user_id = u.id
                WHERE mrt.token = :token
                AND mrt.device_id = :device_id
                AND mrt.expires_at > NOW()
                AND mrt.revoked = FALSE
            """),
            {
                "token": request.refresh_token,
                "device_id": request.device_id
            }
        )
        
        user_row = result.first()
        if not user_row:
            raise HTTPException(401, "Invalid refresh token")
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user_row.id)})
        
        # Optionally rotate refresh token
        new_refresh_token = await _rotate_refresh_token(
            user_row.id,
            user_row.token_id,
            request.device_id,
            db
        )
        
        # Prepare user data
        user_data = {
            "id": str(user_row.id),
            "username": user_row.username,
            "email": user_row.email,
            "full_name": user_row.full_name,
            "avatar_url": user_row.avatar_url,
            "subscription_tier": user_row.subscription_tier,
            "settings": user_row.settings or {},
            "features": await _get_user_features(user_row)
        }
        
        return MobileResponse(
            data=MobileLoginResponse(
                access_token=access_token,
                refresh_token=new_refresh_token or request.refresh_token,
                expires_in=3600,
                user=user_data
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Token refresh failed: {str(e)}")


@router.post("/logout")
async def mobile_logout(
    device_id: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Logout from mobile device."""
    try:
        # Revoke refresh tokens for device
        await db.execute(
            text("""
                UPDATE mobile_refresh_tokens
                SET revoked = TRUE,
                    revoked_at = NOW()
                WHERE user_id = :user_id
                AND device_id = :device_id
                AND revoked = FALSE
            """),
            {
                "user_id": current_user.id,
                "device_id": device_id
            }
        )
        
        # Clear device registration
        await db.execute(
            text("""
                UPDATE mobile_devices
                SET push_token = NULL,
                    is_active = FALSE
                WHERE user_id = :user_id
                AND device_id = :device_id
            """),
            {
                "user_id": current_user.id,
                "device_id": device_id
            }
        )
        
        await db.commit()
        
        return MobileResponse(
            data={"message": "Logged out successfully"}
        )
        
    except Exception as e:
        raise HTTPException(500, f"Logout failed: {str(e)}")


@router.post("/device/register")
async def register_device(
    request: DeviceRegistrationRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Register or update device information."""
    try:
        await _register_device(current_user, request.device_info, db)
        
        # Update notification preferences
        if request.enable_notifications and request.device_info.push_token:
            await db.execute(
                text("""
                    UPDATE mobile_devices
                    SET push_notifications_enabled = TRUE
                    WHERE user_id = :user_id
                    AND device_id = :device_id
                """),
                {
                    "user_id": current_user.id,
                    "device_id": request.device_info.device_id
                }
            )
            await db.commit()
        
        return MobileResponse(
            data={"message": "Device registered successfully"}
        )
        
    except Exception as e:
        raise HTTPException(500, f"Device registration failed: {str(e)}")


@router.post("/biometric/setup")
async def setup_biometric(
    request: BiometricSetupRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Set up biometric authentication for device."""
    try:
        # Store biometric public key
        await db.execute(
            text("""
                INSERT INTO mobile_biometric_keys (
                    user_id, device_id, biometric_type,
                    public_key, created_at
                ) VALUES (
                    :user_id, :device_id, :biometric_type,
                    :public_key, NOW()
                )
                ON CONFLICT (user_id, device_id)
                DO UPDATE SET
                    biometric_type = :biometric_type,
                    public_key = :public_key,
                    updated_at = NOW()
            """),
            {
                "user_id": current_user.id,
                "device_id": request.device_id,
                "biometric_type": request.biometric_type,
                "public_key": request.public_key
            }
        )
        
        await db.commit()
        
        return MobileResponse(
            data={"message": "Biometric authentication enabled"}
        )
        
    except Exception as e:
        raise HTTPException(500, f"Biometric setup failed: {str(e)}")


@router.delete("/biometric/disable")
async def disable_biometric(
    device_id: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Disable biometric authentication for device."""
    try:
        await db.execute(
            text("""
                DELETE FROM mobile_biometric_keys
                WHERE user_id = :user_id
                AND device_id = :device_id
            """),
            {
                "user_id": current_user.id,
                "device_id": device_id
            }
        )
        
        await db.commit()
        
        return MobileResponse(
            data={"message": "Biometric authentication disabled"}
        )
        
    except Exception as e:
        raise HTTPException(500, f"Failed to disable biometric: {str(e)}")


# Helper functions
async def _register_device(user: User, device_info: DeviceInfo, db: AsyncSession):
    """Register or update mobile device."""
    await db.execute(
        text("""
            INSERT INTO mobile_devices (
                device_id, user_id, device_type, os_version,
                app_version, push_token, timezone, language,
                last_active_at, is_active
            ) VALUES (
                :device_id, :user_id, :device_type, :os_version,
                :app_version, :push_token, :timezone, :language,
                NOW(), TRUE
            )
            ON CONFLICT (device_id)
            DO UPDATE SET
                user_id = :user_id,
                device_type = :device_type,
                os_version = :os_version,
                app_version = :app_version,
                push_token = COALESCE(:push_token, mobile_devices.push_token),
                timezone = COALESCE(:timezone, mobile_devices.timezone),
                language = COALESCE(:language, mobile_devices.language),
                last_active_at = NOW(),
                is_active = TRUE
        """),
        {
            "device_id": device_info.device_id,
            "user_id": user.id,
            "device_type": device_info.device_type,
            "os_version": device_info.os_version,
            "app_version": device_info.app_version,
            "push_token": device_info.push_token,
            "timezone": device_info.timezone,
            "language": device_info.language
        }
    )
    await db.commit()


async def _create_refresh_token(user: User, device_id: str, db: AsyncSession) -> str:
    """Create a refresh token for mobile device."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    await db.execute(
        text("""
            INSERT INTO mobile_refresh_tokens (
                user_id, device_id, token, expires_at
            ) VALUES (
                :user_id, :device_id, :token, :expires_at
            )
        """),
        {
            "user_id": user.id,
            "device_id": device_id,
            "token": token,
            "expires_at": expires_at
        }
    )
    await db.commit()
    
    return token


async def _rotate_refresh_token(
    user_id: str,
    old_token_id: str,
    device_id: str,
    db: AsyncSession
) -> Optional[str]:
    """Rotate refresh token for enhanced security."""
    # Mark old token as revoked
    await db.execute(
        text("""
            UPDATE mobile_refresh_tokens
            SET revoked = TRUE,
                revoked_at = NOW()
            WHERE id = :token_id
        """),
        {"token_id": old_token_id}
    )
    
    # Create new token
    return await _create_refresh_token(
        User(id=user_id), 
        device_id, 
        db
    )


async def _create_biometric_token(user: User, device_id: str, db: AsyncSession) -> str:
    """Create a token for biometric authentication."""
    token = secrets.token_urlsafe(32)
    
    await db.execute(
        text("""
            INSERT INTO mobile_biometric_tokens (
                user_id, device_id, token, created_at
            ) VALUES (
                :user_id, :device_id, :token, NOW()
            )
            ON CONFLICT (user_id, device_id)
            DO UPDATE SET
                token = :token,
                created_at = NOW()
        """),
        {
            "user_id": user.id,
            "device_id": device_id,
            "token": token
        }
    )
    await db.commit()
    
    return token


async def _verify_biometric_login(
    biometric_token: str,
    device_id: str,
    db: AsyncSession
) -> Optional[User]:
    """Verify biometric login token."""
    result = await db.execute(
        text("""
            SELECT u.*
            FROM users u
            JOIN mobile_biometric_tokens mbt ON u.id = mbt.user_id
            WHERE mbt.token = :token
            AND mbt.device_id = :device_id
            AND mbt.created_at > NOW() - INTERVAL '90 days'
        """),
        {
            "token": biometric_token,
            "device_id": device_id
        }
    )
    
    return result.first()


async def _create_mfa_session(user: User, device_info: DeviceInfo, db: AsyncSession) -> str:
    """Create MFA session for mobile."""
    from core.cache import redis_client
    
    session_id = str(uuid.uuid4())
    session_data = {
        "user_id": user.id,
        "device_id": device_info.device_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store in Redis for 10 minutes
    await redis_client.setex(
        f"mobile_mfa_session:{session_id}",
        600,
        session_data
    )
    
    return session_id


async def _get_user_features(user: User) -> Dict[str, bool]:
    """Get enabled features for user."""
    from src.backend.api.mobile.base import MobileFeatureFlags
    
    features = {}
    for feature in [
        MobileFeatureFlags.BIOMETRIC_AUTH,
        MobileFeatureFlags.PUSH_NOTIFICATIONS,
        MobileFeatureFlags.OFFLINE_MODE,
        MobileFeatureFlags.ADVANCED_CHARTS,
        MobileFeatureFlags.VOICE_COMMANDS,
        MobileFeatureFlags.AR_FEATURES
    ]:
        features[feature] = await MobileFeatureFlags.is_enabled(feature, user)
    
    return features


async def _apply_referral_code(user: User, code: str, db: AsyncSession):
    """Apply referral code benefits."""
    # This would implement referral tracking
    # For now, just log it
    pass