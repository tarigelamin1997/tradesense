# Database module

# Database initialization
from backend.core.db.session import engine, Base

# Import models to register them - fix import paths
from backend.models.user import User
from backend.models.trade import Trade
from backend.models.trade_note import TradeNote
from backend.models.strategy import Strategy

# Analytics modules are available for import
from backend import analytics

__all__ = ["User", "Trade", "TradeNote", "Strategy", "analytics"]

# Create tables
Base.metadata.create_all(bind=engine)

# Database configuration and utilities
from .session import get_db

__all__ = ["get_db"]

# Import behavioral analytics service for dependency injection
try:
    from backend.services.behavioral_analytics import BehavioralAnalyticsService
    __all__.append("BehavioralAnalyticsService")
except ImportError:
    pass
