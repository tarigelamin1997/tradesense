"""
Analytics package for TradeSense.
Provides user behavior tracking and product analytics.
"""

from .user_analytics import (
    user_analytics,
    UserAnalytics,
    UserEvent,
    EventType,
    AnalyticsMiddleware
)
from .product_analytics import (
    product_analytics,
    ProductAnalytics,
    track_trade_analytics,
    track_feature_usage,
    track_subscription_event,
    track_support_event
)

__all__ = [
    "user_analytics",
    "UserAnalytics",
    "UserEvent",
    "EventType",
    "AnalyticsMiddleware",
    "product_analytics",
    "ProductAnalytics",
    "track_trade_analytics",
    "track_feature_usage",
    "track_subscription_event",
    "track_support_event"
]