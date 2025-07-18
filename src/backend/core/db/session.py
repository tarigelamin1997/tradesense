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
            from models.user import User
            from models.trade import Trade
            from models.portfolio import Portfolio
            from models.trading_account import TradingAccount
            from models.playbook import Playbook
            from models.tag import Tag, trade_tags
            from models.trade_review import TradeReview
            from models.trade_note import TradeNote
            from models.feature_request import FeatureRequest, FeatureVote, FeatureComment
            from models.strategy import Strategy
            from models.mental_map import MentalMap, MentalMapEntry
            from models.pattern_cluster import PatternCluster
            from models.milestone import Milestone
            from models.daily_emotion_reflection import DailyEmotionReflection
            _models_registered = True
        except Exception as e:
            print(f"Warning: Could not register models: {e}")

# Database configuration
from core.config import settings
DATABASE_URL = settings.database_url

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
        pool_size=20,              # Number of persistent connections
        max_overflow=40,           # Maximum overflow connections (increased from 30)
        pool_timeout=30,           # Timeout for getting connection from pool
        pool_pre_ping=True,        # Test connections before use
        pool_recycle=1800,         # Recycle connections after 30 min (reduced from 3600)
        echo=False,
        echo_pool=settings.debug,  # Log pool checkouts in debug mode
        # Additional optimizations for production databases
        connect_args={
            "connect_timeout": 10,
            "application_name": "tradesense_backend",
            "options": "-c timezone=utc",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
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
        # Don't log HTTPExceptions (like 401, 403) as database errors
        from fastapi import HTTPException
        if not isinstance(e, HTTPException):
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


def get_pool_status():
    """Get current database connection pool status"""
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.total(),
        "max_overflow": pool._max_overflow
    }