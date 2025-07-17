"""
Base classes and utilities for mobile API endpoints.
Provides common functionality for mobile-optimized responses.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
from fastapi import Query, Depends, HTTPException, Request
from datetime import datetime
import hashlib
import json
from enum import Enum

from core.auth import get_current_user
from models.user import User


T = TypeVar('T')


class DeviceType(str, Enum):
    """Supported mobile device types."""
    IOS = "ios"
    ANDROID = "android"
    TABLET_IOS = "tablet_ios"
    TABLET_ANDROID = "tablet_android"
    OTHER = "other"


class MobilePaginationParams(BaseModel):
    """Standard pagination parameters for mobile endpoints."""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class MobileResponse(BaseModel, Generic[T]):
    """Standard mobile API response wrapper."""
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"


class MobilePaginatedResponse(MobileResponse[T]):
    """Paginated response for mobile endpoints."""
    pagination: Dict[str, Any]


class MobileErrorResponse(BaseModel):
    """Standard error response for mobile API."""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeviceInfo(BaseModel):
    """Device information from mobile client."""
    device_id: str
    device_type: DeviceType
    os_version: str
    app_version: str
    push_token: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
) -> MobilePaginationParams:
    """Dependency for pagination parameters."""
    return MobilePaginationParams(page=page, limit=limit)


def get_device_info(request: Request) -> Optional[DeviceInfo]:
    """Extract device information from request headers."""
    headers = request.headers
    
    device_id = headers.get("X-Device-ID")
    if not device_id:
        return None
    
    return DeviceInfo(
        device_id=device_id,
        device_type=headers.get("X-Device-Type", DeviceType.OTHER),
        os_version=headers.get("X-OS-Version", "unknown"),
        app_version=headers.get("X-App-Version", "unknown"),
        push_token=headers.get("X-Push-Token"),
        timezone=headers.get("X-Timezone"),
        language=headers.get("X-Language")
    )


def create_paginated_response(
    items: List[Any],
    total: int,
    pagination: MobilePaginationParams,
    **kwargs
) -> Dict[str, Any]:
    """Create a standard paginated response."""
    total_pages = (total + pagination.limit - 1) // pagination.limit
    
    return {
        "success": True,
        "data": items,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": pagination.page < total_pages,
            "has_prev": pagination.page > 1
        },
        "timestamp": datetime.utcnow(),
        **kwargs
    }


def create_etag(data: Any) -> str:
    """Generate ETag for response caching."""
    if isinstance(data, (dict, list)):
        content = json.dumps(data, sort_keys=True, default=str)
    else:
        content = str(data)
    
    return hashlib.md5(content.encode()).hexdigest()


def check_etag(request: Request, etag: str) -> bool:
    """Check if client's ETag matches current data."""
    client_etag = request.headers.get("If-None-Match")
    return client_etag == etag


def optimize_image_url(url: str, width: Optional[int] = None, height: Optional[int] = None) -> str:
    """Generate optimized image URL for mobile devices."""
    if not url or not (width or height):
        return url
    
    # Add image optimization parameters
    params = []
    if width:
        params.append(f"w={width}")
    if height:
        params.append(f"h={height}")
    
    # Add format optimization
    params.append("fm=webp")
    params.append("q=80")
    
    # Construct optimized URL
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{'&'.join(params)}"


def format_currency(amount: float, currency: str = "USD") -> Dict[str, Any]:
    """Format currency for mobile display."""
    return {
        "amount": amount,
        "currency": currency,
        "formatted": f"${amount:,.2f}" if currency == "USD" else f"{amount:,.2f} {currency}"
    }


def format_percentage(value: float, decimals: int = 2) -> Dict[str, Any]:
    """Format percentage for mobile display."""
    return {
        "value": value,
        "formatted": f"{value:.{decimals}f}%",
        "is_positive": value > 0,
        "is_negative": value < 0
    }


class MobileAuthDependency:
    """Enhanced authentication dependency for mobile endpoints."""
    
    def __init__(self, required: bool = True):
        self.required = required
    
    async def __call__(
        self,
        request: Request,
        current_user: Optional[User] = Depends(get_current_user)
    ) -> Optional[User]:
        if self.required and not current_user:
            raise HTTPException(401, "Authentication required")
        
        # Track mobile session
        if current_user:
            device_info = get_device_info(request)
            if device_info:
                # Update last seen, device info, etc.
                # This would be implemented with actual session tracking
                pass
        
        return current_user


# Convenience instances
RequireAuth = MobileAuthDependency(required=True)
OptionalAuth = MobileAuthDependency(required=False)


class MobileFeatureFlags:
    """Feature flags specific to mobile apps."""
    
    # Feature flag keys
    BIOMETRIC_AUTH = "mobile_biometric_auth"
    PUSH_NOTIFICATIONS = "mobile_push_notifications"
    OFFLINE_MODE = "mobile_offline_mode"
    ADVANCED_CHARTS = "mobile_advanced_charts"
    VOICE_COMMANDS = "mobile_voice_commands"
    AR_FEATURES = "mobile_ar_features"
    
    @staticmethod
    async def is_enabled(feature: str, user: Optional[User] = None) -> bool:
        """Check if a mobile feature is enabled."""
        # This would integrate with the feature flags system
        # For now, return some defaults
        default_enabled = {
            MobileFeatureFlags.BIOMETRIC_AUTH: True,
            MobileFeatureFlags.PUSH_NOTIFICATIONS: True,
            MobileFeatureFlags.OFFLINE_MODE: False,
            MobileFeatureFlags.ADVANCED_CHARTS: True,
            MobileFeatureFlags.VOICE_COMMANDS: False,
            MobileFeatureFlags.AR_FEATURES: False
        }
        
        return default_enabled.get(feature, False)


class DataSyncInfo(BaseModel):
    """Information about data synchronization status."""
    last_sync: Optional[datetime] = None
    pending_changes: int = 0
    sync_in_progress: bool = False
    next_sync: Optional[datetime] = None
    sync_errors: List[str] = []