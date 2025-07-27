"""
Production-ready database connection pooling and optimization

Implements connection pooling, query optimization, and monitoring
"""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time
from datetime import datetime
from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
import logging

from core.config_env import get_env_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class DatabasePoolConfig:
    """Database connection pool configuration"""
    
    def __init__(self, env_config):
        self.database_url = env_config.database.url
        self.pool_size = env_config.database.pool_size
        self.max_overflow = env_config.database.max_overflow
        self.pool_timeout = env_config.database.pool_timeout
        self.pool_recycle = env_config.database.pool_recycle
        self.echo = env_config.database.echo
        self.environment = env_config.environment.value
        
        # Query monitoring
        self.slow_query_threshold = 1.0  # seconds
        self.log_slow_queries = True
        
        # Connection retry
        self.retry_on_disconnect = True
        self.max_retries = 3
        self.retry_delay = 1.0


class ConnectionPoolManager:
    """Manage database connection pools with monitoring"""
    
    def __init__(self, config: DatabasePoolConfig):
        self.config = config
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "total_time": 0.0
        }
        
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with optimized settings"""
        
        # Choose pool class based on environment
        if self.config.environment == "testing":
            poolclass = StaticPool
            pool_kwargs = {"connect_args": {"check_same_thread": False}}
        elif self.config.environment == "development":
            poolclass = QueuePool
            pool_kwargs = {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600
            }
        else:  # production/staging
            poolclass = QueuePool
            pool_kwargs = {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
                "pool_pre_ping": True,  # Verify connections before use
                "echo_pool": self.config.echo  # Log pool checkouts/checkins
            }
        
        # Create engine
        engine = create_engine(
            self.config.database_url,
            poolclass=poolclass,
            echo=self.config.echo,
            future=True,
            query_cache_size=1200,  # Cache parsed SQL statements
            connect_args={
                "server_settings": {
                    "application_name": f"tradesense-{self.config.environment}",
                    "jit": "off"  # Disable JIT for more predictable performance
                },
                "command_timeout": 60,
                "options": "-c statement_timeout=30000"  # 30 second statement timeout
            },
            **pool_kwargs
        )
        
        # Add event listeners
        self._setup_event_listeners(engine)
        
        logger.info(
            f"Database engine created with pool_size={pool_kwargs.get('pool_size', 'default')}, "
            f"max_overflow={pool_kwargs.get('max_overflow', 'default')}"
        )
        
        return engine
    
    def _setup_event_listeners(self, engine: Engine):
        """Set up SQLAlchemy event listeners for monitoring"""
        
        # Connection events
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Configure connection on checkout"""
            connection_record.info['connect_time'] = time.time()
            
            # Set connection parameters
            with dbapi_connection.cursor() as cursor:
                # Set work_mem for better query performance
                cursor.execute("SET work_mem = '16MB'")
                # Set random_page_cost for SSD
                cursor.execute("SET random_page_cost = 1.1")
                # Enable timing for EXPLAIN ANALYZE
                cursor.execute("SET track_io_timing = ON")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout"""
            checkout_time = time.time()
            connect_time = connection_record.info.get('connect_time', checkout_time)
            age = checkout_time - connect_time
            
            if age > 3600:  # Log old connections
                logger.warning(f"Old connection checked out (age: {age:.1f}s)")
        
        # Query execution events
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query start time"""
            conn.info.setdefault('query_start_time', []).append(time.time())
            self._query_stats["total_queries"] += 1
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries and update stats"""
            total_time = time.time() - conn.info['query_start_time'].pop(-1)
            self._query_stats["total_time"] += total_time
            
            if self.config.log_slow_queries and total_time > self.config.slow_query_threshold:
                self._query_stats["slow_queries"] += 1
                logger.warning(
                    f"Slow query detected ({total_time:.2f}s): {statement[:100]}...",
                    extra={
                        "query_time": total_time,
                        "query": statement[:500],
                        "parameters": str(parameters)[:200]
                    }
                )
        
        @event.listens_for(engine, "handle_error")
        def handle_error(exception_context):
            """Handle database errors"""
            self._query_stats["failed_queries"] += 1
            
            if exception_context.is_disconnect:
                logger.error("Database connection lost")
                # Invalidate the connection
                exception_context.invalidate_pool_ok = True
            else:
                logger.error(
                    f"Database error: {exception_context.original_exception}",
                    exc_info=True
                )
    
    def initialize(self) -> sessionmaker:
        """Initialize connection pool and session factory"""
        if not self.engine:
            self.engine = self.create_engine()
            
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # Don't expire objects after commit
            class_=Session
        )
        
        # Test connection
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
        
        return self.SessionLocal
    
    @contextmanager
    def get_db_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        if not self.engine or not hasattr(self.engine.pool, 'status'):
            return {"status": "not initialized"}
        
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow()
        }
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        stats = self._query_stats.copy()
        
        if stats["total_queries"] > 0:
            stats["avg_query_time"] = stats["total_time"] / stats["total_queries"]
            stats["slow_query_percentage"] = (stats["slow_queries"] / stats["total_queries"]) * 100
        else:
            stats["avg_query_time"] = 0
            stats["slow_query_percentage"] = 0
        
        return stats
    
    def optimize_connection_pool(self):
        """Dynamically optimize pool settings based on usage"""
        pool_status = self.get_pool_status()
        
        if pool_status.get("status") == "not initialized":
            return
        
        # Check if we're consistently at max capacity
        utilization = pool_status["checked_out"] / pool_status["total"]
        
        if utilization > 0.8:
            logger.warning(
                f"High connection pool utilization: {utilization:.1%}. "
                "Consider increasing pool_size or max_overflow"
            )
        
        # Check for connection leaks
        if pool_status["checked_out"] > 0 and self._query_stats["total_queries"] == 0:
            logger.warning(
                f"Possible connection leak: {pool_status['checked_out']} connections "
                "checked out but no queries executed"
            )
    
    def close(self):
        """Close all connections and dispose of the engine"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global connection pool manager
_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """Get or create the global connection pool manager"""
    global _pool_manager
    
    if _pool_manager is None:
        env_config = get_env_config()
        db_config = DatabasePoolConfig(env_config)
        _pool_manager = ConnectionPoolManager(db_config)
        _pool_manager.initialize()
    
    return _pool_manager


def get_db():
    """Dependency to get database session"""
    pool_manager = get_pool_manager()
    session = pool_manager.SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Query optimization helpers
class QueryOptimizer:
    """Helper class for query optimization"""
    
    @staticmethod
    def add_query_hints(query, hints: Dict[str, Any]):
        """Add query hints for optimization"""
        # Example: query.execution_options(synchronize_session=False)
        return query.execution_options(**hints)
    
    @staticmethod
    def explain_query(session: Session, query):
        """Get query execution plan"""
        from sqlalchemy import text
        
        # Get the compiled SQL
        compiled = query.statement.compile(compile_kwargs={"literal_binds": True})
        sql = str(compiled)
        
        # Run EXPLAIN ANALYZE
        result = session.execute(text(f"EXPLAIN ANALYZE {sql}"))
        return [row[0] for row in result]
    
    @staticmethod
    def create_indexes_sql() -> list:
        """Generate SQL for creating recommended indexes"""
        return [
            # User queries
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);",
            
            # Trade queries
            "CREATE INDEX IF NOT EXISTS idx_trades_user_id_created_at ON trades(user_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol_created_at ON trades(symbol, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status) WHERE status != 'closed';",
            
            # Analytics queries
            "CREATE INDEX IF NOT EXISTS idx_analytics_user_id_date ON user_analytics(user_id, date DESC);",
            "CREATE INDEX IF NOT EXISTS idx_analytics_metric_date ON analytics_metrics(metric_name, created_at DESC);",
            
            # Session queries
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON sessions(user_id, expires_at);",
            
            # Audit queries
            "CREATE INDEX IF NOT EXISTS idx_audit_user_id_created ON audit_logs(user_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_audit_action_created ON audit_logs(action, created_at DESC);"
        ]