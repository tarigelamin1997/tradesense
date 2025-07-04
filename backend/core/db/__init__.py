# Database module

# Database initialization
from backend.core.db.session import engine, Base

# Analytics modules are available for import
try:
    from backend import analytics
    __all__ = ["analytics"]
except ImportError:
    __all__ = []

# Database configuration and utilities
from .session import get_db

__all__ = ["get_db"]

# Import behavioral analytics service for dependency injection
try:
    from backend.services.behavioral_analytics import BehavioralAnalyticsService
    __all__.append("BehavioralAnalyticsService")
except ImportError:
    pass
