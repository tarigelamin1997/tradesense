"""
Tests for Redis enhancements
"""
import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from fakeredis import FakeRedis

from core.redis_enhancements import (
    RedisSessionStore,
    RedisRateLimiter,
    RedisPubSub,
    RedisLock
)


class TestRedisSessionStore:
    """Test Redis session store functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.redis = FakeRedis(decode_responses=True)
        self.session_store = RedisSessionStore(self.redis)
    
    def test_create_session(self):
        """Test session creation"""
        session_id = self.session_store.create_session(
            "user123",
            {"ip": "192.168.1.1", "device": "mobile"}
        )
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        
        # Verify session was stored
        session_key = f"session:{session_id}"
        assert self.redis.exists(session_key)
        
        # Verify user session index
        user_sessions = self.redis.smembers("session:user:user123")
        assert session_id in user_sessions
    
    def test_get_session(self):
        """Test session retrieval"""
        session_id = self.session_store.create_session(
            "user123",
            {"ip": "192.168.1.1"}
        )
        
        session = self.session_store.get_session(session_id)
        assert session is not None
        assert session["user_id"] == "user123"
        assert session["ip"] == "192.168.1.1"
        assert "created_at" in session
        assert "last_activity" in session
    
    def test_update_session(self):
        """Test session update"""
        session_id = self.session_store.create_session("user123", {})
        
        # Update session
        success = self.session_store.update_session(
            session_id,
            {"theme": "dark", "language": "en"}
        )
        assert success is True
        
        # Verify update
        session = self.session_store.get_session(session_id)
        assert session["theme"] == "dark"
        assert session["language"] == "en"
    
    def test_delete_session(self):
        """Test session deletion"""
        session_id = self.session_store.create_session("user123", {})
        
        # Delete session
        success = self.session_store.delete_session(session_id)
        assert success is True
        
        # Verify deletion
        session = self.session_store.get_session(session_id)
        assert session is None
        
        # Verify removed from user index
        user_sessions = self.redis.smembers("session:user:user123")
        assert session_id not in user_sessions
    
    def test_get_user_sessions(self):
        """Test getting all user sessions"""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = self.session_store.create_session(
                "user123",
                {"device": f"device{i}"}
            )
            session_ids.append(session_id)
        
        # Get all sessions
        sessions = self.session_store.get_user_sessions("user123")
        assert len(sessions) == 3
        
        # Verify session data
        devices = [s["device"] for s in sessions]
        assert "device0" in devices
        assert "device1" in devices
        assert "device2" in devices
    
    def test_invalidate_user_sessions(self):
        """Test invalidating all user sessions"""
        # Create multiple sessions
        for i in range(3):
            self.session_store.create_session("user123", {})
        
        # Invalidate all
        count = self.session_store.invalidate_user_sessions("user123")
        assert count == 3
        
        # Verify all deleted
        sessions = self.session_store.get_user_sessions("user123")
        assert len(sessions) == 0


class TestRedisRateLimiter:
    """Test Redis rate limiter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.redis = FakeRedis(decode_responses=True)
        self.rate_limiter = RedisRateLimiter(self.redis)
    
    def test_sliding_window_limit(self):
        """Test sliding window rate limiting"""
        key = "test:sliding"
        limit = 5
        window = 10  # seconds
        
        # Should allow first 5 requests
        for i in range(limit):
            allowed, remaining = self.rate_limiter.check_rate_limit(
                key, limit, window, "sliding_window"
            )
            assert allowed is True
            assert remaining == limit - i - 1
        
        # 6th request should be blocked
        allowed, remaining = self.rate_limiter.check_rate_limit(
            key, limit, window, "sliding_window"
        )
        assert allowed is False
        assert remaining == 0
    
    def test_token_bucket_limit(self):
        """Test token bucket rate limiting"""
        key = "test:bucket"
        limit = 10
        window = 1  # 10 tokens per second
        
        # Should allow initial burst
        for i in range(5):
            allowed, remaining = self.rate_limiter.check_rate_limit(
                key, limit, window, "token_bucket"
            )
            assert allowed is True
        
        # Quick succession should eventually block
        blocked = False
        for i in range(10):
            allowed, _ = self.rate_limiter.check_rate_limit(
                key, limit, window, "token_bucket"
            )
            if not allowed:
                blocked = True
                break
        
        assert blocked is True
    
    def test_fixed_window_limit(self):
        """Test fixed window rate limiting"""
        key = "test:fixed"
        limit = 3
        window = 1  # 1 second window
        
        # Should allow first 3 requests
        for i in range(limit):
            allowed, remaining = self.rate_limiter.check_rate_limit(
                key, limit, window, "fixed_window"
            )
            assert allowed is True
        
        # 4th request should be blocked
        allowed, remaining = self.rate_limiter.check_rate_limit(
            key, limit, window, "fixed_window"
        )
        assert allowed is False
        assert remaining == 0
        
        # Wait for next window
        time.sleep(1.1)
        
        # Should allow again
        allowed, remaining = self.rate_limiter.check_rate_limit(
            key, limit, window, "fixed_window"
        )
        assert allowed is True
    
    def test_reset_limit(self):
        """Test rate limit reset"""
        key = "test:reset"
        
        # Use up limit
        for i in range(5):
            self.rate_limiter.check_rate_limit(key, 5, 60)
        
        # Should be blocked
        allowed, _ = self.rate_limiter.check_rate_limit(key, 5, 60)
        assert allowed is False
        
        # Reset limit
        success = self.rate_limiter.reset_limit(key)
        assert success is True
        
        # Should allow again
        allowed, _ = self.rate_limiter.check_rate_limit(key, 5, 60)
        assert allowed is True


class TestRedisPubSub:
    """Test Redis pub/sub functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.redis = FakeRedis(decode_responses=True)
        self.pubsub = RedisPubSub(self.redis)
    
    def test_publish(self):
        """Test message publishing"""
        channel = "test:channel"
        message = {"type": "notification", "data": "test"}
        
        # Should return number of subscribers (0 in this case)
        count = self.pubsub.publish(channel, message)
        assert isinstance(count, int)
    
    def test_subscribe_unsubscribe(self):
        """Test subscription management"""
        channel = "test:channel"
        callback = Mock()
        
        # Subscribe
        success = self.pubsub.subscribe(channel, callback)
        assert success is True
        assert channel in self.pubsub.subscribers
        
        # Unsubscribe
        success = self.pubsub.unsubscribe(channel)
        assert success is True
        assert channel not in self.pubsub.subscribers


class TestRedisLock:
    """Test distributed lock functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.redis = FakeRedis(decode_responses=True)
    
    def test_acquire_release(self):
        """Test lock acquisition and release"""
        lock = RedisLock(self.redis, "test_lock", timeout=10)
        
        # Acquire lock
        acquired = lock.acquire(blocking=False)
        assert acquired is True
        assert lock.identifier is not None
        
        # Try to acquire again (should fail)
        lock2 = RedisLock(self.redis, "test_lock", timeout=10)
        acquired2 = lock2.acquire(blocking=False)
        assert acquired2 is False
        
        # Release lock
        released = lock.release()
        assert released is True
        
        # Now lock2 should be able to acquire
        acquired2 = lock2.acquire(blocking=False)
        assert acquired2 is True
        lock2.release()
    
    def test_lock_timeout(self):
        """Test lock auto-expiration"""
        lock = RedisLock(self.redis, "test_timeout", timeout=1)
        
        # Acquire lock
        acquired = lock.acquire(blocking=False)
        assert acquired is True
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Another lock should be able to acquire
        lock2 = RedisLock(self.redis, "test_timeout", timeout=1)
        acquired2 = lock2.acquire(blocking=False)
        assert acquired2 is True
        lock2.release()
    
    def test_extend_lock(self):
        """Test extending lock timeout"""
        lock = RedisLock(self.redis, "test_extend", timeout=2)
        
        # Acquire lock
        acquired = lock.acquire(blocking=False)
        assert acquired is True
        
        # Extend timeout
        extended = lock.extend(5)
        assert extended is True
        
        # Verify extension by checking TTL
        ttl = self.redis.ttl("lock:test_extend")
        assert ttl > 2  # Should be extended
    
    def test_context_manager(self):
        """Test lock as context manager"""
        lock = RedisLock(self.redis)
        
        with lock("test_context", timeout=10) as acquired:
            assert acquired is True
            
            # Try to acquire same lock
            lock2 = RedisLock(self.redis, "test_context")
            acquired2 = lock2.acquire(blocking=False)
            assert acquired2 is False
        
        # After context, lock should be released
        lock3 = RedisLock(self.redis, "test_context")
        acquired3 = lock3.acquire(blocking=False)
        assert acquired3 is True
        lock3.release()


@pytest.mark.integration
class TestRedisIntegration:
    """Integration tests with actual Redis (if available)"""
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--redis-url"),
        reason="Redis URL not provided"
    )
    def test_real_redis_connection(self):
        """Test with real Redis server"""
        import redis
        
        redis_url = pytest.config.getoption("--redis-url")
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        session_store = RedisSessionStore(client)
        session_id = session_store.create_session("test_user", {"test": True})
        
        assert session_id is not None
        
        session = session_store.get_session(session_id)
        assert session is not None
        assert session["user_id"] == "test_user"
        
        # Cleanup
        session_store.delete_session(session_id)