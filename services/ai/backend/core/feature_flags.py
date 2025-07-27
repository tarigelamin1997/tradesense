"""
Dynamic feature flags system

Provides runtime feature flag management with support for:
- User-specific flags
- Percentage rollouts
- A/B testing
- Flag dependencies
"""

import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

from core.cache import cache_manager
from core.logging_config import get_logger
from core.db.session import SessionLocal
from models.user import User

logger = get_logger(__name__)


class FlagType(str, Enum):
    """Types of feature flags"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    USER_ATTRIBUTE = "user_attribute"
    SCHEDULE = "schedule"
    VARIANT = "variant"


class FlagStatus(str, Enum):
    """Feature flag status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class FeatureFlagConfig(BaseModel):
    """Feature flag configuration"""
    name: str
    description: str
    flag_type: FlagType
    status: FlagStatus = FlagStatus.ACTIVE
    default_value: Any = False
    
    # Type-specific configurations
    percentage: Optional[float] = Field(None, ge=0, le=100)
    user_ids: Optional[List[str]] = None
    user_attributes: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    variants: Optional[Dict[str, Any]] = None
    variant_weights: Optional[Dict[str, float]] = None
    
    # Dependencies
    depends_on: Optional[List[str]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class FeatureFlag:
    """Individual feature flag implementation"""
    
    def __init__(self, config: FeatureFlagConfig):
        self.config = config
    
    def is_enabled_for_user(self, user: Optional[User] = None, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if flag is enabled for specific user"""
        if self.config.status != FlagStatus.ACTIVE:
            return bool(self.config.default_value)
        
        # Check dependencies first
        if self.config.depends_on:
            for dep_flag in self.config.depends_on:
                if not feature_flags.is_enabled(dep_flag, user, context):
                    return False
        
        # Evaluate based on flag type
        if self.config.flag_type == FlagType.BOOLEAN:
            return bool(self.config.default_value)
        
        elif self.config.flag_type == FlagType.PERCENTAGE:
            if not user:
                return False
            return self._check_percentage_rollout(user)
        
        elif self.config.flag_type == FlagType.USER_LIST:
            if not user:
                return False
            return str(user.id) in (self.config.user_ids or [])
        
        elif self.config.flag_type == FlagType.USER_ATTRIBUTE:
            if not user:
                return False
            return self._check_user_attributes(user, context)
        
        elif self.config.flag_type == FlagType.SCHEDULE:
            return self._check_schedule()
        
        elif self.config.flag_type == FlagType.VARIANT:
            # For variant flags, being "enabled" means having any variant
            return self.get_variant_for_user(user) is not None
        
        return bool(self.config.default_value)
    
    def get_variant_for_user(self, user: Optional[User] = None) -> Optional[str]:
        """Get variant for A/B testing"""
        if self.config.flag_type != FlagType.VARIANT or not self.config.variants:
            return None
        
        if not user:
            return None
        
        # Use consistent hashing for user bucketing
        user_hash = int(hashlib.md5(f"{self.config.name}:{user.id}".encode()).hexdigest(), 16)
        bucket = (user_hash % 100) / 100.0
        
        # Select variant based on weights
        cumulative = 0.0
        for variant, weight in (self.config.variant_weights or {}).items():
            cumulative += weight
            if bucket <= cumulative:
                return variant
        
        return None
    
    def _check_percentage_rollout(self, user: User) -> bool:
        """Check if user falls within percentage rollout"""
        if not self.config.percentage:
            return False
        
        # Use consistent hashing for stable rollout
        user_hash = int(hashlib.md5(f"{self.config.name}:{user.id}".encode()).hexdigest(), 16)
        user_bucket = (user_hash % 10000) / 100.0
        
        return user_bucket < self.config.percentage
    
    def _check_user_attributes(self, user: User, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user matches required attributes"""
        if not self.config.user_attributes:
            return True
        
        for attr, expected_value in self.config.user_attributes.items():
            # Check user attributes
            if hasattr(user, attr):
                actual_value = getattr(user, attr)
            elif context and attr in context:
                actual_value = context[attr]
            else:
                return False
            
            # Support different comparison types
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif isinstance(expected_value, dict) and "operator" in expected_value:
                if not self._evaluate_operator(actual_value, expected_value):
                    return False
            elif actual_value != expected_value:
                return False
        
        return True
    
    def _check_schedule(self) -> bool:
        """Check if current time is within schedule"""
        now = datetime.utcnow()
        
        if self.config.start_date and now < self.config.start_date:
            return False
        
        if self.config.end_date and now > self.config.end_date:
            return False
        
        return True
    
    def _evaluate_operator(self, value: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate operator-based conditions"""
        operator = condition.get("operator")
        expected = condition.get("value")
        
        if operator == "gt":
            return value > expected
        elif operator == "gte":
            return value >= expected
        elif operator == "lt":
            return value < expected
        elif operator == "lte":
            return value <= expected
        elif operator == "in":
            return value in expected
        elif operator == "not_in":
            return value not in expected
        elif operator == "contains":
            return expected in str(value)
        elif operator == "regex":
            import re
            return bool(re.match(expected, str(value)))
        
        return False


class FeatureFlagsManager:
    """Manages all feature flags"""
    
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_flags()
    
    def _load_flags(self):
        """Load feature flags from configuration"""
        # Load from database or configuration file
        # For now, define flags in code
        self._register_default_flags()
    
    def _register_default_flags(self):
        """Register default feature flags"""
        default_flags = [
            FeatureFlagConfig(
                name="oauth_login",
                description="Enable OAuth social login",
                flag_type=FlagType.BOOLEAN,
                default_value=True
            ),
            FeatureFlagConfig(
                name="mfa_enforcement",
                description="Enforce MFA for all users",
                flag_type=FlagType.PERCENTAGE,
                percentage=100.0,
                default_value=False
            ),
            FeatureFlagConfig(
                name="ai_trade_analysis",
                description="Enable AI-powered trade analysis",
                flag_type=FlagType.USER_ATTRIBUTE,
                user_attributes={"subscription_tier": ["premium", "enterprise"]},
                default_value=False
            ),
            FeatureFlagConfig(
                name="new_dashboard_ui",
                description="New dashboard UI experiment",
                flag_type=FlagType.VARIANT,
                variants={"control": {}, "variant_a": {"layout": "grid"}, "variant_b": {"layout": "list"}},
                variant_weights={"control": 0.5, "variant_a": 0.25, "variant_b": 0.25}
            ),
            FeatureFlagConfig(
                name="websocket_trading",
                description="Real-time trading via WebSocket",
                flag_type=FlagType.USER_LIST,
                user_ids=[],  # Add beta tester IDs
                default_value=False
            ),
            FeatureFlagConfig(
                name="holiday_promotion",
                description="Holiday promotional features",
                flag_type=FlagType.SCHEDULE,
                start_date=datetime(2024, 12, 1),
                end_date=datetime(2024, 12, 31),
                default_value=True
            ),
            FeatureFlagConfig(
                name="advanced_analytics",
                description="Advanced analytics features",
                flag_type=FlagType.BOOLEAN,
                default_value=True,
                depends_on=["ai_trade_analysis"]
            ),
            FeatureFlagConfig(
                name="maintenance_mode",
                description="System maintenance mode",
                flag_type=FlagType.BOOLEAN,
                default_value=False
            ),
            FeatureFlagConfig(
                name="rate_limit_override",
                description="Override rate limits for specific users",
                flag_type=FlagType.USER_ATTRIBUTE,
                user_attributes={"is_internal": True},
                default_value=False
            ),
            FeatureFlagConfig(
                name="export_feature",
                description="Data export functionality",
                flag_type=FlagType.PERCENTAGE,
                percentage=100.0,
                default_value=True
            )
        ]
        
        for flag_config in default_flags:
            self.register_flag(flag_config)
    
    def register_flag(self, config: FeatureFlagConfig):
        """Register a new feature flag"""
        flag = FeatureFlag(config)
        self.flags[config.name] = flag
        logger.info(f"Registered feature flag: {config.name}")
    
    def is_enabled(self, flag_name: str, user: Optional[User] = None, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a feature flag is enabled"""
        # Check cache first
        cache_key = f"feature_flag:{flag_name}:{user.id if user else 'anonymous'}"
        cached_value = cache_manager.get(cache_key)
        if cached_value is not None:
            return cached_value
        
        # Evaluate flag
        if flag_name not in self.flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        flag = self.flags[flag_name]
        enabled = flag.is_enabled_for_user(user, context)
        
        # Cache result for 1 minute
        cache_manager.set(cache_key, enabled, ttl=60)
        
        # Log flag evaluation
        logger.debug(
            f"Feature flag evaluated: {flag_name}={enabled}",
            extra={
                "flag_name": flag_name,
                "user_id": str(user.id) if user else None,
                "enabled": enabled,
                "context": context
            }
        )
        
        return enabled
    
    def get_variant(self, flag_name: str, user: Optional[User] = None) -> Optional[str]:
        """Get variant for A/B testing flag"""
        if flag_name not in self.flags:
            return None
        
        flag = self.flags[flag_name]
        return flag.get_variant_for_user(user)
    
    def get_all_flags_for_user(self, user: Optional[User] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Union[bool, str]]:
        """Get all flag values for a user"""
        result = {}
        
        for flag_name, flag in self.flags.items():
            if flag.config.flag_type == FlagType.VARIANT:
                variant = flag.get_variant_for_user(user)
                if variant:
                    result[flag_name] = variant
            else:
                result[flag_name] = flag.is_enabled_for_user(user, context)
        
        return result
    
    def update_flag(self, flag_name: str, updates: Dict[str, Any]):
        """Update a feature flag configuration"""
        if flag_name not in self.flags:
            raise ValueError(f"Feature flag {flag_name} not found")
        
        flag = self.flags[flag_name]
        
        # Update configuration
        for key, value in updates.items():
            if hasattr(flag.config, key):
                setattr(flag.config, key, value)
        
        flag.config.updated_at = datetime.utcnow()
        
        # Clear cache
        cache_manager.invalidate_cache_pattern(f"feature_flag:{flag_name}:*")
        
        logger.info(f"Updated feature flag: {flag_name}", extra={"updates": updates})
    
    def get_flag_config(self, flag_name: str) -> Optional[FeatureFlagConfig]:
        """Get flag configuration"""
        if flag_name in self.flags:
            return self.flags[flag_name].config
        return None
    
    def list_flags(self) -> List[FeatureFlagConfig]:
        """List all feature flags"""
        return [flag.config for flag in self.flags.values()]
    
    def export_flags(self) -> Dict[str, Any]:
        """Export all flags as JSON"""
        return {
            name: flag.config.model_dump()
            for name, flag in self.flags.items()
        }
    
    def import_flags(self, flags_data: Dict[str, Any]):
        """Import flags from JSON"""
        for name, config_data in flags_data.items():
            config = FeatureFlagConfig(**config_data)
            self.register_flag(config)


# Global feature flags instance
feature_flags = FeatureFlagsManager()


# Decorator for feature flag protection
def feature_flag_required(flag_name: str, redirect_on_disabled: bool = False):
    """Decorator to check feature flag before executing function"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Try to get user from request
            user = None
            for arg in args:
                if hasattr(arg, 'state') and hasattr(arg.state, 'user'):
                    user = arg.state.user
                    break
            
            if not feature_flags.is_enabled(flag_name, user):
                if redirect_on_disabled:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=404,
                        detail="Feature not available"
                    )
                return None
            
            return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            user = None
            for arg in args:
                if hasattr(arg, 'state') and hasattr(arg.state, 'user'):
                    user = arg.state.user
                    break
            
            if not feature_flags.is_enabled(flag_name, user):
                if redirect_on_disabled:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=404,
                        detail="Feature not available"
                    )
                return None
            
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience functions
def is_feature_enabled(flag_name: str, user: Optional[User] = None) -> bool:
    """Check if a feature is enabled"""
    return feature_flags.is_enabled(flag_name, user)


def get_feature_variant(flag_name: str, user: Optional[User] = None) -> Optional[str]:
    """Get feature variant for A/B testing"""
    return feature_flags.get_variant(flag_name, user)