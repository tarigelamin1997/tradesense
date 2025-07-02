"""
TradeSense Models Registry
Centralized import ensures all models are registered with SQLAlchemy before any operations.
"""

# Import shared Base first
from backend.core.db.session import Base

# Import all models in dependency order
from .tag import trade_tags
from .user import User
from .trade import Trade
from .portfolio import Portfolio
from .trading_account import TradingAccount
from .playbook import Playbook
from .tag import Tag
from .trade_review import TradeReview
from .trade_note import TradeNote
from .feature_request import FeatureRequest, FeatureVote, FeatureComment
from .strategy import Strategy
from .mental_map import MentalMap, MentalMapEntry
from .pattern_cluster import PatternCluster
from .milestone import Milestone
from .daily_emotion_reflection import DailyEmotionReflection

# Export all models
__all__ = [
    "Base",
    "User",
    "Trade", 
    "Portfolio",
    "TradingAccount",
    "Playbook",
    "Tag",
    "TradeReview",
    "TradeNote",
    "FeatureRequest",
    "FeatureVote", 
    "FeatureComment",
    "Strategy",
    "MentalMap",
    "MentalMapEntry",
    "PatternCluster",
    "Milestone",
    "DailyEmotionReflection"
]
