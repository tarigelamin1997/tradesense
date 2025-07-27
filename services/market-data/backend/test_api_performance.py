#!/usr/bin/env python3
"""
Test API performance with caching and optimizations
"""

import os
import sys
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor
import httpx
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "perf_test@example.com"
TEST_USER_PASSWORD = "test_password_123"
NUM_REQUESTS = 100
CONCURRENT_USERS = 10

print("🧪 Testing TradeSense API Performance...")
print("=" * 50)

async def create_test_user():
    """Create a test user for performance testing"""
    async with httpx.AsyncClient() as client:
        # Try to register
        response = await client.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "username": "perf_test_user",
                "password": TEST_USER_PASSWORD,
                "full_name": "Performance Test User"
            }
        )
        if response.status_code not in [201, 400]:  # 400 if user already exists
            print(f"❌ Failed to create test user: {response.text}")
            return None
        
        # Login to get token
        response = await client.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        if response.status_code != 200:
            print(f"❌ Failed to login: {response.text}")
            return None
        
        token_data = response.json()
        return token_data.get("access_token")

async def test_endpoint_performance(endpoint: str, token: str, test_name: str):
    """Test performance of a specific endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    response_times = []
    errors = 0
    cache_hits = 0
    
    print(f"\n📊 Testing {test_name}...")
    
    async with httpx.AsyncClient() as client:
        # Warm up cache with first request
        await client.get(f"{API_BASE_URL}{endpoint}", headers=headers)
        
        # Run performance test
        for i in range(NUM_REQUESTS):
            start_time = time.time()
            try:
                response = await client.get(f"{API_BASE_URL}{endpoint}", headers=headers)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    response_times.append(duration)
                    # Check if response was cached (usually much faster)
                    if duration < 0.01:  # Less than 10ms likely cached
                        cache_hits += 1
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                print(f"   ❌ Request {i+1} failed: {e}")
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"   Progress: {i+1}/{NUM_REQUESTS} requests completed")
    
    # Calculate statistics
    if response_times:
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        
        print(f"\n✅ {test_name} Results:")
        print(f"   Total requests: {NUM_REQUESTS}")
        print(f"   Successful: {len(response_times)}")
        print(f"   Errors: {errors}")
        print(f"   Cache hits (estimated): {cache_hits} ({cache_hits/NUM_REQUESTS*100:.1f}%)")
        print(f"   Average response time: {avg_time*1000:.2f}ms")
        print(f"   Median response time: {median_time*1000:.2f}ms")
        print(f"   Min response time: {min_time*1000:.2f}ms")
        print(f"   Max response time: {max_time*1000:.2f}ms")
        print(f"   95th percentile: {p95_time*1000:.2f}ms")
        print(f"   99th percentile: {p99_time*1000:.2f}ms")
        print(f"   Requests per second: {1/avg_time:.1f}")
        
        return {
            "endpoint": endpoint,
            "avg_ms": avg_time * 1000,
            "p95_ms": p95_time * 1000,
            "p99_ms": p99_time * 1000,
            "rps": 1/avg_time,
            "cache_hit_rate": cache_hits/NUM_REQUESTS
        }
    else:
        print(f"❌ All requests failed for {test_name}")
        return None

async def test_concurrent_load(endpoint: str, token: str, test_name: str):
    """Test endpoint under concurrent load"""
    print(f"\n🔥 Testing {test_name} under concurrent load...")
    print(f"   Concurrent users: {CONCURRENT_USERS}")
    
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    
    async def make_request():
        async with httpx.AsyncClient() as client:
            return await client.get(f"{API_BASE_URL}{endpoint}", headers=headers)
    
    # Create concurrent tasks
    tasks = []
    for _ in range(CONCURRENT_USERS * 10):  # 10 requests per user
        tasks.append(make_request())
    
    # Execute all tasks concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
    failed = len(responses) - successful
    
    print(f"\n✅ Concurrent Load Test Results:")
    print(f"   Total requests: {len(responses)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Throughput: {len(responses)/total_time:.1f} requests/second")
    
    return {
        "throughput": len(responses)/total_time,
        "success_rate": successful/len(responses)
    }

async def test_cache_invalidation(token: str):
    """Test cache invalidation on data changes"""
    print("\n🔄 Testing cache invalidation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Get initial trades (should cache)
        start = time.time()
        response1 = await client.get(f"{API_BASE_URL}/trades", headers=headers)
        time1 = time.time() - start
        initial_count = len(response1.json()) if response1.status_code == 200 else 0
        
        # Get again (should be cached and fast)
        start = time.time()
        response2 = await client.get(f"{API_BASE_URL}/trades", headers=headers)
        time2 = time.time() - start
        
        # Create a new trade (should invalidate cache)
        new_trade = await client.post(
            f"{API_BASE_URL}/trades",
            headers=headers,
            json={
                "symbol": "AAPL",
                "direction": "long",
                "quantity": 100,
                "entry_price": 150.00,
                "entry_time": "2024-01-15T10:00:00Z",
                "exit_price": 155.00,
                "exit_time": "2024-01-15T14:00:00Z"
            }
        )
        
        # Get trades again (cache should be invalidated, slower)
        start = time.time()
        response3 = await client.get(f"{API_BASE_URL}/trades", headers=headers)
        time3 = time.time() - start
        final_count = len(response3.json()) if response3.status_code == 200 else 0
        
        print(f"   Initial fetch: {time1*1000:.2f}ms")
        print(f"   Cached fetch: {time2*1000:.2f}ms (speedup: {time1/time2:.1f}x)")
        print(f"   After invalidation: {time3*1000:.2f}ms")
        print(f"   Cache working: {'✅ Yes' if time2 < time1/2 else '❌ No'}")
        print(f"   Invalidation working: {'✅ Yes' if final_count > initial_count else '❌ No'}")

async def main():
    """Run all performance tests"""
    # Create test user and get token
    print("🔐 Setting up test user...")
    token = await create_test_user()
    if not token:
        print("❌ Failed to setup test user")
        return
    
    print("✅ Test user created and authenticated")
    
    # Test individual endpoints
    results = []
    
    # Test trades endpoint
    result = await test_endpoint_performance("/trades", token, "Trades Endpoint")
    if result:
        results.append(result)
    
    # Test analytics endpoint
    result = await test_endpoint_performance("/analytics/summary", token, "Analytics Summary")
    if result:
        results.append(result)
    
    # Test performance metrics endpoint
    result = await test_endpoint_performance("/health/metrics", token, "Health Metrics")
    if result:
        results.append(result)
    
    # Test concurrent load
    await test_concurrent_load("/trades", token, "Trades Endpoint")
    
    # Test cache invalidation
    await test_cache_invalidation(token)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Performance Test Summary:")
    print("=" * 50)
    
    for result in results:
        print(f"\n{result['endpoint']}:")
        print(f"  Average: {result['avg_ms']:.2f}ms")
        print(f"  P95: {result['p95_ms']:.2f}ms")
        print(f"  P99: {result['p99_ms']:.2f}ms")
        print(f"  RPS: {result['rps']:.1f}")
        print(f"  Cache Hit Rate: {result['cache_hit_rate']*100:.1f}%")
    
    print("\n✅ Performance testing complete!")

if __name__ == "__main__":
    asyncio.run(main())