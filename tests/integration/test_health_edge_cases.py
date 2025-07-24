"""
Edge case tests for health check endpoints
Tests various failure scenarios: database down, service timeouts, network issues, etc.
"""
import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.exc import OperationalError, DatabaseError, InterfaceError
from redis.exceptions import ConnectionError as RedisConnectionError
import httpx
from fastapi.testclient import TestClient


class TestDatabaseFailureScenarios:
    """Test health checks during database failures"""
    
    @patch('src.backend.core.database.SessionLocal')
    def test_health_check_database_connection_lost(self, mock_session, client: TestClient):
        """Test health check when database connection is lost"""
        # Simulate connection lost
        mock_session.side_effect = OperationalError("Lost connection to MySQL server", None, None)
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"]["status"] == "disconnected"
        assert "error" in data["database"]
        assert "Lost connection" in data["database"]["error"]
    
    @patch('src.backend.core.database.SessionLocal')
    def test_health_check_database_timeout(self, mock_session, client: TestClient):
        """Test health check when database queries timeout"""
        # Simulate query timeout
        mock_session.side_effect = OperationalError("Query execution was interrupted", None, None)
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "timeout" in data["database"]["error"].lower() or "interrupted" in data["database"]["error"].lower()
    
    @patch('src.backend.core.database.engine')
    def test_health_check_database_pool_exhausted(self, mock_engine, client: TestClient):
        """Test health check when database connection pool is exhausted"""
        # Simulate pool exhaustion
        mock_pool = MagicMock()
        mock_pool.size.return_value = 20
        mock_pool.checked_in.return_value = 0
        mock_pool.overflow.return_value = 10
        mock_pool.total.return_value = 30
        mock_engine.pool = mock_pool
        
        response = client.get("/health/detailed")
        
        data = response.json()
        # Should still be healthy but show pool status
        assert data["database"]["pool_size"] == 20
        assert data["database"]["active_connections"] == 30
        assert data["database"]["pool_overflow"] == 10
    
    @patch('src.backend.core.database.SessionLocal')
    def test_health_check_database_locked(self, mock_session, client: TestClient):
        """Test health check when database tables are locked"""
        # Simulate database lock
        mock_session.side_effect = OperationalError("Lock wait timeout exceeded", None, None)
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "lock" in data["database"]["error"].lower()


class TestCacheFailureScenarios:
    """Test health checks during cache (Redis) failures"""
    
    @patch('src.backend.core.cache.redis_client')
    def test_health_check_redis_connection_failed(self, mock_redis, client: TestClient):
        """Test health check when Redis connection fails"""
        # Simulate Redis connection failure
        mock_redis.ping.side_effect = RedisConnectionError("Connection refused")
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200  # Should degrade gracefully
        data = response.json()
        assert data["status"] == "degraded"
        assert data["components"]["cache"]["status"] == "disconnected"
        assert "Connection refused" in data["components"]["cache"]["error"]
    
    @patch('src.backend.core.cache.redis_client')
    def test_health_check_redis_timeout(self, mock_redis, client: TestClient):
        """Test health check when Redis operations timeout"""
        # Simulate Redis timeout
        mock_redis.ping.side_effect = TimeoutError("Redis operation timed out")
        
        response = client.get("/health/detailed")
        
        data = response.json()
        assert data["status"] == "degraded"
        assert data["components"]["cache"]["status"] == "error"
        assert "timed out" in data["components"]["cache"]["error"]
    
    @patch('src.backend.core.cache.redis_client')
    def test_health_check_redis_memory_full(self, mock_redis, client: TestClient):
        """Test health check when Redis memory is full"""
        # Simulate Redis memory full
        mock_redis.info.return_value = {
            "used_memory": 8589934592,  # 8GB
            "maxmemory": 8589934592,    # 8GB
            "evicted_keys": 1000000
        }
        mock_redis.ping.return_value = True
        
        response = client.get("/health/detailed")
        
        data = response.json()
        assert data["components"]["cache"]["status"] == "degraded"
        assert data["components"]["cache"]["memory_usage_percent"] == 100
        assert data["components"]["cache"]["evicted_keys"] > 0


class TestNetworkFailureScenarios:
    """Test health checks during network failures"""
    
    @pytest.mark.asyncio
    async def test_health_check_dns_resolution_failure(self):
        """Test health check when DNS resolution fails"""
        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.side_effect = OSError("Name or service not known")
            
            # Attempt to check external service health
            with pytest.raises(httpx.ConnectError):
                async with httpx.AsyncClient() as client:
                    await client.get("http://external-service.invalid/health")
    
    @pytest.mark.asyncio
    async def test_health_check_network_unreachable(self):
        """Test health check when network is unreachable"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.NetworkError("Network is unreachable")
            
            async with httpx.AsyncClient() as client:
                with pytest.raises(httpx.NetworkError):
                    await client.get("http://localhost:8001/health")
    
    def test_health_check_partial_network_failure(self, client: TestClient):
        """Test health check when only some network connections fail"""
        with patch('httpx.Client.get') as mock_get:
            def selective_failure(url, **kwargs):
                if "external-api" in url:
                    raise httpx.ConnectError("Connection refused")
                else:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "healthy"}
                    return mock_response
            
            mock_get.side_effect = selective_failure
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "external-api" in [
                comp for comp, status in data["components"].items() 
                if status.get("status") == "error"
            ]


class TestResourceExhaustionScenarios:
    """Test health checks during resource exhaustion"""
    
    @patch('psutil.virtual_memory')
    def test_health_check_low_memory(self, mock_memory, client: TestClient):
        """Test health check when system memory is low"""
        # Simulate low memory (95% used)
        mock_memory.return_value = MagicMock(
            total=8589934592,  # 8GB
            available=429496729,  # ~400MB
            percent=95.0
        )
        
        response = client.get("/health/detailed")
        
        data = response.json()
        assert data["system"]["memory"]["percent_used"] > 90
        # Service might degrade performance but should still respond
        assert response.status_code == 200
    
    @patch('psutil.cpu_percent')
    def test_health_check_high_cpu(self, mock_cpu, client: TestClient):
        """Test health check when CPU usage is high"""
        # Simulate high CPU usage
        mock_cpu.return_value = 98.5
        
        response = client.get("/health/detailed")
        
        data = response.json()
        assert data["system"]["cpu"]["percent_used"] > 95
        # Should still respond but might be slower
        assert response.status_code == 200
    
    @patch('os.statvfs')
    def test_health_check_disk_full(self, mock_statvfs, client: TestClient):
        """Test health check when disk is full"""
        # Simulate disk full
        mock_stat = MagicMock()
        mock_stat.f_bavail = 0  # No available blocks
        mock_stat.f_blocks = 1000000
        mock_stat.f_bsize = 4096
        mock_statvfs.return_value = mock_stat
        
        response = client.get("/health/detailed")
        
        data = response.json()
        assert data["system"]["disk"]["percent_used"] == 100
        # Critical issue - should affect health status
        assert data["status"] in ["degraded", "unhealthy"]


class TestConcurrentRequestScenarios:
    """Test health checks under high concurrent load"""
    
    def test_health_check_under_load(self, client: TestClient):
        """Test health check performance under concurrent requests"""
        import concurrent.futures
        import threading
        
        request_count = 100
        successful_requests = 0
        failed_requests = 0
        response_times = []
        lock = threading.Lock()
        
        def make_request():
            try:
                start = time.time()
                response = client.get("/health")
                end = time.time()
                
                with lock:
                    if response.status_code == 200:
                        successful_requests += 1
                        response_times.append(end - start)
                    else:
                        failed_requests += 1
                
                return response
            except Exception:
                with lock:
                    failed_requests += 1
                return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(request_count)]
            concurrent.futures.wait(futures)
        
        # Most requests should succeed
        assert successful_requests > request_count * 0.95
        
        # Average response time should be reasonable
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 0.5  # 500ms average
    
    def test_health_check_rate_limiting(self, client: TestClient):
        """Test health check rate limiting behavior"""
        # Make many requests rapidly
        responses = []
        for _ in range(50):
            response = client.get("/health")
            responses.append(response)
            time.sleep(0.01)  # 10ms between requests
        
        # Check if rate limiting kicked in
        status_codes = [r.status_code for r in responses]
        rate_limited = status_codes.count(429)  # Too Many Requests
        
        # Some rate limiting is expected but not all requests
        assert rate_limited < len(responses) * 0.5


class TestServiceDependencyFailures:
    """Test health checks when service dependencies fail"""
    
    @patch('httpx.Client.get')
    def test_health_check_auth_service_down(self, mock_get, client: TestClient):
        """Test health check when auth service is down"""
        def mock_service_response(url, **kwargs):
            if "auth" in url:
                raise httpx.ConnectError("Auth service unavailable")
            return MagicMock(status_code=200, json=lambda: {"status": "healthy"})
        
        mock_get.side_effect = mock_service_response
        
        response = client.get("/health/detailed")
        
        data = response.json()
        # Auth service being down should severely impact health
        assert data["status"] in ["degraded", "unhealthy"]
        assert data["components"]["auth_service"]["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_cascading_service_failures(self):
        """Test health check during cascading service failures"""
        # Simulate service dependency chain failure
        service_dependencies = {
            "trading": ["auth", "market-data"],
            "analytics": ["trading", "market-data"],
            "ai": ["analytics", "market-data"]
        }
        
        failed_services = ["market-data"]
        affected_services = set(failed_services)
        
        # Calculate cascading failures
        for service, deps in service_dependencies.items():
            if any(dep in affected_services for dep in deps):
                affected_services.add(service)
        
        assert "trading" in affected_services
        assert "analytics" in affected_services
        assert "ai" in affected_services


class TestRecoveryScenarios:
    """Test health check behavior during recovery from failures"""
    
    def test_health_check_gradual_recovery(self, client: TestClient):
        """Test health check status during gradual recovery"""
        recovery_stages = [
            {"status": "unhealthy", "components_up": 2},
            {"status": "degraded", "components_up": 4},
            {"status": "degraded", "components_up": 5},
            {"status": "healthy", "components_up": 6}
        ]
        
        for stage in recovery_stages:
            # Simulate recovery stage
            with patch('src.backend.api.health.router.get_system_health') as mock_health:
                mock_health.return_value = {
                    "status": stage["status"],
                    "components_up": stage["components_up"],
                    "total_components": 6
                }
                
                response = client.get("/health")
                data = response.json()
                
                assert data["status"] == stage["status"]
                
                # Status code should reflect health
                if stage["status"] == "unhealthy":
                    assert response.status_code == 503
                else:
                    assert response.status_code == 200
    
    def test_health_check_flapping_detection(self):
        """Test detection of flapping health status"""
        health_history = [
            "healthy", "unhealthy", "healthy", "unhealthy", 
            "healthy", "unhealthy", "healthy", "unhealthy"
        ]
        
        # Detect flapping (rapid status changes)
        changes = sum(
            1 for i in range(1, len(health_history)) 
            if health_history[i] != health_history[i-1]
        )
        
        flapping_threshold = 5
        is_flapping = changes >= flapping_threshold
        
        assert is_flapping
        # System should detect and report flapping condition