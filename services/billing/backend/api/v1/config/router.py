"""
Configuration and feature flags API endpoints

Provides runtime configuration management and feature flag controls
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from api.deps import get_current_user
from models.user import User
from core.config_env import get_env_config, config_manager
from core.feature_flags import feature_flags, FeatureFlagConfig, FlagType, FlagStatus
from core.config_validator import get_config_summary, ConfigurationValidator
from core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/config")


class ConfigResponse(BaseModel):
    """Configuration response model"""
    environment: str
    version: str
    features: Dict[str, bool]
    settings: Dict[str, Any]


class FeatureFlagUpdate(BaseModel):
    """Feature flag update request"""
    status: Optional[FlagStatus] = None
    percentage: Optional[float] = None
    user_ids: Optional[List[str]] = None
    user_attributes: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    default_value: Optional[Any] = None


@router.get("/", response_model=ConfigResponse)
async def get_configuration(
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get client configuration
    
    Returns configuration relevant to the current user including
    enabled features and settings.
    """
    config = get_env_config()
    
    # Get feature flags for user
    user_features = feature_flags.get_all_flags_for_user(current_user)
    
    # Build client-safe configuration
    client_config = {
        "environment": config.environment.value,
        "version": config.api_version,
        "features": user_features,
        "settings": {
            "api_prefix": config.api_prefix,
            "max_upload_size_mb": config.max_upload_size_mb,
            "allowed_file_types": config.allowed_file_types,
            "websocket_enabled": config.feature_flags.enable_websocket,
            "market_data_provider": config.market_data_provider
        }
    }
    
    # Add user-specific settings
    if current_user:
        client_config["settings"]["user"] = {
            "id": str(current_user.id),
            "email": current_user.email,
            "subscription_tier": getattr(current_user, "subscription_tier", "free"),
            "mfa_enabled": current_user.mfa_enabled if hasattr(current_user, "mfa_enabled") else False
        }
    
    return client_config


@router.get("/features", response_model=Dict[str, Any])
async def get_feature_flags(
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get all feature flags for current user
    
    Returns a dictionary of feature flag names to their values
    """
    flags = feature_flags.get_all_flags_for_user(current_user)
    
    return {
        "flags": flags,
        "user_id": str(current_user.id) if current_user else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/features/{flag_name}")
async def get_feature_flag(
    flag_name: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get specific feature flag value
    
    Returns the flag value and any variant information
    """
    if not feature_flags.get_flag_config(flag_name):
        raise HTTPException(404, f"Feature flag '{flag_name}' not found")
    
    enabled = feature_flags.is_enabled(flag_name, current_user)
    variant = feature_flags.get_variant(flag_name, current_user)
    
    return {
        "flag": flag_name,
        "enabled": enabled,
        "variant": variant,
        "user_id": str(current_user.id) if current_user else None
    }


# Admin endpoints
@router.get("/admin/summary", response_model=Dict[str, Any])
async def get_config_summary_admin(
    current_user: User = Depends(get_current_user)
):
    """
    Get configuration summary (admin only)
    
    Returns complete configuration overview
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    return get_config_summary()


@router.get("/admin/validate")
async def validate_configuration_admin(
    current_user: User = Depends(get_current_user)
):
    """
    Validate current configuration (admin only)
    
    Runs all configuration validation checks
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    validator = ConfigurationValidator()
    passed, results = await validator.validate_all()
    
    return {
        "passed": passed,
        "timestamp": datetime.utcnow().isoformat(),
        "results": [
            {
                "name": r.name,
                "passed": r.passed,
                "message": r.message,
                "severity": r.severity
            }
            for r in results
        ]
    }


@router.get("/admin/features", response_model=List[Dict[str, Any]])
async def list_all_feature_flags(
    current_user: User = Depends(get_current_user)
):
    """
    List all feature flags (admin only)
    
    Returns complete feature flag configurations
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    flags = feature_flags.list_flags()
    
    return [
        {
            "name": flag.name,
            "description": flag.description,
            "type": flag.flag_type.value,
            "status": flag.status.value,
            "default_value": flag.default_value,
            "configuration": {
                "percentage": flag.percentage,
                "user_ids": flag.user_ids,
                "user_attributes": flag.user_attributes,
                "start_date": flag.start_date.isoformat() if flag.start_date else None,
                "end_date": flag.end_date.isoformat() if flag.end_date else None,
                "variants": flag.variants,
                "variant_weights": flag.variant_weights,
                "depends_on": flag.depends_on
            },
            "metadata": {
                "created_at": flag.created_at.isoformat(),
                "updated_at": flag.updated_at.isoformat(),
                "created_by": flag.created_by,
                "tags": flag.tags
            }
        }
        for flag in flags
    ]


@router.put("/admin/features/{flag_name}")
async def update_feature_flag(
    flag_name: str,
    updates: FeatureFlagUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update feature flag configuration (admin only)
    
    Allows runtime modification of feature flags
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    if not feature_flags.get_flag_config(flag_name):
        raise HTTPException(404, f"Feature flag '{flag_name}' not found")
    
    # Convert update model to dict
    update_dict = updates.model_dump(exclude_unset=True)
    
    # Update flag
    try:
        feature_flags.update_flag(flag_name, update_dict)
        
        logger.info(
            f"Feature flag updated by admin",
            extra={
                "flag_name": flag_name,
                "admin_id": str(current_user.id),
                "updates": update_dict
            }
        )
        
        return {
            "status": "success",
            "flag": flag_name,
            "updates": update_dict,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update feature flag: {e}")
        raise HTTPException(500, f"Failed to update flag: {str(e)}")


@router.post("/admin/features/{flag_name}/test")
async def test_feature_flag(
    flag_name: str,
    test_user_id: Optional[str] = Body(None),
    test_context: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """
    Test feature flag evaluation (admin only)
    
    Allows testing how a flag would evaluate for a specific user
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    if not feature_flags.get_flag_config(flag_name):
        raise HTTPException(404, f"Feature flag '{flag_name}' not found")
    
    # Get test user if ID provided
    test_user = None
    if test_user_id:
        from core.db.session import SessionLocal
        db = SessionLocal()
        try:
            test_user = db.query(User).filter(User.id == test_user_id).first()
            if not test_user:
                raise HTTPException(404, f"Test user {test_user_id} not found")
        finally:
            db.close()
    
    # Evaluate flag
    enabled = feature_flags.is_enabled(flag_name, test_user, test_context)
    variant = feature_flags.get_variant(flag_name, test_user)
    
    return {
        "flag": flag_name,
        "test_user_id": test_user_id,
        "test_context": test_context,
        "result": {
            "enabled": enabled,
            "variant": variant
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/admin/export")
async def export_configuration(
    include_secrets: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """
    Export complete configuration (admin only)
    
    Exports configuration and feature flags for backup/migration
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Export configuration
    config_export = config_manager.export_config(include_secrets)
    
    # Export feature flags
    flags_export = feature_flags.export_flags()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": get_env_config().environment.value,
        "configuration": config_export,
        "feature_flags": flags_export
    }


@router.post("/admin/reload")
async def reload_configuration(
    current_user: User = Depends(get_current_user)
):
    """
    Reload configuration from environment (admin only)
    
    Forces a reload of configuration from environment variables
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    try:
        # Reinitialize configuration
        global config_manager
        from core.config_env import ConfigurationManager
        config_manager = ConfigurationManager()
        
        logger.info(
            "Configuration reloaded by admin",
            extra={"admin_id": str(current_user.id)}
        )
        
        return {
            "status": "success",
            "message": "Configuration reloaded",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(500, f"Failed to reload: {str(e)}")


@router.get("/env/{key}")
async def get_environment_variable(
    key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get specific environment variable (admin only)
    
    Useful for debugging configuration issues
    """
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Whitelist of safe environment variables to expose
    safe_vars = [
        "ENVIRONMENT",
        "API_VERSION",
        "RAILWAY_PROJECT_NAME",
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_REPLICA_ID",
        "PORT",
        "REDIS_URL",  # URL is safe, credentials are in the URL
        "DATABASE_URL",  # Same as above
        "SENTRY_DSN",
        "LOG_LEVEL",
        "CORS_ORIGINS"
    ]
    
    if key not in safe_vars:
        raise HTTPException(403, f"Access to '{key}' not allowed")
    
    value = os.getenv(key)
    
    return {
        "key": key,
        "value": value if value else None,
        "exists": value is not None
    }