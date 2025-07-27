"""
Production startup script with configuration validation

Ensures the system is properly configured before starting
"""

import sys
import os
import asyncio
from typing import List, Tuple

from core.config_env import get_env_config, Environment
from core.config_validator import validate_configuration, ConfigurationValidator
from core.logging_config import setup_logging, get_logger
from core.db.session import create_tables
from core.monitoring_enhanced import health_checker


async def run_startup_checks() -> Tuple[bool, List[str]]:
    """Run all startup checks"""
    errors = []
    warnings = []
    
    logger = get_logger(__name__)
    config = get_env_config()
    
    logger.info(f"Starting TradeSense Backend v{config.api_version}")
    logger.info(f"Environment: {config.environment.value}")
    
    # 1. Validate configuration
    logger.info("Validating configuration...")
    try:
        validator = ConfigurationValidator()
        passed, results = await validator.validate_all()
        
        for result in results:
            if not result.passed:
                if result.severity == "error":
                    errors.append(f"[CONFIG] {result.name}: {result.message}")
                else:
                    warnings.append(f"[CONFIG] {result.name}: {result.message}")
        
        if not passed and config.environment == Environment.PRODUCTION:
            logger.error("Configuration validation failed in production")
            return False, errors
            
    except Exception as e:
        errors.append(f"[CONFIG] Validation error: {str(e)}")
        logger.exception("Configuration validation failed")
        return False, errors
    
    # 2. Initialize database
    if config.database.url:
        logger.info("Initializing database...")
        try:
            create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            error_msg = f"[DATABASE] Initialization failed: {str(e)}"
            if config.environment == Environment.PRODUCTION:
                errors.append(error_msg)
            else:
                warnings.append(error_msg)
            logger.exception("Database initialization failed")
    else:
        errors.append("[DATABASE] No database URL configured")
    
    # 3. Run health checks
    logger.info("Running health checks...")
    try:
        health_results = await health_checker.run_checks()
        
        for check_name, check_result in health_results['checks'].items():
            if check_result['status'] == 'unhealthy':
                if check_result['critical']:
                    errors.append(f"[HEALTH] {check_name}: {check_result['message']}")
                else:
                    warnings.append(f"[HEALTH] {check_name}: {check_result['message']}")
        
    except Exception as e:
        warnings.append(f"[HEALTH] Health check error: {str(e)}")
        logger.exception("Health check failed")
    
    # 4. Validate feature flags
    logger.info("Validating feature flags...")
    try:
        from core.feature_flags import feature_flags
        flag_count = len(feature_flags.list_flags())
        logger.info(f"Loaded {flag_count} feature flags")
    except Exception as e:
        warnings.append(f"[FEATURES] Feature flag error: {str(e)}")
        logger.exception("Feature flag initialization failed")
    
    # 5. Check external services
    if config.monitoring.sentry_enabled:
        if not config.monitoring.sentry_dsn:
            warnings.append("[MONITORING] Sentry enabled but DSN not configured")
    
    # 6. Security checks
    if config.environment == Environment.PRODUCTION:
        # Check JWT secret
        jwt_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
        if not jwt_secret or jwt_secret == "changeme":
            errors.append("[SECURITY] JWT secret not properly configured")
        
        # Check CORS
        if "*" in config.cors_origins:
            warnings.append("[SECURITY] CORS allows all origins (*)")
    
    # Print results
    print("\n" + "="*60)
    print("STARTUP CHECK RESULTS")
    print("="*60)
    
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print("\n✅ All checks passed!")
    
    print("="*60 + "\n")
    
    # Return results
    success = len(errors) == 0
    all_messages = errors + warnings
    
    return success, all_messages


def main():
    """Main startup function"""
    # Setup logging first
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/tradesense.log")
    )
    
    logger = get_logger(__name__)
    
    try:
        # Run async startup checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success, messages = loop.run_until_complete(run_startup_checks())
        
        if not success:
            logger.error("Startup checks failed")
            if get_env_config().environment == Environment.PRODUCTION:
                logger.error("Refusing to start in production with errors")
                sys.exit(1)
            else:
                logger.warning("Starting with errors in non-production environment")
        
        # Start the application
        logger.info("Starting FastAPI application...")
        
        # Import and run the app
        import uvicorn
        from main import app
        
        port = int(os.getenv("PORT", 8000))
        is_production = get_env_config().environment == Environment.PRODUCTION
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=not is_production,
            log_level="info",
            access_log=not is_production
        )
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.exception(f"Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()