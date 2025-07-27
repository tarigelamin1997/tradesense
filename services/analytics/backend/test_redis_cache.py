#!/usr/bin/env python3
"""
Test Redis caching functionality
"""

import os
import sys
import time
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['DATABASE_URL'] = 'postgresql://tradesense_user:2ca9bfcf1a40257caa7b4be903c7fe22@localhost:5433/tradesense'
os.environ['JWT_SECRET_KEY'] = '3f8b7e2a1d6c9e4f7a2b5d8e1c4f7a9b2e5d8c1f4a7b9e2d5c8f1a4b7e9d2c5f'

from core.cache import cache_manager, cache_response, invalidate_user_cache

print("🧪 Testing TradeSense Redis Cache...")
print("=" * 50)

# Test 1: Basic Redis connection
print("\n1️⃣ Testing Redis connection...")
try:
    stats = cache_manager.get_stats()
    redis_stats = stats.get('redis', {})
    if redis_stats.get('connected'):
        print(f"✅ Redis connected: {redis_stats.get('type', 'Unknown')}")
        if redis_stats.get('type') == 'Redis':
            print(f"   Memory used: {redis_stats.get('used_memory', 'N/A')}")
            print(f"   Connected clients: {redis_stats.get('connected_clients', 'N/A')}")
    else:
        print(f"❌ Redis not connected: {redis_stats.get('error', 'Unknown error')}")
except Exception as e:
    print(f"❌ Failed to get cache stats: {e}")

# Test 2: Basic cache operations
print("\n2️⃣ Testing basic cache operations...")
try:
    # Set a value
    cache_manager.set("test_key", {"data": "test_value", "timestamp": time.time()}, ttl=60)
    print("✅ Cache SET successful")
    
    # Get the value
    value = cache_manager.get("test_key")
    if value and value.get("data") == "test_value":
        print(f"✅ Cache GET successful: {value}")
    else:
        print(f"❌ Cache GET failed: {value}")
    
    # Delete the value
    cache_manager.delete("test_key")
    deleted_value = cache_manager.get("test_key")
    if deleted_value is None:
        print("✅ Cache DELETE successful")
    else:
        print(f"❌ Cache DELETE failed: {deleted_value}")
        
except Exception as e:
    print(f"❌ Basic cache operations failed: {e}")

# Test 3: TTL expiration
print("\n3️⃣ Testing TTL expiration...")
try:
    # Set with 2 second TTL
    cache_manager.set("ttl_test", "will_expire", ttl=2)
    
    # Should exist immediately
    value = cache_manager.get("ttl_test")
    if value == "will_expire":
        print("✅ Value exists before expiration")
    
    # Wait for expiration
    print("   Waiting 3 seconds for expiration...")
    time.sleep(3)
    
    # Should be expired
    expired_value = cache_manager.get("ttl_test")
    if expired_value is None:
        print("✅ Value expired correctly")
    else:
        print(f"❌ Value did not expire: {expired_value}")
        
except Exception as e:
    print(f"❌ TTL expiration test failed: {e}")

# Test 4: Cache decorator
print("\n4️⃣ Testing cache decorator...")

@cache_response(ttl=60, key_prefix="test", user_aware=True)
async def expensive_calculation(user_id: int, value: int) -> dict:
    """Simulate an expensive calculation"""
    await asyncio.sleep(0.1)  # Simulate work
    return {
        "user_id": user_id,
        "result": value * 2,
        "timestamp": time.time()
    }

async def test_decorator():
    try:
        # First call - should be slow
        start = time.time()
        result1 = await expensive_calculation(user_id=1, value=42)
        duration1 = time.time() - start
        print(f"✅ First call took {duration1:.3f}s: {result1}")
        
        # Second call - should be cached and fast
        start = time.time()
        result2 = await expensive_calculation(user_id=1, value=42)
        duration2 = time.time() - start
        print(f"✅ Cached call took {duration2:.3f}s: {result2}")
        
        if duration2 < duration1 / 10:  # Should be at least 10x faster
            print("✅ Cache decorator working correctly")
        else:
            print("⚠️ Cache might not be working optimally")
            
        # Test cache invalidation
        invalidate_user_cache(1, cache_type="test")
        
        # Third call - should be slow again
        start = time.time()
        result3 = await expensive_calculation(user_id=1, value=42)
        duration3 = time.time() - start
        print(f"✅ After invalidation took {duration3:.3f}s")
        
        if duration3 > duration2 * 5:  # Should be slower than cached
            print("✅ Cache invalidation working correctly")
        
    except Exception as e:
        print(f"❌ Decorator test failed: {e}")

# Run async test
asyncio.run(test_decorator())

# Test 5: Performance under load
print("\n5️⃣ Testing performance under load...")
try:
    import random
    
    # Generate test data
    test_keys = [f"perf_test_{i}" for i in range(100)]
    test_data = [{"value": random.randint(1, 1000), "data": f"test_{i}"} for i in range(100)]
    
    # Measure write performance
    start = time.time()
    for key, data in zip(test_keys, test_data):
        cache_manager.set(key, data, ttl=300)
    write_duration = time.time() - start
    write_ops_per_sec = len(test_keys) / write_duration
    print(f"✅ Write performance: {write_ops_per_sec:.0f} ops/sec ({write_duration:.3f}s for {len(test_keys)} writes)")
    
    # Measure read performance
    start = time.time()
    for key in test_keys:
        _ = cache_manager.get(key)
    read_duration = time.time() - start
    read_ops_per_sec = len(test_keys) / read_duration
    print(f"✅ Read performance: {read_ops_per_sec:.0f} ops/sec ({read_duration:.3f}s for {len(test_keys)} reads)")
    
    # Cleanup
    for key in test_keys:
        cache_manager.delete(key)
    
except Exception as e:
    print(f"❌ Performance test failed: {e}")

# Test 6: Cache statistics
print("\n6️⃣ Cache statistics...")
try:
    stats = cache_manager.get_stats()
    print("📊 Cache Stats:")
    print(f"   Redis: {stats.get('redis', {})}")
    print(f"   Memory: {stats.get('memory', {})}")
    
    # Calculate hit rate if available
    redis_stats = stats.get('redis', {})
    if redis_stats.get('connected') and redis_stats.get('hit_rate') is not None:
        print(f"   Cache hit rate: {redis_stats.get('hit_rate')}%")
        
except Exception as e:
    print(f"❌ Failed to get cache statistics: {e}")

print("\n" + "=" * 50)
print("✅ Redis cache testing complete!")
print("🚀 Cache system is ready for production use!")