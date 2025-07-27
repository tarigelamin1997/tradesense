"""
Mobile API module.
Provides optimized endpoints for mobile applications.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .trades import router as trades_router
from .analytics import router as analytics_router
from .portfolio import router as portfolio_router
from .market import router as market_router
from .notifications import router as notifications_router
from .settings import router as settings_router

# Create main mobile router
mobile_router = APIRouter(prefix="/mobile/v1", tags=["Mobile API"])

# Include all sub-routers
mobile_router.include_router(auth_router, tags=["Mobile Auth"])
mobile_router.include_router(trades_router, tags=["Mobile Trades"])
mobile_router.include_router(analytics_router, tags=["Mobile Analytics"])
mobile_router.include_router(portfolio_router, tags=["Mobile Portfolio"])
mobile_router.include_router(market_router, tags=["Mobile Market"])
mobile_router.include_router(notifications_router, tags=["Mobile Notifications"])
mobile_router.include_router(settings_router, tags=["Mobile Settings"])

__all__ = ["mobile_router"]
