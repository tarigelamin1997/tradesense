"""
Performance tests for health check endpoints
Tests response times, throughput, and scalability of health checks
"""
import pytest
import time
import asyncio
import statistics
from typing import List, Dict, Any
import concurrent.futures
from locust import HttpUser, task, between
import httpx
from fastapi.testclient import TestClient


class TestHealthEndpointPerformance:
    """Test performance characteristics of health endpoints"""
    
    def test_basic_health_check_response_time(self, client: TestClient):
        """Test that basic health check responds within acceptable time"""
        response_times = []
        iterations = 100
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            response = client.get("/health")
            end_time = time.perf_counter()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Assert performance requirements
        assert avg_time < 50  # Average should be under 50ms
        assert median_time < 30  # Median should be under 30ms
        assert p95_time < 100  # 95% of requests under 100ms
        assert p99_time < 200  # 99% of requests under 200ms
    
    def test_detailed_health_check_response_time(self, client: TestClient):
        """Test that detailed health check responds within acceptable time"""
        response_times = []
        iterations = 50
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            response = client.get("/health/detailed")
            end_time = time.perf_counter()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)
        
        # Detailed checks are expected to be slower
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]
        
        assert avg_time < 200  # Average under 200ms
        assert p95_time < 500  # 95% under 500ms
    
    def test_health_check_concurrent_performance(self, client: TestClient):
        """Test health check performance under concurrent load"""
        concurrent_users = 50
        requests_per_user = 10
        response_times = []
        errors = []
        
        def make_health_request(user_id: int):
            user_times = []
            user_errors = []
            
            for _ in range(requests_per_user):
                try:
                    start_time = time.perf_counter()
                    response = client.get("/health")
                    end_time = time.perf_counter()
                    
                    if response.status_code == 200:
                        user_times.append((end_time - start_time) * 1000)
                    else:
                        user_errors.append(response.status_code)
                except Exception as e:
                    user_errors.append(str(e))
            
            return user_times, user_errors
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_health_request, i) for i in range(concurrent_users)]
            
            for future in concurrent.futures.as_completed(futures):
                times, errs = future.result()
                response_times.extend(times)
                errors.extend(errs)
        
        # Analyze results
        total_requests = concurrent_users * requests_per_user
        success_rate = len(response_times) / total_requests
        
        assert success_rate > 0.99  # 99% success rate
        assert statistics.mean(response_times) < 100  # Average under 100ms even under load
        assert len(errors) < total_requests * 0.01  # Less than 1% errors
    
    @pytest.mark.asyncio
    async def test_health_check_async_performance(self):
        """Test async health check performance"""
        async def make_async_request(session: httpx.AsyncClient, url: str):
            start_time = time.perf_counter()
            response = await session.get(url)
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000, response.status_code
        
        url = "http://localhost:8000/health"
        concurrent_requests = 100
        
        async with httpx.AsyncClient() as client:
            tasks = [make_async_request(client, url) for _ in range(concurrent_requests)]
            
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = (time.perf_counter() - start_time) * 1000
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, tuple)]
        response_times = [r[0] for r in valid_results]
        
        # All concurrent requests should complete quickly
        assert total_time < 1000  # All 100 requests in under 1 second
        assert len(valid_results) > concurrent_requests * 0.95  # 95% success


class TestHealthCheckThroughput:
    """Test health check endpoint throughput"""
    
    def test_health_check_requests_per_second(self, client: TestClient):
        """Test how many health check requests can be handled per second"""
        duration_seconds = 5
        request_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            response = client.get("/health")
            if response.status_code == 200:
                request_count += 1
        
        requests_per_second = request_count / duration_seconds
        
        # Should handle at least 100 requests per second
        assert requests_per_second > 100
    
    def test_health_check_sustained_load(self, client: TestClient):
        """Test health check performance under sustained load"""
        test_duration = 30  # 30 seconds
        interval = 0.01  # 10ms between requests (100 req/s target)
        
        response_times = []
        errors = []
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            request_start = time.perf_counter()
            
            try:
                response = client.get("/health")
                request_time = (time.perf_counter() - request_start) * 1000
                
                if response.status_code == 200:
                    response_times.append(request_time)
                else:
                    errors.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
            
            # Wait for next interval
            time.sleep(interval)
        
        # Analyze sustained load results
        assert len(errors) < len(response_times) * 0.01  # Less than 1% errors
        assert statistics.mean(response_times) < 100  # Consistent performance
        
        # Check for performance degradation over time
        first_third = response_times[:len(response_times)//3]
        last_third = response_times[-len(response_times)//3:]
        
        # Performance shouldn't degrade significantly
        assert statistics.mean(last_third) < statistics.mean(first_third) * 1.5


class TestHealthCheckScalability:
    """Test health check scalability characteristics"""
    
    def test_health_check_scaling_pattern(self, client: TestClient):
        """Test how health check performance scales with load"""
        load_levels = [10, 50, 100, 200]  # Concurrent users
        results = []
        
        for concurrent_users in load_levels:
            level_times = []
            
            def make_request():
                start = time.perf_counter()
                response = client.get("/health")
                end = time.perf_counter()
                
                if response.status_code == 200:
                    return (end - start) * 1000
                return None
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrent_users * 5)]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        level_times.append(result)
            
            results.append({
                "concurrent_users": concurrent_users,
                "avg_response_time": statistics.mean(level_times),
                "p95_response_time": statistics.quantiles(level_times, n=20)[18]
            })
        
        # Verify scaling characteristics
        for i in range(1, len(results)):
            # Response time shouldn't increase linearly with load
            load_increase = results[i]["concurrent_users"] / results[i-1]["concurrent_users"]
            time_increase = results[i]["avg_response_time"] / results[i-1]["avg_response_time"]
            
            # Sub-linear scaling (better than linear)
            assert time_increase < load_increase


class HealthCheckLoadTest(HttpUser):
    """Locust load test for health check endpoints"""
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def basic_health_check(self):
        """Test basic health endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def detailed_health_check(self):
        """Test detailed health endpoint"""
        with self.client.get("/health/detailed", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def versioned_health_check(self):
        """Test versioned API health endpoint"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class TestHealthCheckCaching:
    """Test health check caching performance"""
    
    def test_cached_health_check_performance(self, client: TestClient):
        """Test performance improvement with health check caching"""
        # First request (cache miss)
        start_time = time.perf_counter()
        response1 = client.get("/health/detailed")
        first_request_time = (time.perf_counter() - start_time) * 1000
        
        assert response1.status_code == 200
        
        # Subsequent requests (cache hits)
        cached_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            response = client.get("/health/detailed")
            cached_times.append((time.perf_counter() - start_time) * 1000)
            assert response.status_code == 200
        
        # Cached requests should be significantly faster
        avg_cached_time = statistics.mean(cached_times)
        assert avg_cached_time < first_request_time * 0.5  # At least 50% faster
    
    def test_cache_invalidation_performance(self, client: TestClient):
        """Test performance impact of cache invalidation"""
        # Measure time for cache invalidation
        cache_invalidation_times = []
        
        for _ in range(10):
            # Simulate cache invalidation trigger
            start_time = time.perf_counter()
            response = client.post("/admin/cache/invalidate/health")
            invalidation_time = (time.perf_counter() - start_time) * 1000
            
            if response.status_code == 200:
                cache_invalidation_times.append(invalidation_time)
        
        # Cache invalidation should be fast
        if cache_invalidation_times:
            assert statistics.mean(cache_invalidation_times) < 50


class TestHealthCheckResourceUsage:
    """Test resource usage of health check endpoints"""
    
    def test_health_check_memory_usage(self, client: TestClient):
        """Test that health checks don't leak memory"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many health check requests
        for _ in range(1000):
            response = client.get("/health")
            assert response.status_code == 200
        
        # Check memory after requests
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 50MB)
        assert memory_increase < 50
    
    def test_health_check_cpu_efficiency(self, client: TestClient):
        """Test CPU efficiency of health checks"""
        import psutil
        
        # Measure CPU usage during health checks
        cpu_percentages = []
        
        for _ in range(100):
            psutil.cpu_percent(interval=None)  # Reset
            
            # Make health check request
            response = client.get("/health")
            assert response.status_code == 200
            
            # Measure CPU after request
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_percentages.append(cpu_percent)
        
        # Average CPU usage should be reasonable
        avg_cpu = statistics.mean(cpu_percentages)
        assert avg_cpu < 50  # Less than 50% CPU usage


@pytest.mark.parametrize("endpoint,expected_time_ms", [
    ("/health", 50),
    ("/health/ready", 30),
    ("/api/v1/health", 50),
    ("/api/v1/status", 20),
    ("/version", 10),
])
def test_health_endpoint_sla(client: TestClient, endpoint: str, expected_time_ms: float):
    """Test that each health endpoint meets its SLA"""
    response_times = []
    
    for _ in range(20):
        start_time = time.perf_counter()
        response = client.get(endpoint)
        response_time = (time.perf_counter() - start_time) * 1000
        
        if response.status_code == 200:
            response_times.append(response_time)
    
    # 95% of requests should meet SLA
    p95_time = statistics.quantiles(response_times, n=20)[18]
    assert p95_time < expected_time_ms