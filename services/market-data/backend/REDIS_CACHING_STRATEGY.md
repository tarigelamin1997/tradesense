# Redis Caching Strategy

## Overview

TradeSense uses a hybrid caching strategy with Redis as the primary cache and in-memory fallback for development/testing environments. This document outlines the caching architecture and usage patterns.

## Architecture

### Cache Layers

1. **Redis (Primary)**
   - Distributed caching for production
   - Persistent across server restarts
   - Shared between all instances
   - TTL-based expiration

2. **In-Memory (Fallback)**
   - Development environments
   - When Redis is unavailable
   - Per-instance cache
   - Size-limited with LRU eviction

### Components

#### 1. Core Cache Manager (`core/cache.py`)
- Hybrid cache with automatic fallback
- JSON serialization for complex objects
- Pattern-based invalidation
- Cache statistics and monitoring

#### 2. Enhanced Redis Features (`core/redis_enhancements.py`)

##### Session Store
- Secure session management
- User session indexing
- Session invalidation
- Activity tracking

```python
# Create session
session_id = session_store.create_session(user_id, {"ip": "192.168.1.1"})

# Get session
session = session_store.get_session(session_id)

# Invalidate all user sessions
session_store.invalidate_user_sessions(user_id)
```

##### Rate Limiter
- Multiple strategies (sliding window, token bucket, fixed window)
- Distributed rate limiting across instances
- Configurable limits per endpoint

```python
# Check rate limit
allowed, remaining = rate_limiter.check_rate_limit(
    "login:192.168.1.1", 
    limit=5, 
    window=300,
    strategy="sliding_window"
)
```

##### Pub/Sub
- Real-time notifications
- WebSocket event broadcasting
- Cross-instance communication

```python
# Publish event
pubsub.publish("trade:updates", {"user_id": 123, "action": "new_trade"})

# Subscribe to events
pubsub.subscribe("trade:updates", handle_trade_update)
```

##### Distributed Locks
- Prevent race conditions
- Atomic operations
- Auto-release on timeout

```python
with distributed_lock("import:user:123", timeout=30):
    # Exclusive operation
    process_trade_import()
```

## Caching Strategy

### What to Cache

1. **API Responses**
   - Trade analytics (5 min TTL)
   - Portfolio summaries (2 min TTL)
   - Market data (1 min TTL)
   - User profiles (10 min TTL)

2. **Database Queries**
   - Aggregated statistics (5 min TTL)
   - User settings (10 min TTL)
   - Reference data (1 hour TTL)

3. **Computed Values**
   - Performance metrics
   - Risk calculations
   - Technical indicators

### What NOT to Cache

1. **Sensitive Data**
   - Passwords
   - API keys
   - Personal information

2. **Transactional Data**
   - Trade executions
   - Account balances
   - Order status

3. **Real-time Data**
   - Live prices
   - Order book
   - Market depth

## Usage Patterns

### 1. API Response Caching

```python
@cache_response(ttl=300, key_prefix="analytics", user_aware=True)
async def get_portfolio_analytics(user_id: int):
    # Expensive calculation
    return calculate_analytics(user_id)
```

### 2. Query Result Caching

```python
@query_cache.cache_query(ttl=60)
async def get_top_trades(user_id: int, limit: int = 10):
    return db.query(Trade).filter_by(user_id=user_id).limit(limit).all()
```

### 3. Manual Cache Management

```python
# Set cache
cache_manager.set("market:btc:price", 45000, ttl=60)

# Get cache
price = cache_manager.get("market:btc:price")

# Invalidate pattern
invalidate_cache_pattern("market:*")
```

### 4. User-Specific Invalidation

```python
# After trade import
invalidate_trades_cache(user_id)
invalidate_analytics_cache(user_id)

# After settings change
invalidate_user_cache(user_id, "settings")
```

## Performance Considerations

### TTL Guidelines

- **Short (< 1 min)**: Real-time data, market prices
- **Medium (1-5 min)**: User data, analytics
- **Long (> 5 min)**: Reference data, configurations

### Memory Management

- Redis memory limit: Configure based on instance
- In-memory cache: 1000 entries max
- Automatic cleanup of expired entries

### Cache Warming

- Pre-load frequently accessed data
- Background refresh for critical data
- Gradual cache population to avoid thundering herd

## Monitoring

### Metrics to Track

1. **Hit Rate**: Aim for > 80%
2. **Response Time**: Cache hits < 5ms
3. **Memory Usage**: Stay under 80% of limit
4. **Eviction Rate**: Should be minimal

### Health Checks

```python
# Get cache statistics
stats = cache_manager.get_stats()

# Check Redis health
info = get_redis_info()
```

## Best Practices

1. **Always Set TTL**: Never cache indefinitely
2. **Use Meaningful Keys**: Include context (user_id, type)
3. **Handle Failures Gracefully**: Fall back to database
4. **Invalidate Proactively**: Don't wait for TTL
5. **Monitor Performance**: Track hit rates and latency

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0
REDIS_PRIVATE_URL=redis://internal:6379/0  # For Railway

# Cache settings
CACHE_DEFAULT_TTL=300
CACHE_MAX_MEMORY_ENTRIES=1000
```

### Feature Flags

```python
# Disable caching for debugging
CACHE_ENABLED=false

# Use only in-memory cache
REDIS_ENABLED=false
```

## Troubleshooting

### Common Issues

1. **Low Hit Rate**
   - Check TTL values
   - Verify cache keys
   - Monitor invalidation patterns

2. **Memory Issues**
   - Reduce TTL for large objects
   - Implement cache size limits
   - Use Redis memory policies

3. **Stale Data**
   - Implement proper invalidation
   - Use shorter TTL
   - Add cache versioning

### Debug Commands

```python
# Clear all cache
cache_manager.clear()

# View cache contents (development only)
redis_client.keys("*")

# Monitor cache operations
redis_client.monitor()
```

## Future Enhancements

1. **Cache Tagging**: Group related entries
2. **Compression**: For large objects
3. **Multi-tier Caching**: L1/L2 cache layers
4. **Predictive Caching**: ML-based prefetching
5. **Cache Analytics**: Detailed usage patterns