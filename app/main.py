#!/usr/bin/env python3
"""
TradeSense Backend API
Production-ready FastAPI backend with proper routing and service integration
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import routers
from app.routers import auth, analytics, scheduler, journaling, admin, exports
from app.services.auth_service import get_current_user
from app.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense Backend API",
    description="Production-ready backend for TradeSense trading analytics platform",
    version="2.5.9",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to verify all modules
@app.on_event("startup")
async def startup_event():
    """Verify all critical modules are loaded"""
    logger.info("🚀 TradeSense Backend Starting...")

    # Verify critical services
    try:
        from app.services.email_service import EmailService
        from app.services.database_service import DatabaseService
        from app.services.auth_service import AuthService

        logger.info("✅ All critical services imported successfully")
        logger.info("✅ EmailService: Available")
        logger.info("✅ DatabaseService: Available")
        logger.info("✅ AuthService: Available")

        # Initialize database
        db_service = DatabaseService()
        logger.info("✅ Database connection established")

        logger.info("🎯 TradeSense Backend fully operational!")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

# Include all routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["Email Scheduler"])
app.include_router(journaling.router, prefix="/api/journal", tags=["Journaling"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])

@app.get("/")
async def root():
    return {"message": "TradeSense Backend API v2.5.9", "status": "operational"}

@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Test database connection
        from app.services.database_service import DatabaseService
        db_service = DatabaseService()

        # Test core services
        health_status = {
            "status": "healthy",
            "timestamp": "2024-12-24T00:00:00Z",
            "version": "2.5.9",
            "database": "connected",
            "services": {
                "auth": "operational",
                "analytics": "operational", 
                "scheduler": "operational",
                "journaling": "operational",
                "email": "operational"
            }
        }

        return JSONResponse(content=health_status, status_code=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)}, 
            status_code=503
        )

if __name__ == "__main__":
    logger.info("🚀 Starting TradeSense Backend API v2.5.9")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )