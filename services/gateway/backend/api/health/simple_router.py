"""
Simple health check that doesn't require database
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple health check endpoint that always returns success"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tradesense-backend",
        "version": "2.0.0"
    }

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TradeSense API",
        "status": "operational",
        "docs": "/docs"
    }