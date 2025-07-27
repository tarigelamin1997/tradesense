"""
Environment-specific configuration management

Provides different configurations for development, staging, and production
with validation and feature flags support.
"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
from pathlib import Path

from core.logging_config import get_logger

logger = get_logger(__name__)


class Environment(str, Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=40, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=60)
    echo: bool = False
    
    @validator('url')
    def validate_url(cls, v):
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


class RedisConfig(BaseModel):
    """Redis configuration"""
    url: Optional[str] = None
    max_connections: int = Field(default=50, ge=1, le=200)
    timeout: int = Field(default=5, ge=1, le=30)
    decode_responses: bool = True
    retry_on_timeout: bool = True


class SecurityConfig(BaseModel):
    """Security configuration"""
    jwt_expire_minutes: int = Field(default=30, ge=5, le=1440)
    password_min_length: int = Field(default=8, ge=6)
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = Field(default=5, ge=3, le=10)
    lockout_duration_minutes: int = Field(default=15, ge=5, le=60)
    mfa_enabled: bool = True
    session_timeout_minutes: int = Field(default=60, ge=10, le=480)
    csrf_protection: bool = True
    secure_cookies: bool = True


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    enabled: bool = True
    default_limit: int = Field(default=100, ge=10)
    default_window_seconds: int = Field(default=60, ge=1)
    login_limit: int = Field(default=5, ge=3, le=20)
    login_window_seconds: int = Field(default=300, ge=60)
    api_burst_limit: int = Field(default=1000, ge=100)
    api_sustained_limit: int = Field(default=100, ge=10)


class CacheConfig(BaseModel):
    """Cache configuration"""
    enabled: bool = True
    default_ttl_seconds: int = Field(default=300, ge=1)
    max_memory_mb: int = Field(default=512, ge=64)
    eviction_policy: str = Field(default="lru", pattern="^(lru|lfu|random)$")
    compression: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "json"
    include_traceback: bool = True
    log_requests: bool = True
    log_responses: bool = False
    mask_sensitive_data: bool = True
    retention_days: int = Field(default=30, ge=1, le=365)


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    enabled: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    trace_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    health_check_interval_seconds: int = Field(default=30, ge=10)
    sentry_enabled: bool = False
    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)


class FeatureFlags(BaseModel):
    """Feature flags configuration"""
    enable_oauth: bool = True
    enable_mfa: bool = True
    enable_websocket: bool = True
    enable_ai_features: bool = True
    enable_market_data: bool = True
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    enable_push_notifications: bool = False
    enable_data_export: bool = True
    enable_api_versioning: bool = True
    enable_rate_limiting: bool = True
    enable_subscription_billing: bool = False
    maintenance_mode: bool = False
    read_only_mode: bool = False


class EnvironmentConfig(BaseModel):
    """Complete environment configuration"""
    environment: Environment
    debug: bool = False
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    rate_limit: RateLimitConfig
    cache: CacheConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    feature_flags: FeatureFlags
    
    # API Configuration
    api_title: str = "TradeSense API"
    api_version: str = "2.0.0"
    api_prefix: str = "/api/v1"
    docs_enabled: bool = True
    
    # CORS Configuration
    cors_origins: List[str] = Field(default_factory=list)
    cors_allow_credentials: bool = True
    
    # File Upload Configuration
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    allowed_file_types: List[str] = Field(default_factory=lambda: [".csv", ".xlsx", ".xls"])
    
    # Email Configuration
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_from_email: Optional[str] = None
    
    # External Services
    market_data_provider: str = Field(default="alpha_vantage", pattern="^(alpha_vantage|yahoo|polygon)$")
    market_data_cache_minutes: int = Field(default=15, ge=1, le=60)


# Environment-specific configurations
DEVELOPMENT_CONFIG = EnvironmentConfig(
    environment=Environment.DEVELOPMENT,
    debug=True,
    database=DatabaseConfig(
        url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/tradesense"),
        pool_size=5,
        max_overflow=10,
        echo=True
    ),
    redis=RedisConfig(
        url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ),
    security=SecurityConfig(
        jwt_expire_minutes=1440,  # 24 hours for dev
        password_min_length=6,
        password_require_special=False,
        secure_cookies=False
    ),
    rate_limit=RateLimitConfig(
        enabled=False,  # Disabled for development
        default_limit=1000
    ),
    cache=CacheConfig(
        enabled=True,
        default_ttl_seconds=60
    ),
    logging=LoggingConfig(
        level="DEBUG",
        log_responses=True
    ),
    monitoring=MonitoringConfig(
        enabled=True,
        sentry_enabled=False,
        trace_sample_rate=1.0  # Trace everything in dev
    ),
    feature_flags=FeatureFlags(
        enable_subscription_billing=False
    ),
    cors_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app",
        "https://frontend-jj8nosjl0-tarig-ahmeds-projects.vercel.app",
        "https://frontend-*.vercel.app",
        "https://*.vercel.app",
        "https://tradesense.vercel.app",
        "https://tradesense-*.vercel.app"
    ],
    docs_enabled=True
)


STAGING_CONFIG = EnvironmentConfig(
    environment=Environment.STAGING,
    debug=False,
    database=DatabaseConfig(
        url=os.getenv("DATABASE_URL", ""),
        pool_size=10,
        max_overflow=20,
        echo=False
    ),
    redis=RedisConfig(
        url=os.getenv("REDIS_URL"),
        max_connections=30
    ),
    security=SecurityConfig(
        jwt_expire_minutes=60,
        secure_cookies=True
    ),
    rate_limit=RateLimitConfig(
        enabled=True,
        default_limit=200
    ),
    cache=CacheConfig(
        enabled=True,
        default_ttl_seconds=300
    ),
    logging=LoggingConfig(
        level="INFO",
        log_responses=False
    ),
    monitoring=MonitoringConfig(
        enabled=True,
        sentry_enabled=True,
        sentry_dsn=os.getenv("SENTRY_DSN"),
        trace_sample_rate=0.5
    ),
    feature_flags=FeatureFlags(
        enable_subscription_billing=True
    ),
    cors_origins=[
        "https://staging.tradesense.io",
        "https://staging-app.tradesense.io"
    ],
    docs_enabled=True
)


PRODUCTION_CONFIG = EnvironmentConfig(
    environment=Environment.PRODUCTION,
    debug=False,
    database=DatabaseConfig(
        url=os.getenv("DATABASE_URL", ""),
        pool_size=20,
        max_overflow=40,
        echo=False,
        pool_recycle=1800  # 30 minutes
    ),
    redis=RedisConfig(
        url=os.getenv("REDIS_URL"),
        max_connections=50,
        timeout=3
    ),
    security=SecurityConfig(
        jwt_expire_minutes=30,
        secure_cookies=True,
        max_login_attempts=3,
        lockout_duration_minutes=30
    ),
    rate_limit=RateLimitConfig(
        enabled=True,
        default_limit=100,
        login_limit=3,
        login_window_seconds=600
    ),
    cache=CacheConfig(
        enabled=True,
        default_ttl_seconds=300,
        compression=True
    ),
    logging=LoggingConfig(
        level="WARNING",
        log_responses=False,
        retention_days=90
    ),
    monitoring=MonitoringConfig(
        enabled=True,
        sentry_enabled=True,
        sentry_dsn=os.getenv("SENTRY_DSN"),
        trace_sample_rate=0.1
    ),
    feature_flags=FeatureFlags(
        enable_subscription_billing=True,
        enable_sms_notifications=True
    ),
    cors_origins=[
        "https://tradesense.io",
        "https://www.tradesense.io",
        "https://app.tradesense.io"
    ],
    docs_enabled=False  # Disable in production
)


TESTING_CONFIG = EnvironmentConfig(
    environment=Environment.TESTING,
    debug=True,
    database=DatabaseConfig(
        url="postgresql://postgres:postgres@localhost/tradesense_test",
        pool_size=1,
        max_overflow=0
    ),
    redis=RedisConfig(
        url=None  # Use FakeRedis
    ),
    security=SecurityConfig(
        jwt_expire_minutes=5,
        password_min_length=6,  # Fixed to meet minimum requirement
        password_require_uppercase=False,
        password_require_lowercase=False,
        password_require_numbers=False,
        password_require_special=False
    ),
    rate_limit=RateLimitConfig(
        enabled=False
    ),
    cache=CacheConfig(
        enabled=False
    ),
    logging=LoggingConfig(
        level="DEBUG"
    ),
    monitoring=MonitoringConfig(
        enabled=False
    ),
    feature_flags=FeatureFlags(),
    cors_origins=["http://testserver"],
    docs_enabled=False
)


class ConfigurationManager:
    """Manages environment-specific configurations"""
    
    def __init__(self):
        self.env = os.getenv("ENVIRONMENT", "development").lower()
        self.config = self._load_config()
        self._validate_config()
        logger.info(f"Configuration loaded for environment: {self.env}")
    
    def _load_config(self) -> EnvironmentConfig:
        """Load configuration for current environment"""
        configs = {
            "development": DEVELOPMENT_CONFIG,
            "staging": STAGING_CONFIG,
            "production": PRODUCTION_CONFIG,
            "testing": TESTING_CONFIG
        }
        
        base_config = configs.get(self.env, DEVELOPMENT_CONFIG)
        
        # Override with environment variables
        return self._override_with_env(base_config)
    
    def _override_with_env(self, config: EnvironmentConfig) -> EnvironmentConfig:
        """Override configuration with environment variables"""
        # Database URL
        if db_url := os.getenv("DATABASE_URL"):
            config.database.url = db_url
        
        # Redis URL
        if redis_url := os.getenv("REDIS_URL"):
            config.redis.url = redis_url
        
        # Sentry DSN
        if sentry_dsn := os.getenv("SENTRY_DSN"):
            config.monitoring.sentry_dsn = sentry_dsn
            config.monitoring.sentry_enabled = True
        
        # CORS Origins
        if cors_origins := os.getenv("CORS_ORIGINS"):
            # Clean up any formatting issues (semicolons, newlines, etc.)
            cors_origins = cors_origins.replace(";", ",").replace("\n", "").replace("\\n", "")
            config.cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
        
        # Feature flags from environment
        for flag_name in config.feature_flags.model_fields:
            env_var = f"FEATURE_{flag_name.upper()}"
            if value := os.getenv(env_var):
                setattr(config.feature_flags, flag_name, value.lower() == "true")
        
        return config
    
    def _validate_config(self):
        """Validate configuration for current environment"""
        if self.env == "production":
            # Ensure critical settings in production
            if not self.config.database.url:
                raise ValueError("DATABASE_URL must be set in production")
            
            if not self.config.security.secure_cookies:
                raise ValueError("Secure cookies must be enabled in production")
            
            if self.config.debug:
                raise ValueError("Debug mode must be disabled in production")
            
            if self.config.docs_enabled:
                logger.warning("API documentation is enabled in production")
    
    def get_config(self) -> EnvironmentConfig:
        """Get current configuration"""
        return self.config
    
    def get_feature_flag(self, flag_name: str) -> bool:
        """Get specific feature flag value"""
        return getattr(self.config.feature_flags, flag_name, False)
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.config.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.config.environment == Environment.DEVELOPMENT
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        config_dict = self.config.model_dump()
        
        if not include_secrets:
            # Remove sensitive values
            if 'database' in config_dict:
                config_dict['database']['url'] = '***'
            if 'redis' in config_dict:
                config_dict['redis']['url'] = '***'
            if 'monitoring' in config_dict:
                config_dict['monitoring']['sentry_dsn'] = '***'
        
        return config_dict


# Global configuration instance
config_manager = ConfigurationManager()
env_config = config_manager.get_config()


# Convenience functions
def get_env_config() -> EnvironmentConfig:
    """Get current environment configuration"""
    return env_config


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled"""
    return config_manager.get_feature_flag(feature)


def get_database_url() -> str:
    """Get database URL for current environment"""
    return env_config.database.url


def get_redis_url() -> Optional[str]:
    """Get Redis URL for current environment"""
    return env_config.redis.url