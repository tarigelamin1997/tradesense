"""
Configuration validation and health checks

Validates configuration at startup and provides runtime checks
to ensure the system is properly configured.
"""

import os
import re
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse
import socket
import asyncio
from pathlib import Path

import httpx
from sqlalchemy import create_engine, text
from redis import Redis

from core.config_env import get_env_config, Environment
from core.logging_config import get_logger
from core.secrets_manager import get_secret

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Configuration validation error"""
    pass


class ValidationResult:
    """Result of a validation check"""
    
    def __init__(self, name: str, passed: bool, message: str, severity: str = "error"):
        self.name = name
        self.passed = passed
        self.message = message
        self.severity = severity  # error, warning, info
    
    def __repr__(self):
        status = "✓" if self.passed else "✗"
        return f"[{status}] {self.name}: {self.message}"


class ConfigurationValidator:
    """Validates system configuration"""
    
    def __init__(self):
        self.config = get_env_config()
        self.results: List[ValidationResult] = []
    
    async def validate_all(self) -> Tuple[bool, List[ValidationResult]]:
        """Run all validation checks"""
        self.results = []
        
        # Basic validations
        self._validate_environment()
        self._validate_paths()
        self._validate_urls()
        
        # Service validations
        await self._validate_database()
        await self._validate_redis()
        await self._validate_smtp()
        
        # Security validations
        self._validate_security_settings()
        self._validate_secrets()
        
        # Feature validations
        self._validate_features()
        
        # Check if all critical validations passed
        has_errors = any(
            not r.passed and r.severity == "error" 
            for r in self.results
        )
        
        return not has_errors, self.results
    
    def _validate_environment(self):
        """Validate environment settings"""
        env = self.config.environment
        
        # Check environment is valid
        if env not in Environment:
            self.results.append(
                ValidationResult(
                    "environment",
                    False,
                    f"Invalid environment: {env}"
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "environment",
                    True,
                    f"Environment: {env.value}"
                )
            )
        
        # Production-specific checks
        if env == Environment.PRODUCTION:
            # Debug mode
            if self.config.debug:
                self.results.append(
                    ValidationResult(
                        "debug_mode",
                        False,
                        "Debug mode enabled in production!"
                    )
                )
            
            # API docs
            if self.config.docs_enabled:
                self.results.append(
                    ValidationResult(
                        "api_docs",
                        False,
                        "API documentation exposed in production!",
                        "warning"
                    )
                )
    
    def _validate_paths(self):
        """Validate required paths exist"""
        required_dirs = [
            "logs",
            "uploads",
            "temp",
            "reports"
        ]
        
        for dir_name in required_dirs:
            path = Path(dir_name)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.results.append(
                        ValidationResult(
                            f"path_{dir_name}",
                            True,
                            f"Created directory: {dir_name}"
                        )
                    )
                except Exception as e:
                    self.results.append(
                        ValidationResult(
                            f"path_{dir_name}",
                            False,
                            f"Cannot create directory {dir_name}: {e}"
                        )
                    )
            else:
                self.results.append(
                    ValidationResult(
                        f"path_{dir_name}",
                        True,
                        f"Directory exists: {dir_name}"
                    )
                )
    
    def _validate_urls(self):
        """Validate URL formats"""
        # Database URL
        if self.config.database.url:
            try:
                parsed = urlparse(self.config.database.url)
                if parsed.scheme not in ["postgresql", "postgres"]:
                    self.results.append(
                        ValidationResult(
                            "database_url",
                            False,
                            f"Invalid database scheme: {parsed.scheme}"
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            "database_url",
                            True,
                            "Database URL format valid"
                        )
                    )
            except Exception as e:
                self.results.append(
                    ValidationResult(
                        "database_url",
                        False,
                        f"Invalid database URL: {e}"
                    )
                )
        
        # Redis URL
        if self.config.redis.url:
            try:
                parsed = urlparse(self.config.redis.url)
                if parsed.scheme not in ["redis", "rediss"]:
                    self.results.append(
                        ValidationResult(
                            "redis_url",
                            False,
                            f"Invalid Redis scheme: {parsed.scheme}"
                        )
                    )
            except Exception as e:
                self.results.append(
                    ValidationResult(
                        "redis_url",
                        False,
                        f"Invalid Redis URL: {e}"
                    )
                )
    
    async def _validate_database(self):
        """Validate database connection"""
        if not self.config.database.url:
            self.results.append(
                ValidationResult(
                    "database_connection",
                    False,
                    "No database URL configured"
                )
            )
            return
        
        try:
            # Test connection
            engine = create_engine(
                self.config.database.url,
                pool_pre_ping=True,
                pool_size=1,
                max_overflow=0
            )
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                if result == 1:
                    # Check version
                    version = conn.execute(text("SELECT version()")).scalar()
                    self.results.append(
                        ValidationResult(
                            "database_connection",
                            True,
                            f"Database connected: {version.split(',')[0]}"
                        )
                    )
                    
                    # Check required extensions
                    extensions = conn.execute(
                        text("SELECT extname FROM pg_extension")
                    ).fetchall()
                    ext_names = [e[0] for e in extensions]
                    
                    required_extensions = ["uuid-ossp", "pgcrypto"]
                    for ext in required_extensions:
                        if ext not in ext_names:
                            self.results.append(
                                ValidationResult(
                                    f"postgres_extension_{ext}",
                                    False,
                                    f"Missing PostgreSQL extension: {ext}",
                                    "warning"
                                )
                            )
                else:
                    raise Exception("Database connectivity test failed")
                    
        except Exception as e:
            self.results.append(
                ValidationResult(
                    "database_connection",
                    False,
                    f"Database connection failed: {str(e)}"
                )
            )
    
    async def _validate_redis(self):
        """Validate Redis connection"""
        if not self.config.redis.url:
            self.results.append(
                ValidationResult(
                    "redis_connection",
                    False,
                    "No Redis URL configured",
                    "warning" if self.config.environment == Environment.DEVELOPMENT else "error"
                )
            )
            return
        
        try:
            # Test connection
            redis = Redis.from_url(
                self.config.redis.url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Ping Redis
            if redis.ping():
                info = redis.info()
                self.results.append(
                    ValidationResult(
                        "redis_connection",
                        True,
                        f"Redis connected: v{info.get('redis_version', 'unknown')}"
                    )
                )
                
                # Check memory usage
                used_memory = info.get('used_memory', 0)
                max_memory = info.get('maxmemory', 0)
                if max_memory > 0 and used_memory / max_memory > 0.9:
                    self.results.append(
                        ValidationResult(
                            "redis_memory",
                            False,
                            "Redis memory usage above 90%",
                            "warning"
                        )
                    )
            else:
                raise Exception("Redis ping failed")
                
        except Exception as e:
            self.results.append(
                ValidationResult(
                    "redis_connection",
                    False,
                    f"Redis connection failed: {str(e)}",
                    "warning" if self.config.environment == Environment.DEVELOPMENT else "error"
                )
            )
    
    async def _validate_smtp(self):
        """Validate SMTP configuration"""
        if not self.config.smtp_enabled:
            return
        
        if not all([self.config.smtp_host, self.config.smtp_port]):
            self.results.append(
                ValidationResult(
                    "smtp_config",
                    False,
                    "SMTP enabled but host/port not configured"
                )
            )
            return
        
        try:
            # Test SMTP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.config.smtp_host, self.config.smtp_port))
            sock.close()
            
            if result == 0:
                self.results.append(
                    ValidationResult(
                        "smtp_connection",
                        True,
                        f"SMTP server reachable at {self.config.smtp_host}:{self.config.smtp_port}"
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "smtp_connection",
                        False,
                        f"Cannot connect to SMTP server",
                        "warning"
                    )
                )
        except Exception as e:
            self.results.append(
                ValidationResult(
                    "smtp_connection",
                    False,
                    f"SMTP validation failed: {str(e)}",
                    "warning"
                )
            )
    
    def _validate_security_settings(self):
        """Validate security configuration"""
        # JWT Secret
        jwt_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
        if not jwt_secret or len(jwt_secret) < 32:
            self.results.append(
                ValidationResult(
                    "jwt_secret",
                    False,
                    "JWT secret key too short (min 32 chars)"
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "jwt_secret",
                    True,
                    "JWT secret key configured"
                )
            )
        
        # Production security
        if self.config.environment == Environment.PRODUCTION:
            # Secure cookies
            if not self.config.security.secure_cookies:
                self.results.append(
                    ValidationResult(
                        "secure_cookies",
                        False,
                        "Secure cookies disabled in production"
                    )
                )
            
            # Password policy
            if self.config.security.password_min_length < 8:
                self.results.append(
                    ValidationResult(
                        "password_policy",
                        False,
                        "Password minimum length too short for production"
                    )
                )
            
            # Rate limiting
            if not self.config.rate_limit.enabled:
                self.results.append(
                    ValidationResult(
                        "rate_limiting",
                        False,
                        "Rate limiting disabled in production",
                        "warning"
                    )
                )
    
    def _validate_secrets(self):
        """Validate secret management"""
        # Check if secrets provider is configured
        provider = os.getenv("SECRETS_PROVIDER", "env")
        
        if provider != "env" and self.config.environment == Environment.PRODUCTION:
            # Validate provider-specific settings
            if provider == "aws_secrets_manager":
                if not os.getenv("AWS_REGION"):
                    self.results.append(
                        ValidationResult(
                            "secrets_aws",
                            False,
                            "AWS region not configured for secrets manager"
                        )
                    )
            elif provider == "azure_key_vault":
                if not os.getenv("AZURE_KEY_VAULT_URL"):
                    self.results.append(
                        ValidationResult(
                            "secrets_azure",
                            False,
                            "Azure Key Vault URL not configured"
                        )
                    )
        
        # Test secret access
        try:
            test_secret = get_secret("JWT_SECRET_KEY")
            if test_secret:
                self.results.append(
                    ValidationResult(
                        "secrets_access",
                        True,
                        f"Secrets provider accessible: {provider}"
                    )
                )
        except Exception as e:
            self.results.append(
                ValidationResult(
                    "secrets_access",
                    False,
                    f"Cannot access secrets: {str(e)}",
                    "warning"
                )
            )
    
    def _validate_features(self):
        """Validate feature-specific configuration"""
        # OAuth
        if self.config.feature_flags.enable_oauth:
            oauth_providers = [
                ("GOOGLE_CLIENT_ID", "Google OAuth"),
                ("GITHUB_CLIENT_ID", "GitHub OAuth"),
                ("LINKEDIN_CLIENT_ID", "LinkedIn OAuth"),
                ("MICROSOFT_CLIENT_ID", "Microsoft OAuth")
            ]
            
            configured_count = 0
            for env_var, provider in oauth_providers:
                if os.getenv(env_var):
                    configured_count += 1
            
            if configured_count == 0:
                self.results.append(
                    ValidationResult(
                        "oauth_config",
                        False,
                        "OAuth enabled but no providers configured",
                        "warning"
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "oauth_config",
                        True,
                        f"{configured_count} OAuth provider(s) configured"
                    )
                )
        
        # MFA
        if self.config.feature_flags.enable_mfa:
            if self.config.feature_flags.enable_sms_notifications:
                if not all([
                    os.getenv("TWILIO_ACCOUNT_SID"),
                    os.getenv("TWILIO_AUTH_TOKEN"),
                    os.getenv("TWILIO_PHONE_NUMBER")
                ]):
                    self.results.append(
                        ValidationResult(
                            "mfa_sms",
                            False,
                            "SMS MFA enabled but Twilio not configured",
                            "warning"
                        )
                    )
        
        # Monitoring
        if self.config.monitoring.sentry_enabled:
            if not self.config.monitoring.sentry_dsn:
                self.results.append(
                    ValidationResult(
                        "sentry_config",
                        False,
                        "Sentry enabled but DSN not configured"
                    )
                )
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*60)
        print("CONFIGURATION VALIDATION RESULTS")
        print("="*60)
        
        for result in self.results:
            icon = "✅" if result.passed else ("⚠️" if result.severity == "warning" else "❌")
            print(f"{icon} {result.name}: {result.message}")
        
        errors = sum(1 for r in self.results if not r.passed and r.severity == "error")
        warnings = sum(1 for r in self.results if not r.passed and r.severity == "warning")
        
        print("\n" + "-"*60)
        print(f"Total: {len(self.results)} checks")
        print(f"Errors: {errors}")
        print(f"Warnings: {warnings}")
        print("="*60 + "\n")


async def validate_configuration() -> bool:
    """Run configuration validation"""
    validator = ConfigurationValidator()
    passed, results = await validator.validate_all()
    
    if not passed:
        validator.print_results()
        
        # In production, fail fast
        if get_env_config().environment == Environment.PRODUCTION:
            raise ConfigurationError("Configuration validation failed")
    
    return passed


def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary for monitoring"""
    config = get_env_config()
    
    return {
        "environment": config.environment.value,
        "debug": config.debug,
        "database": {
            "pool_size": config.database.pool_size,
            "max_overflow": config.database.max_overflow
        },
        "redis": {
            "enabled": bool(config.redis.url),
            "max_connections": config.redis.max_connections
        },
        "security": {
            "mfa_enabled": config.security.mfa_enabled,
            "secure_cookies": config.security.secure_cookies
        },
        "features": config.feature_flags.model_dump(),
        "monitoring": {
            "enabled": config.monitoring.enabled,
            "sentry": config.monitoring.sentry_enabled
        }
    }