"""
Enhanced main.py with comprehensive monitoring and observability

This version includes structured logging, metrics collection, error tracking,
and performance monitoring integrated into the FastAPI application.
"""

import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize logging first
from core.logging_config import setup_logging, get_logger, log_business_event
from core.logging_middleware import LoggingMiddleware, LoggingRoute
from core.metrics import metrics_collector
from core.error_tracking import error_tracker, track_errors
from core.performance_optimizer import compression_middleware

# Setup structured logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/tradesense.log")
)

logger = get_logger(__name__)

# Log startup
logger.info("🚀 Starting TradeSense Backend with monitoring enabled", extra={
    "event": "startup",
    "version": "2.0.0",
    "environment": os.getenv("ENVIRONMENT", "development")
})

# Initialize database
try:
    logger.info("Initializing database...")
    
    # Import all models first to register them with SQLAlchemy
    import models  # This ensures all models are registered
    
    # Initialize database
    from initialize_db import *

    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization warning: {e}", exc_info=True)
    error_tracker.capture_exception(e, {"phase": "database_init"})

# Import routers
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
from api.v1.monitoring.router import router as monitoring_router
from api.health.router import router as health_router_legacy, root_router as health_root_router
from core.middleware import setup_middleware
from core.exceptions import setup_exception_handlers
from core.validation_middleware import setup_validation_middleware
from core.async_manager import task_manager
from core.security_headers import security_headers_middleware
from api.v1.public import public_router

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('temp', exist_ok=True)

def create_app() -> FastAPI:
    """Create and configure FastAPI application with monitoring"""

    app = FastAPI(
        title="TradeSense API",
        description="Advanced Trading Analytics and Risk Management Platform",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        # Use custom route class for request ID tracking
        route_class=LoggingRoute
    )

    # Setup CORS
    from core.config import settings
    cors_origins = [origin.strip() for origin in settings.cors_origins_str.split(",")]
    if os.getenv("ENVIRONMENT", "development") != "production":
        cors_origins.extend([
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:5173",
            "http://0.0.0.0:3000",
            "http://0.0.0.0:3001",
        ])
        cors_origins = list(set(cors_origins))
    
    logger.info(f"CORS Origins configured: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add monitoring middleware
    app.add_middleware(LoggingMiddleware)
    app.middleware("http")(compression_middleware)
    
    # Setup other middleware and exception handlers
    setup_middleware(app)
    setup_exception_handlers(app)
    setup_validation_middleware(app)
    
    # Add security headers middleware
    app.middleware("http")(security_headers_middleware)
    
    # Custom exception handler with error tracking
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_id = error_tracker.capture_exception(exc, {
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None
        })
        
        logger.error(f"Unhandled exception: {exc}", extra={
            "error_id": error_id,
            "request_path": request.url.path
        })
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_id": error_id,
                "message": "An unexpected error occurred. Please try again later."
            }
        )
    
    # Startup event handlers
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        logger.info("Starting up TradeSense services...")
        
        # Start background task cleanup if enabled
        if os.getenv("ENABLE_TASK_CLEANUP", "false").lower() == "true":
            task_manager.start_cleanup_task()
            logger.info("🔄 Background task cleanup enabled")
        else:
            logger.info("⚡ Fast startup mode - task cleanup disabled")
        
        # Initialize error tracking
        if os.getenv("SENTRY_DSN"):
            logger.info("📊 Sentry error tracking enabled")
        
        # Start metrics collection
        try:
            metrics_collector.collect_system_metrics()
            logger.info("📈 Metrics collection started")
        except Exception as e:
            logger.warning(f"Failed to start metrics collection: {e}")
        
        # Log startup complete
        log_business_event("application_started", "system", {
            "version": "2.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        })
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("Shutting down TradeSense services...")
        
        # Log shutdown
        log_business_event("application_shutdown", "system", {
            "version": "2.0.0"
        })
    
    # Include routers with correct prefixes
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.include_router(trades_router, prefix="/api/v1/trades")
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(uploads_router, prefix="/api/v1/uploads")
    app.include_router(features_router, prefix="/api/v1/features", tags=["features"])
    app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
    app.include_router(market_data_router, prefix="/api/v1/market-data", tags=["market-data"])
    app.include_router(portfolio_router, prefix="/api/v1/portfolio")
    app.include_router(leaderboard_router, prefix="/api/v1/leaderboard")
    app.include_router(notes_router, prefix="/api/v1/notes")
    app.include_router(milestones_router, prefix="/api/v1/milestones")
    app.include_router(patterns_router, prefix="/api/v1/patterns")
    app.include_router(playbooks_router, prefix="/api/v1/playbooks")
    app.include_router(reviews_router, prefix="/api/v1/reviews")
    app.include_router(strategies_router, prefix="/api/v1/strategies")
    app.include_router(journal_router, prefix="/api/v1/journal")
    app.include_router(tags_router, prefix="/api/v1/tags")
    app.include_router(reflections_router, prefix="/api/v1/reflections")
    app.include_router(critique_router, prefix="/api/v1/critique")
    app.include_router(strategy_lab_router, prefix="/api/v1/strategy-lab", tags=["strategy-lab"])
    app.include_router(mental_map_router, prefix="/api/v1/mental-map", tags=["mental-map"])
    app.include_router(emotions_router, prefix="/api/v1/emotions")
    app.include_router(performance_router, prefix="/api/v1/performance")
    app.include_router(health_router, prefix="/api/v1/health")
    app.include_router(billing_router, prefix="/api/v1/billing", tags=["billing"])
    app.include_router(websocket_router, prefix="/api/v1/ws", tags=["websocket"])
    app.include_router(monitoring_router, prefix="/api/v1/monitoring")
    
    # Include legacy health endpoints at root
    app.include_router(health_router_legacy, prefix="/api/health")
    app.include_router(health_root_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to TradeSense API",
            "version": "2.0.0",
            "docs": "/api/docs",
            "health": "/api/v1/monitoring/health"
        }
    
    return app

# Create application instance
app = create_app()

# Export for uvicorn
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "main_monitoring:app",
        host=host,
        port=port,
        reload=reload,
        log_config=None  # Use our custom logging
    )