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

__all__ = ["Trade", "User", "TradeNote", "Strategy"]

# Create tables
Base.metadata.create_all(bind=engine)