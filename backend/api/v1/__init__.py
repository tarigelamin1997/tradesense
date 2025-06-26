"""
API v1 module initialization
"""
from fastapi import APIRouter

from backend.api.v1.users.router import router as users_router
from backend.api.v1.trades.router import router as trades_router
from backend.api.v1.notes.router import router as notes_router
from backend.api.v1.strategies.router import router as strategies_router
from backend.api.v1.tags.router import router as tags_router
from backend.api.v1.emotions.router import router as emotions_router
from backend.api.v1.portfolio.router import router as portfolio_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include all routers
api_v1_router.include_router(users_router)
api_v1_router.include_router(trades_router)
api_v1_router.include_router(notes_router)
api_v1_router.include_router(strategies_router)
api_v1_router.include_router(tags_router)
api_v1_router.include_router(emotions_router)
api_v1_router.include_router(portfolio_router)