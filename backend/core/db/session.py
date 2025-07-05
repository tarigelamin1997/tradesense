"""
Database session management and model registry
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, registry
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
import logging

logger = logging.getLogger(__name__)

# Create a completely isolated registry
mapper_registry = registry()
Base = mapper_registry.generate_base()

# Global flag to prevent multiple registrations
_models_registered = False

def register_model(model_class):
    """Safely register a model class to prevent duplicates"""
    global _models_registered
    if _models_registered:
        return False
    
    # Handle both Table objects and model classes
    if hasattr(model_class, '__name__'):
        name = model_class.__name__
    elif hasattr(model_class, 'name'):
        name = model_class.name
    else:
        name = str(model_class)
    
    return True

def get_registered_models():
    """Get list of registered model names"""
    if hasattr(mapper_registry, 'metadata'):
        return list(mapper_registry.metadata.tables.keys())
    return []

def ensure_models_registered():
    """Ensure all models are registered only once"""
    global _models_registered
    if not _models_registered:
        # Import all models here to ensure they're registered
        try:
            # Import all model modules to register them
            from backend.models.user import User
            from backend.models.trade import Trade
            from backend.models.portfolio import Portfolio
            from backend.models.trading_account import TradingAccount
            from backend.models.playbook import Playbook
            from backend.models.tag import Tag, trade_tags
            from backend.models.trade_review import TradeReview
            from backend.models.trade_note import TradeNote
            from backend.models.feature_request import FeatureRequest, FeatureVote, FeatureComment
            from backend.models.strategy import Strategy
            from backend.models.mental_map import MentalMap, MentalMapEntry
            from backend.models.pattern_cluster import PatternCluster
            from backend.models.milestone import Milestone
            from backend.models.daily_emotion_reflection import DailyEmotionReflection
            _models_registered = True
        except Exception as e:
            print(f"Warning: Could not register models: {e}")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tradesense.db")

# Create engine with optimized configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
else:
    # PostgreSQL/MySQL optimized configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
        # Additional optimizations for production databases
        connect_args={
            "connect_timeout": 10,
            "application_name": "tradesense_backend"
        }
    )

# Create session factory with optimized settings
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent unnecessary queries after commit
)

def get_db():
    """Dependency to get database session with error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Safely create all tables with duplicate handling"""
    try:
        ensure_models_registered()
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print(f"✅ Database tables created successfully. Registered models: {get_registered_models()}")
    except Exception as e:
        print(f"⚠️ Database table creation warning: {e}")
        # Continue execution even if some tables already exist

# Database connection event handlers for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Optimize SQLite connections"""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.close()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout for monitoring"""
    logger.debug("Database connection checked out")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin for monitoring"""
    logger.debug("Database connection checked in")