"""
Enhanced Redis functionality for TradeSense
Adds session management, rate limiting backend, pub/sub, and distributed locks
"""
import json
import time
import uuid
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
import logging
import asyncio
from contextlib import contextmanager

from core.cache import redis_client, REDIS_AVAILABLE

logger = logging.getLogger(__name__)


class RedisSessionStore:
    """
    Redis-based session store for scalable session management
    """
    
    def __init__(self, redis_client=None, prefix="session:", ttl=86400):
        self.redis = redis_client or globals().get('redis_client')
        self.prefix = prefix
        self.default_ttl = ttl  # 24 hours default
    
    def create_session(self, user_id: str, data: Dict[str, Any]) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_key = f"{self.prefix}{session_id}"
        
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            **data
        }
        
        if self.redis:
            try:
                self.redis.setex(
                    session_key,
                    self.default_ttl,
                    json.dumps(session_data)
                )
                # Add to user's session index
                user_sessions_key = f"{self.prefix}user:{user_id}"
                self.redis.sadd(user_sessions_key, session_id)
                self.redis.expire(user_sessions_key, self.default_ttl)
                
                logger.info(f"Created session {session_id} for user {user_id}")
                return session_id
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
        
        return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        session_key = f"{self.prefix}{session_id}"
        
        if self.redis:
            try:
                data = self.redis.get(session_key)
                if data:
                    session_data = json.loads(data)
                    # Update last activity
                    session_data["last_activity"] = datetime.utcnow().isoformat()
                    self.redis.setex(
                        session_key,
                        self.default_ttl,
                        json.dumps(session_data)
                    )
                    return session_data
            except Exception as e:
                logger.error(f"Failed to get session: {e}")
        
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        session_key = f"{self.prefix}{session_id}"
        
        if self.redis:
            try:
                existing = self.get_session(session_id)
                if existing:
                    existing.update(data)
                    existing["last_activity"] = datetime.utcnow().isoformat()
                    self.redis.setex(
                        session_key,
                        self.default_ttl,
                        json.dumps(existing)
                    )
                    return True
            except Exception as e:
                logger.error(f"Failed to update session: {e}")
        
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"{self.prefix}{session_id}"
        
        if self.redis:
            try:
                # Get session to find user
                session_data = self.get_session(session_id)
                if session_data:
                    user_id = session_data.get("user_id")
                    # Remove from user's session index
                    if user_id:
                        user_sessions_key = f"{self.prefix}user:{user_id}"
                        self.redis.srem(user_sessions_key, session_id)
                
                # Delete session
                self.redis.delete(session_key)
                logger.info(f"Deleted session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete session: {e}")
        
        return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        user_sessions_key = f"{self.prefix}user:{user_id}"
        sessions = []
        
        if self.redis:
            try:
                session_ids = self.redis.smembers(user_sessions_key)
                for session_id in session_ids:
                    session = self.get_session(session_id)
                    if session:
                        sessions.append({
                            "session_id": session_id,
                            **session
                        })
            except Exception as e:
                logger.error(f"Failed to get user sessions: {e}")
        
        return sessions
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user"""
        count = 0
        sessions = self.get_user_sessions(user_id)
        
        for session in sessions:
            if self.delete_session(session["session_id"]):
                count += 1
        
        logger.info(f"Invalidated {count} sessions for user {user_id}")
        return count


class RedisRateLimiter:
    """
    Enhanced Redis-based rate limiter with multiple strategies
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or globals().get('redis_client')
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        strategy: str = "sliding_window"
    ) -> tuple[bool, int]:
        """
        Check if action is allowed under rate limit
        
        Returns:
            tuple: (allowed, remaining_calls)
        """
        if not self.redis:
            return True, limit
        
        try:
            if strategy == "sliding_window":
                return self._sliding_window_limit(key, limit, window)
            elif strategy == "token_bucket":
                return self._token_bucket_limit(key, limit, window)
            elif strategy == "fixed_window":
                return self._fixed_window_limit(key, limit, window)
            else:
                return self._sliding_window_limit(key, limit, window)
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, limit  # Fail open
    
    def _sliding_window_limit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Sliding window rate limiting"""
        now = time.time()
        pipeline = self.redis.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window)
        # Add current request
        pipeline.zadd(key, {str(uuid.uuid4()): now})
        # Count requests in window
        pipeline.zcard(key)
        # Set expiry
        pipeline.expire(key, window + 1)
        
        results = pipeline.execute()
        count = results[2]
        
        if count > limit:
            # Remove the just-added entry
            pipeline = self.redis.pipeline()
            pipeline.zremrangebyrank(key, -1, -1)
            pipeline.execute()
            return False, 0
        
        return True, limit - count
    
    def _token_bucket_limit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Token bucket rate limiting"""
        bucket_key = f"{key}:bucket"
        last_refill_key = f"{key}:last_refill"
        
        now = time.time()
        refill_rate = limit / window  # tokens per second
        
        # Get current bucket state
        tokens = self.redis.get(bucket_key)
        last_refill = self.redis.get(last_refill_key)
        
        if tokens is None:
            tokens = limit
        else:
            tokens = float(tokens)
        
        if last_refill is None:
            last_refill = now
        else:
            last_refill = float(last_refill)
        
        # Calculate tokens to add
        time_passed = now - last_refill
        tokens_to_add = time_passed * refill_rate
        tokens = min(limit, tokens + tokens_to_add)
        
        if tokens >= 1:
            # Consume a token
            tokens -= 1
            pipeline = self.redis.pipeline()
            pipeline.set(bucket_key, tokens)
            pipeline.set(last_refill_key, now)
            pipeline.expire(bucket_key, window * 2)
            pipeline.expire(last_refill_key, window * 2)
            pipeline.execute()
            return True, int(tokens)
        
        return False, 0
    
    def _fixed_window_limit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Fixed window rate limiting"""
        # Calculate window start
        window_start = int(time.time() / window) * window
        window_key = f"{key}:{window_start}"
        
        # Increment counter
        pipeline = self.redis.pipeline()
        pipeline.incr(window_key)
        pipeline.expire(window_key, window + 1)
        results = pipeline.execute()
        
        count = results[0]
        
        if count > limit:
            return False, 0
        
        return True, limit - count
    
    def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a key"""
        if self.redis:
            try:
                # Delete all related keys
                keys = self.redis.keys(f"{key}*")
                if keys:
                    self.redis.delete(*keys)
                return True
            except Exception as e:
                logger.error(f"Failed to reset rate limit: {e}")
        return False


class RedisPubSub:
    """
    Redis Pub/Sub for real-time features
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or globals().get('redis_client')
        self.subscribers = {}
        self._pubsub = None
        self._listener_task = None
    
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish message to channel"""
        if self.redis:
            try:
                data = json.dumps(message)
                return self.redis.publish(channel, data)
            except Exception as e:
                logger.error(f"Failed to publish message: {e}")
        return 0
    
    def subscribe(self, channel: str, callback: Callable) -> bool:
        """Subscribe to channel with callback"""
        if self.redis:
            try:
                if not self._pubsub:
                    self._pubsub = self.redis.pubsub()
                
                self._pubsub.subscribe(channel)
                self.subscribers[channel] = callback
                
                # Start listener if not running
                if not self._listener_task:
                    self._start_listener()
                
                return True
            except Exception as e:
                logger.error(f"Failed to subscribe: {e}")
        return False
    
    def unsubscribe(self, channel: str) -> bool:
        """Unsubscribe from channel"""
        if self._pubsub and channel in self.subscribers:
            try:
                self._pubsub.unsubscribe(channel)
                del self.subscribers[channel]
                return True
            except Exception as e:
                logger.error(f"Failed to unsubscribe: {e}")
        return False
    
    def _start_listener(self):
        """Start background listener for pub/sub messages"""
        async def listen():
            try:
                for message in self._pubsub.listen():
                    if message['type'] == 'message':
                        channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
                        if channel in self.subscribers:
                            try:
                                data = json.loads(message['data'])
                                callback = self.subscribers[channel]
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(channel, data)
                                else:
                                    callback(channel, data)
                            except Exception as e:
                                logger.error(f"Error in pub/sub callback: {e}")
            except Exception as e:
                logger.error(f"Pub/sub listener error: {e}")
        
        self._listener_task = asyncio.create_task(listen())


class RedisLock:
    """
    Distributed lock implementation using Redis
    """
    
    def __init__(self, redis_client=None, key: str = None, timeout: int = 10):
        self.redis = redis_client or globals().get('redis_client')
        self.key = f"lock:{key}" if key else None
        self.timeout = timeout
        self.identifier = None
    
    def acquire(self, blocking: bool = True, timeout: Optional[int] = None) -> bool:
        """Acquire the lock"""
        if not self.redis or not self.key:
            return True  # No Redis, no locking needed
        
        self.identifier = str(uuid.uuid4())
        timeout = timeout or self.timeout
        
        if blocking:
            while True:
                if self._try_acquire(timeout):
                    return True
                time.sleep(0.1)
        else:
            return self._try_acquire(timeout)
    
    def _try_acquire(self, timeout: int) -> bool:
        """Try to acquire lock once"""
        try:
            return self.redis.set(
                self.key,
                self.identifier,
                nx=True,  # Only set if not exists
                ex=timeout
            )
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def release(self) -> bool:
        """Release the lock if we own it"""
        if not self.redis or not self.key or not self.identifier:
            return True
        
        try:
            # Use Lua script to ensure atomic check-and-delete
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            return bool(self.redis.eval(lua_script, 1, self.key, self.identifier))
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
            return False
    
    def extend(self, additional_time: int) -> bool:
        """Extend lock timeout if we own it"""
        if not self.redis or not self.key or not self.identifier:
            return False
        
        try:
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            
            return bool(self.redis.eval(
                lua_script,
                1,
                self.key,
                self.identifier,
                additional_time
            ))
        except Exception as e:
            logger.error(f"Failed to extend lock: {e}")
            return False
    
    @contextmanager
    def __call__(self, key: str, timeout: int = 10):
        """Context manager for distributed locking"""
        lock = RedisLock(self.redis, key, timeout)
        acquired = lock.acquire()
        try:
            yield acquired
        finally:
            if acquired:
                lock.release()


# Global instances
session_store = RedisSessionStore() if REDIS_AVAILABLE else None
rate_limiter = RedisRateLimiter() if REDIS_AVAILABLE else None
pubsub = RedisPubSub() if REDIS_AVAILABLE else None
distributed_lock = RedisLock() if REDIS_AVAILABLE else None


# Utility functions
def get_redis_info() -> Dict[str, Any]:
    """Get Redis server information"""
    if redis_client:
        try:
            info = redis_client.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "uptime_days": info.get("uptime_in_days"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands": info.get("total_commands_processed"),
                "instantaneous_ops": info.get("instantaneous_ops_per_sec"),
                "keyspace": info.get("db0", {}),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    return {"connected": False, "error": "Redis not configured"}