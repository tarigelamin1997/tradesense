"""
TradeSense Models Registry
Centralized import ensures all models are registered with SQLAlchemy before any operations.
"""

import sys
from typing import Set

# Import shared Base first
from core.db.session import Base, register_model

# Track imported models to prevent duplicates
_imported_models: Set[str] = set()

def _safe_import_model(module_name: str, model_name: str):
    """Safely import a model and register it"""
    if model_name in _imported_models:
        return
    
    try:
        module = __import__(module_name, fromlist=[model_name])
        model_class = getattr(module, model_name)
        register_model(model_class)
        _imported_models.add(model_name)
    except Exception as e:
        print(f"Warning: Could not import {model_name} from {module_name}: {e}")

# Import all models in dependency order with safe registration
# Start with association tables
from .tag import trade_tags
register_model(trade_tags)

# Import core models first
_safe_import_model('models.user', 'User')
_safe_import_model('models.trade', 'Trade')
_safe_import_model('models.portfolio', 'Portfolio')
_safe_import_model('models.trading_account', 'TradingAccount')

# Import billing models before other dependent models
_safe_import_model('models.billing', 'Subscription')
_safe_import_model('models.billing', 'Invoice')
_safe_import_model('models.billing', 'UsageRecord')

# Import dependent models
_safe_import_model('models.playbook', 'Playbook')
_safe_import_model('models.tag', 'Tag')
_safe_import_model('models.trade_review', 'TradeReview')
_safe_import_model('models.trade_note', 'TradeNote')
_safe_import_model('models.feature_request', 'FeatureRequest')
_safe_import_model('models.feature_request', 'FeatureVote')
_safe_import_model('models.feature_request', 'FeatureComment')
_safe_import_model('models.strategy', 'Strategy')
_safe_import_model('models.mental_map', 'MentalMap')
_safe_import_model('models.mental_map', 'MentalMapEntry')
_safe_import_model('models.pattern_cluster', 'PatternCluster')
_safe_import_model('models.milestone', 'Milestone')
_safe_import_model('models.daily_emotion_reflection', 'DailyEmotionReflection')

# Import the actual model classes for direct access
from .user import User
from .trade import Trade
from .portfolio import Portfolio
from .trading_account import TradingAccount
from .billing import Subscription, Invoice, UsageRecord
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
    "Subscription",
    "Invoice",
    "UsageRecord",
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
