"""
API v1 module initialization
"""
from fastapi import APIRouter
from .users.router import router as users_router
from .trades import router as trades_router
from .notes.router import router as notes_router
from .strategies.router import router as strategies_router
from .tags.router import router as tags_router
from .emotions.router import router as emotions_router
from .portfolio.router import router as portfolio_router
from .auth.router import router as auth_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include all routers
api_v1_router.include_router(users_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(trades_router)
api_v1_router.include_router(notes_router)
api_v1_router.include_router(strategies_router)
api_v1_router.include_router(tags_router)
api_v1_router.include_router(emotions_router)
api_v1_router.include_router(portfolio_router)