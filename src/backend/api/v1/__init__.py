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
api_v1_router.include_router(users_router, prefix="/users", tags=["users"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(trades_router, prefix="/trades", tags=["trades"])
api_v1_router.include_router(notes_router, prefix="/notes", tags=["notes"])
api_v1_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
api_v1_router.include_router(tags_router, prefix="/tags", tags=["tags"])
api_v1_router.include_router(emotions_router, prefix="/emotions", tags=["emotions"])
api_v1_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])