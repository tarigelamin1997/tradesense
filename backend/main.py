import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize database first
try:
    print("🚀 Starting TradeSense Backend...")
    
    # Import all models first to register them with SQLAlchemy
    import models  # This ensures all models are registered
    
    # Initialize database
    from initialize_db import *

    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Import routers
from backend.api.v1.auth.router import router as auth_router
from backend.api.v1.trades.router import router as trades_router
from backend.api.v1.analytics.router import router as analytics_router
from backend.api.v1.uploads.router import router as uploads_router
from backend.api.v1.features.router import router as features_router
from backend.api.v1.portfolio.router import router as portfolio_router
from backend.api.v1.intelligence.router import router as intelligence_router
from backend.api.v1.market_data.router import router as market_data_router
from backend.api.v1.leaderboard.router import router as leaderboard_router
from backend.api.v1.notes.router import router as notes_router
from backend.api.v1.milestones.router import router as milestones_router
from backend.api.v1.patterns.router import router as patterns_router
from backend.api.v1.playbooks.router import router as playbooks_router
from backend.api.v1.reviews.router import router as reviews_router
from backend.api.v1.strategies.router import router as strategies_router
from backend.api.v1.journal.router import router as journal_router
from backend.api.v1.tags.router import router as tags_router
from backend.api.v1.reflections.router import router as reflections_router
from backend.api.v1.critique.router import router as critique_router
from backend.api.v1.strategy_lab.router import router as strategy_lab_router
from backend.api.v1.mental_map.router import router as mental_map_router
from backend.api.v1.emotions.router import router as emotions_router
from backend.api.v1.health.performance_router import router as performance_router
from backend.api.v1.health.router import router as health_router
from backend.api.health.router import router as health_router_legacy, root_router as health_root_router
from backend.core.middleware import setup_middleware
from backend.core.exceptions import setup_exception_handlers
from backend.core.validation_middleware import setup_validation_middleware
from backend.core.async_manager import task_manager
import logging
from backend.api.v1.public import public_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/tradesense.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="TradeSense API",
        description="Advanced Trading Analytics and Risk Management Platform",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup middleware and exception handlers
    setup_middleware(app)
    setup_exception_handlers(app)
    setup_validation_middleware(app)

    # Start the async cleanup task on FastAPI startup (optional for faster startup)
    @app.on_event("startup")
    async def start_async_manager_cleanup():
        # Only start cleanup task in production or when explicitly enabled
        if os.getenv("ENABLE_TASK_CLEANUP", "false").lower() == "true":
            task_manager.start_cleanup_task()
            print("🔄 Background task cleanup enabled")
        else:
            print("⚡ Fast startup mode - task cleanup disabled")

    # Include routers with correct prefixes
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.include_router(trades_router, prefix="/api/v1/trades")
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(uploads_router, prefix="/api/v1")
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
    app.include_router(strategy_lab_router, prefix="/api/v1/strategy-lab")
    app.include_router(mental_map_router, prefix="/api/v1/mental-map")
    app.include_router(emotions_router, prefix="/api/v1/emotions")
    app.include_router(performance_router, prefix="/api/v1/performance", tags=["performance"])
    app.include_router(health_router, tags=["health"])
    
    # Legacy health router for backward compatibility
    app.include_router(health_router_legacy, prefix="/api")
    app.include_router(health_root_router)  # root-level health endpoints for test compatibility

    @app.get("/", include_in_schema=False)
    async def redirect_to_frontend():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://0.0.0.0:3000")

    @app.get("/api", include_in_schema=False)  
    async def api_root():
        return {
            "message": "TradeSense API v2.0 - Advanced Trade Intelligence",
            "status": "operational",
            "frontend_url": "Port 3000 for React UI",
            "features": [
                "Trade Analytics", "Portfolio Simulation", "Feature Voting",
                "AI Trade Intelligence", "Market Regime Analysis", "Risk Assessment"
            ]
        }

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TradeSense API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )