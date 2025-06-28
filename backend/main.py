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

    # Initialize database
    from backend.initialize_db import *

    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Import routers
try:
    from backend.api.v1.auth.router import router as auth_router
    print("✅ Auth router imported successfully")
except ImportError as e:
    print(f"❌ Failed to import auth router: {e}")
    # Create a simple fallback router
    from fastapi import APIRouter
    auth_router = APIRouter()
    
    @auth_router.get("/auth/status")
    async def auth_status():
        return {"status": "Auth service temporarily unavailable", "fallback": True}
from backend.api.v1.trades.router import router as trades_router
from backend.api.v1.analytics.router import router as analytics_router
from backend.api.v1.uploads.router import router as uploads_router
from backend.api.v1.features.router import router as features_router
from backend.api.v1.portfolio.router import router as portfolio_router
from backend.api.v1.intelligence.router import router as intelligence_router
from backend.api.v1.market_data.router import router as market_data_router
from backend.api.health.router import router as health_router
from backend.core.middleware import setup_middleware
from backend.core.exceptions import setup_exception_handlers
import logging

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

    # Include routers
    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(trades_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(uploads_router, prefix="/api/v1")
    app.include_router(features_router, prefix="/api/v1/features", tags=["features"])
    app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
    app.include_router(market_data_router, prefix="/api/v1/market-data", tags=["market-data"])
    app.include_router(portfolio_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        # Redirect to frontend UI if accessed via browser
        from fastapi.responses import RedirectResponse
        from fastapi import Request
        
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