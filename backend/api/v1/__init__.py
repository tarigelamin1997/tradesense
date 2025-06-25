"""
API v1 module initialization
"""
from fastapi import APIRouter

from backend.api.v1.auth.router import router as auth_router
from backend.api.v1.trades.router import router as trades_router
from backend.api.v1.uploads.router import router as uploads_router
from backend.api.v1.users.router import router as users_router

# Create v1 API router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all module routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(trades_router)
api_v1_router.include_router(uploads_router)
api_v1_router.include_router(users_router)