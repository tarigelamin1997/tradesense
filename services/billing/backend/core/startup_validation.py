"""
Startup validation to ensure all required dependencies and environment variables are present
"""
import os
import sys
import importlib
import time
import asyncio
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates the application can start successfully"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validation checks"""
        self._validate_environment_variables()
        self._validate_imports()
        self._validate_database_url()
        self._validate_directories()
        
        # Test database connection if in production
        if os.getenv("ENVIRONMENT") == "production":
            self._test_database_connection()
        
        is_valid = len(self.errors) == 0
        
        return is_valid, {
            "valid": is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks_performed": [
                "environment_variables",
                "module_imports", 
                "database_config",
                "directory_structure",
                "database_connection" if os.getenv("ENVIRONMENT") == "production" else None
            ]
        }
    
    def _validate_environment_variables(self):
        """Check required environment variables"""
        required_vars = {
            "DATABASE_URL": "PostgreSQL connection string",
            "SECRET_KEY": "Application secret key",
            "JWT_SECRET_KEY": "JWT signing key",
        }
        
        optional_vars = {
            "STRIPE_SECRET_KEY": "Stripe API key (required for billing)",
            "STRIPE_PRICE_ID_STARTER": "Stripe price ID for starter plan",
            "STRIPE_PRICE_ID_PRO": "Stripe price ID for pro plan",
            "REDIS_URL": "Redis connection (optional for caching)",
            "SMTP_HOST": "Email server (optional)",
            "OPENAI_API_KEY": "OpenAI API key (optional for AI features)"
        }
        
        # Check required
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required env var: {var} ({description})")
            elif var == "DATABASE_URL" and value.startswith("postgresql://postgres:postgres@localhost"):
                self.warnings.append(f"{var} is using default localhost value")
                
        # Check optional
        for var, description in optional_vars.items():
            if not os.getenv(var):
                self.warnings.append(f"Missing optional env var: {var} ({description})")
                
    def _validate_imports(self):
        """Validate all critical imports work"""
        critical_imports = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "jose",
            "passlib",
            "redis",
            "stripe",
            "httpx",
            "pandas",
            "numpy",
            "sklearn"
        ]
        
        for module_name in critical_imports:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                self.errors.append(f"Failed to import {module_name}: {str(e)}")
                
    def _validate_database_url(self):
        """Validate database URL format"""
        db_url = os.getenv("DATABASE_URL", "")
        
        if db_url:
            if not db_url.startswith(("postgresql://", "postgres://")):
                self.errors.append("DATABASE_URL must be a PostgreSQL connection string")
            
            # Check for Railway internal URL
            if "railway.internal" in db_url:
                self.warnings.append("Using Railway internal database URL - ensure service is deployed in same project")
                
    def _validate_directories(self):
        """Ensure required directories exist"""
        required_dirs = ["logs", "uploads", "temp", "reports"]
        
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name, exist_ok=True)
                except Exception as e:
                    self.errors.append(f"Failed to create directory {dir_name}: {str(e)}")


    def _test_database_connection(self) -> bool:
        """Test database connection with retry logic"""
        from core.config import get_database_url
        
        db_url = get_database_url()
        if not db_url:
            self.errors.append("No database URL configured")
            return False
            
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Testing database connection (attempt {attempt + 1}/{max_retries})...")
                engine = create_engine(db_url, pool_pre_ping=True)
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                    
                logger.info("✅ Database connection successful")
                return True
                
            except OperationalError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection failed (attempt {attempt + 1}): {str(e)}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.errors.append(f"Database connection failed after {max_retries} attempts: {str(e)}")
                    return False
            except Exception as e:
                self.errors.append(f"Unexpected database error: {str(e)}")
                return False
                
        return False


# Singleton instance
startup_validator = StartupValidator()


def run_startup_validation():
    """Run validation and print results"""
    print("🔍 Running startup validation...")
    
    is_valid, results = startup_validator.validate_all()
    
    if results["errors"]:
        print("\n❌ ERRORS (must fix):")
        for error in results["errors"]:
            print(f"  - {error}")
            
    if results["warnings"]:
        print("\n⚠️  WARNINGS (should address):")
        for warning in results["warnings"]:
            print(f"  - {warning}")
            
    if is_valid:
        print("\n✅ Startup validation passed!")
    else:
        print("\n❌ Startup validation failed!")
        print("Fix the errors above before deployment.")
        
    return is_valid


async def wait_for_database(max_wait_time: int = 60) -> bool:
    """Wait for database to be ready with exponential backoff"""
    from core.config import get_database_url
    
    db_url = get_database_url()
    if not db_url:
        logger.error("No database URL configured")
        return False
        
    start_time = time.time()
    retry_delay = 1
    attempt = 0
    
    while time.time() - start_time < max_wait_time:
        attempt += 1
        try:
            logger.info(f"Checking database availability (attempt {attempt})...")
            engine = create_engine(db_url, pool_pre_ping=True)
            
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            logger.info("✅ Database is ready!")
            return True
            
        except OperationalError as e:
            elapsed = int(time.time() - start_time)
            remaining = max_wait_time - elapsed
            
            if remaining > 0:
                logger.warning(f"Database not ready yet ({elapsed}s elapsed, {remaining}s remaining)")
                await asyncio.sleep(min(retry_delay, remaining))
                retry_delay = min(retry_delay * 2, 10)  # Cap at 10 seconds
            else:
                logger.error(f"Database did not become ready within {max_wait_time} seconds")
                return False
        except Exception as e:
            logger.error(f"Unexpected error waiting for database: {str(e)}")
            return False
            
    return False