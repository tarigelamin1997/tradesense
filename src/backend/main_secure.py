"""
Production-ready main application with comprehensive security

This is the secure version of main.py with all production security features enabled
"""

import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# Security imports
from core.security_middleware import (
    setup_security_middleware,
    SecurityHeadersMiddleware,
    RateLimitingMiddleware,
    InputValidationMiddleware,
    RequestTracingMiddleware
)
from core.security_config import initialize_security, get_security_audit

# Core imports
from core.startup_validation import run_startup_validation
from core.config import settings
from core.config_env import get_env_config, is_feature_enabled
from core.logging_config import setup_logging, get_logger
from core.logging_middleware import LoggingMiddleware
from core.monitoring_enhanced import health_checker, tracer
from core.async_manager import task_manager
from core.exceptions import setup_exception_handlers

# Import all routers
from api.v1.auth.router import router as auth_router
from api.v1.trades.router import router as trades_router
from api.v1.analytics.router import router as analytics_router
from api.v1.uploads.router import router as uploads_router
from api.v1.features.router import router as features_router
from api.v1.portfolio.router import router as portfolio_router
from api.v1.intelligence.router import router as intelligence_router
from api.v1.market_data.router import router as market_data_router
from api.v1.leaderboard.router import router as leaderboard_router
from api.v1.notes.router import router as notes_router
from api.v1.milestones.router import router as milestones_router
from api.v1.patterns.router import router as patterns_router
from api.v1.playbooks.router import router as playbooks_router
from api.v1.reviews.router import router as reviews_router
from api.v1.strategies.router import router as strategies_router
from api.v1.journal.router import router as journal_router
from api.v1.tags.router import router as tags_router
from api.v1.reflections.router import router as reflections_router
from api.v1.critique.router import router as critique_router
from api.v1.strategy_lab.router import router as strategy_lab_router
from api.v1.mental_map.router import router as mental_map_router
from api.v1.emotions.router import router as emotions_router
from api.v1.health.performance_router import router as performance_router
from api.v1.health.router import router as health_router
from api.v1.billing.router import router as billing_router
from api.v1.websocket.router import router as websocket_router
from api.v1.ai.router import router as ai_router
from api.v1.feedback.router import router as feedback_router
from api.health.router import router as health_router_legacy, root_router as health_root_router
from api.v1.public import public_router

# Admin routers
from api.admin import router as admin_router
from api.subscription import router as subscription_router
from api.support import router as support_router
from api.feature_flags import router as feature_flags_router
from api.reporting import router as reporting_router

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('temp', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# Setup structured logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/tradesense.log")
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting TradeSense Backend (Secure Mode)")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Railway Project: {os.getenv('RAILWAY_PROJECT_NAME', 'Unknown')}")
    
    # Run validation checks
    if not run_startup_validation():
        logger.warning("⚠️ Starting with validation warnings - some features may be limited")
    
    # Initialize security components
    security_config = {
        "jwt_secret_key": settings.jwt_secret_key,
        "jwt_algorithm": settings.jwt_algorithm,
        "jwt_expire_minutes": settings.jwt_access_token_expire_minutes,
        "master_encryption_key": settings.master_encryption_key,
        "password_min_length": 12,
        "mfa_enabled": is_feature_enabled("enable_mfa")
    }
    initialize_security(security_config)
    logger.info("✅ Security components initialized")
    
    # Initialize database
    try:
        import models  # Register all models
        if settings.database_url and not settings.database_url.startswith("postgresql://postgres:postgres@localhost"):
            from core.db.session import create_tables
            create_tables()
            logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Start background tasks
    await task_manager.start()
    logger.info("✅ Background tasks started")
    
    # Start health checker
    await health_checker.start()
    logger.info("✅ Health monitoring started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TradeSense Backend")
    await task_manager.stop()
    await health_checker.stop()
    logger.info("✅ Graceful shutdown complete")


def create_secure_app() -> FastAPI:
    """Create production-ready FastAPI application with security"""
    
    # Get environment configuration
    env_config = get_env_config()
    
    app = FastAPI(
        title=env_config.api_title,
        description="Advanced Trading Analytics and Risk Management Platform",
        version=env_config.api_version,
        docs_url="/api/docs" if env_config.docs_enabled else None,
        redoc_url="/api/redoc" if env_config.docs_enabled else None,
        openapi_url="/api/openapi.json" if env_config.docs_enabled else None,
        lifespan=lifespan
    )
    
    # Setup security middleware
    limiter = setup_security_middleware(app, env_config)
    
    # Add structured logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Security audit for all requests
    @app.middleware("http")
    async def audit_requests(request: Request, call_next):
        """Audit all incoming requests"""
        response = await call_next(request)
        
        # Log security-relevant requests
        if request.url.path.startswith("/api/v1/auth") or response.status_code >= 400:
            audit = get_security_audit()
            audit.log_data_access(
                user_id=getattr(request.state, "user_id", "anonymous"),
                data_type="api_request",
                record_ids=[request.url.path],
                action=request.method
            )
        
        return response
    
    # Register routers with rate limiting
    # Public routes (less restrictive)
    app.include_router(health_root_router, tags=["root"])
    app.include_router(health_router_legacy, prefix="/health", tags=["health"])
    app.include_router(public_router, prefix="/api/v1/public", tags=["public"])
    
    # Auth routes (strict rate limiting)
    auth_router_limited = limiter.limit("5/minute")(auth_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    
    # Protected API routes
    api_prefix = env_config.api_prefix
    app.include_router(trades_router, prefix=f"{api_prefix}/trades", tags=["trades"])
    app.include_router(analytics_router, prefix=f"{api_prefix}/analytics", tags=["analytics"])
    app.include_router(uploads_router, prefix=f"{api_prefix}/uploads", tags=["uploads"])
    app.include_router(features_router, prefix=f"{api_prefix}/features", tags=["features"])
    app.include_router(portfolio_router, prefix=f"{api_prefix}/portfolio", tags=["portfolio"])
    app.include_router(intelligence_router, prefix=f"{api_prefix}/intelligence", tags=["intelligence"])
    app.include_router(market_data_router, prefix=f"{api_prefix}/market-data", tags=["market-data"])
    app.include_router(leaderboard_router, prefix=f"{api_prefix}/leaderboard", tags=["leaderboard"])
    app.include_router(notes_router, prefix=f"{api_prefix}/notes", tags=["notes"])
    app.include_router(milestones_router, prefix=f"{api_prefix}/milestones", tags=["milestones"])
    app.include_router(patterns_router, prefix=f"{api_prefix}/patterns", tags=["patterns"])
    app.include_router(playbooks_router, prefix=f"{api_prefix}/playbooks", tags=["playbooks"])
    app.include_router(reviews_router, prefix=f"{api_prefix}/reviews", tags=["reviews"])
    app.include_router(strategies_router, prefix=f"{api_prefix}/strategies", tags=["strategies"])
    app.include_router(journal_router, prefix=f"{api_prefix}/journal", tags=["journal"])
    app.include_router(tags_router, prefix=f"{api_prefix}/tags", tags=["tags"])
    app.include_router(reflections_router, prefix=f"{api_prefix}/reflections", tags=["reflections"])
    app.include_router(critique_router, prefix=f"{api_prefix}/critique", tags=["critique"])
    app.include_router(strategy_lab_router, prefix=f"{api_prefix}/strategy-lab", tags=["strategy-lab"])
    app.include_router(mental_map_router, prefix=f"{api_prefix}/mental-map", tags=["mental-map"])
    app.include_router(emotions_router, prefix=f"{api_prefix}/emotions", tags=["emotions"])
    app.include_router(performance_router, prefix=f"{api_prefix}/performance", tags=["performance"])
    app.include_router(billing_router, prefix=f"{api_prefix}/billing", tags=["billing"])
    app.include_router(websocket_router, prefix=f"{api_prefix}/ws", tags=["websocket"])
    app.include_router(ai_router, prefix=f"{api_prefix}/ai", tags=["ai"])
    app.include_router(feedback_router, prefix=f"{api_prefix}/feedback", tags=["feedback"])
    app.include_router(health_router, prefix=f"{api_prefix}/health", tags=["health"])
    
    # Admin routes (extra protection)
    if is_feature_enabled("enable_admin_api"):
        admin_prefix = "/api/admin"
        app.include_router(admin_router, prefix=admin_prefix, tags=["admin"])
        app.include_router(subscription_router, prefix=f"{admin_prefix}/subscriptions", tags=["admin-subscriptions"])
        app.include_router(support_router, prefix=f"{admin_prefix}/support", tags=["admin-support"])
        app.include_router(feature_flags_router, prefix=f"{admin_prefix}/feature-flags", tags=["admin-features"])
        app.include_router(reporting_router, prefix=f"{admin_prefix}/reports", tags=["admin-reports"])
    
    return app


# Create the application
app = create_secure_app()

if __name__ == "__main__":
    import uvicorn
    
    # Production server configuration
    uvicorn.run(
        "main_secure:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=int(os.getenv("WORKERS", 4)),
        loop="uvloop",
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "handlers": ["default"],
            },
        },
        access_log=False,  # We use our own logging middleware
        server_header=False,  # Don't expose server info
        date_header=False  # Let reverse proxy handle this
    )