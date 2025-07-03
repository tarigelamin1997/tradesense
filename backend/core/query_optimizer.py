"""
Database Query Optimization Utilities

Provides utilities for optimizing database queries, caching, and performance monitoring.
"""
import time
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from functools import wraps
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

T = TypeVar('T')

class QueryOptimizer:
    """Database query optimization utilities"""
    
    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
    
    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key for function call"""
        import hashlib
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_result(self, cache_key: str, ttl_seconds: int = 300) -> Optional[Any]:
        """Get cached result if not expired"""
        if cache_key in self.query_cache:
            if cache_key in self.cache_ttl:
                if datetime.utcnow() < self.cache_ttl[cache_key]:
                    return self.query_cache[cache_key]
                else:
                    # Cache expired, remove it
                    del self.query_cache[cache_key]
                    del self.cache_ttl[cache_key]
        return None
    
    def set_cached_result(self, cache_key: str, result: Any, ttl_seconds: int = 300):
        """Cache result with TTL"""
        self.query_cache[cache_key] = result
        self.cache_ttl[cache_key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries matching pattern"""
        if pattern:
            keys_to_remove = [k for k in self.query_cache.keys() if pattern in k]
        else:
            keys_to_remove = list(self.query_cache.keys())
        
        for key in keys_to_remove:
            self.query_cache.pop(key, None)
            self.cache_ttl.pop(key, None)
    
    def record_query_time(self, query_name: str, duration: float):
        """Record query execution time for monitoring"""
        self.query_stats[query_name].append(duration)
        # Keep only last 100 measurements
        if len(self.query_stats[query_name]) > 100:
            self.query_stats[query_name] = self.query_stats[query_name][-100:]
    
    def get_query_stats(self) -> Dict[str, Dict[str, float]]:
        """Get query performance statistics"""
        stats = {}
        for query_name, times in self.query_stats.items():
            if times:
                stats[query_name] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "last_time": times[-1] if times else 0
                }
        return stats

# Global query optimizer instance
query_optimizer = QueryOptimizer()

def optimize_query(
    cache_ttl: int = 300,
    eager_load: Optional[List[str]] = None,
    use_cache: bool = True
):
    """
    Decorator to optimize database queries with caching and eager loading
    
    Args:
        cache_ttl: Cache TTL in seconds
        eager_load: List of relationships to eager load
        use_cache: Whether to use caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Generate cache key
            cache_key = query_optimizer.cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            if use_cache:
                cached_result = query_optimizer.get_cached_result(cache_key, cache_ttl)
                if cached_result is not None:
                    duration = time.time() - start_time
                    query_optimizer.record_query_time(f"{func.__name__}_cached", duration)
                    logger.debug(f"Cache hit for {func.__name__}: {duration:.3f}s")
                    return cached_result
            
            # Execute query
            try:
                result = func(*args, **kwargs)
                
                # Apply eager loading if specified
                if eager_load and hasattr(result, 'query'):
                    for relation in eager_load:
                        result = result.options(joinedload(relation))
                
                # Cache result
                if use_cache:
                    query_optimizer.set_cached_result(cache_key, result, cache_ttl)
                
                duration = time.time() - start_time
                query_optimizer.record_query_time(func.__name__, duration)
                
                if duration > 1.0:  # Log slow queries
                    logger.warning(f"Slow query {func.__name__}: {duration:.3f}s")
                else:
                    logger.debug(f"Query {func.__name__}: {duration:.3f}s")
                
                return result
                
            except SQLAlchemyError as e:
                duration = time.time() - start_time
                logger.error(f"Database error in {func.__name__}: {str(e)}")
                raise
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    return decorator

def paginate_query(
    query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum items per page
    
    Returns:
        Dict with items, pagination info, and total count
    """
    # Validate and limit per_page
    per_page = min(per_page, max_per_page)
    per_page = max(per_page, 1)
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    items = query.offset(offset).limit(per_page).all()
    
    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
    }

def bulk_upsert(
    db: Session,
    model: Type[T],
    records: List[Dict[str, Any]],
    unique_fields: List[str],
    update_fields: Optional[List[str]] = None
) -> List[T]:
    """
    Bulk upsert records efficiently
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        records: List of record dictionaries
        unique_fields: Fields that determine uniqueness
        update_fields: Fields to update if record exists
    
    Returns:
        List of upserted model instances
    """
    if not records:
        return []
    
    # Build unique constraint filter
    unique_filters = []
    for record in records:
        filter_conditions = []
        for field in unique_fields:
            if field in record:
                filter_conditions.append(getattr(model, field) == record[field])
        if filter_conditions:
            unique_filters.append(and_(*filter_conditions))
    
    # Find existing records
    existing_records = {}
    if unique_filters:
        existing = db.query(model).filter(or_(*unique_filters)).all()
        for record in existing:
            key = tuple(getattr(record, field) for field in unique_fields)
            existing_records[key] = record
    
    # Process records
    upserted_records = []
    for record_data in records:
        # Create unique key
        key = tuple(record_data.get(field) for field in unique_fields)
        
        if key in existing_records:
            # Update existing record
            existing_record = existing_records[key]
            if update_fields:
                for field in update_fields:
                    if field in record_data:
                        setattr(existing_record, field, record_data[field])
            else:
                # Update all non-unique fields
                for field, value in record_data.items():
                    if field not in unique_fields:
                        setattr(existing_record, field, value)
            upserted_records.append(existing_record)
        else:
            # Create new record
            new_record = model(**record_data)
            db.add(new_record)
            upserted_records.append(new_record)
    
    try:
        db.commit()
        return upserted_records
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Bulk upsert failed: {str(e)}")
        raise

def optimize_trade_queries(db: Session, user_id: str, **filters) -> Any:
    """
    Optimized trade query with common filters and eager loading
    
    Args:
        db: Database session
        user_id: User ID to filter by
        **filters: Additional filters to apply
    
    Returns:
        Optimized query object
    """
    from backend.models.trade import Trade
    from backend.models.trade_note import TradeNote
    from backend.models.trade_review import TradeReview
    
    query = db.query(Trade).filter(Trade.user_id == user_id)
    
    # Apply additional filters
    if 'start_date' in filters:
        query = query.filter(Trade.entry_time >= filters['start_date'])
    if 'end_date' in filters:
        query = query.filter(Trade.entry_time <= filters['end_date'])
    if 'symbol' in filters:
        query = query.filter(Trade.symbol == filters['symbol'])
    if 'strategy' in filters:
        query = query.filter(Trade.strategy == filters['strategy'])
    if 'status' in filters:
        query = query.filter(Trade.status == filters['status'])
    
    # Eager load related data
    query = query.options(
        joinedload(Trade.notes),
        joinedload(Trade.reviews),
        joinedload(Trade.tags)
    )
    
    return query

def get_performance_metrics() -> Dict[str, Any]:
    """Get overall performance metrics"""
    stats = query_optimizer.get_query_stats()
    
    # Calculate overall metrics
    total_queries = sum(stat['count'] for stat in stats.values())
    avg_query_time = sum(stat['avg_time'] * stat['count'] for stat in stats.values()) / total_queries if total_queries > 0 else 0
    
    # Find slowest queries
    slowest_queries = sorted(
        [(name, stat['avg_time']) for name, stat in stats.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return {
        "total_queries": total_queries,
        "average_query_time": avg_query_time,
        "cache_hit_rate": len([s for s in stats.values() if '_cached' in s]) / len(stats) if stats else 0,
        "slowest_queries": slowest_queries,
        "cache_size": len(query_optimizer.query_cache),
        "detailed_stats": stats
    } 