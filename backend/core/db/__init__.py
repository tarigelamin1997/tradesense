# Database module

# Database initialization
from backend.core.db.session import engine, Base

# Import models to register them
"""
Database module for TradeSense
"""
from backend.models.trade import Trade
from backend.models.user import User
from backend.models.trade_note import TradeNote
from backend.models.strategy import Strategy
from backend.models.tag import Tag

__all__ = ["Trade", "User", "TradeNote", "Strategy", "Tag"]

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