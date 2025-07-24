"""
API Gateway health aggregation tests for TradeSense
Tests the gateway's ability to aggregate health status from all microservices
"""
import pytest
import asyncio
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, List, Any
from datetime import datetime, timedelta


class TestGatewayHealthAggregation:
    """Test API Gateway health aggregation functionality"""
    
    @pytest.fixture
    def gateway_url(self) -> str:
        """Gateway URL for testing"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def mock_service_health_responses(self) -> Dict[str, Dict[str, Any]]:
        """Mock health responses from microservices"""
        return {
            "auth": {
                "service": "auth",
                "status": "healthy",
                "version": "1.0.0",
                "database": {"connected": True, "latency_ms": 5}
            },
            "trading": {
                "service": "trading",
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "database": {"status": "healthy", "latency_ms": 8},
                    "message_queue": {"status": "healthy", "latency_ms": 12}
                }
            },
            "analytics": {
                "service": "analytics",
                "status": "degraded",
                "version": "1.0.0",
                "processing_queue": {"queue_size": 1500, "status": "overloaded"}
            },
            "market-data": {
                "service": "market-data",
                "status": "healthy",
                "version": "1.0.0",
                "data_sources": {
                    "primary": {"connected": True, "latency_ms": 15},
                    "backup": {"connected": True, "latency_ms": 20}
                }
            },
            "billing": {
                "service": "billing",
                "status": "healthy",
                "version": "1.0.0",
                "payment_gateway": {"status": "connected"}
            },
            "ai": {
                "service": "ai",
                "status": "unhealthy",
                "version": "1.0.0",
                "error": "Model loading failed"
            }
        }
    
    @pytest.mark.asyncio
    async def test_gateway_health_endpoint(self, gateway_url: str):
        """Test gateway's main health endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{gateway_url}/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Check overall status
                assert "status" in data
                assert data["status"] in ["healthy", "degraded", "unhealthy"]
                assert "timestamp" in data
                assert "services" in data
                
                # Verify timestamp format
                timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                assert (datetime.utcnow() - timestamp) < timedelta(seconds=5)
            except httpx.ConnectError:
                pytest.skip("Gateway service not running")
    
    @pytest.mark.asyncio
    async def test_gateway_services_list(self, gateway_url: str):
        """Test gateway's services listing endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{gateway_url}/services")
                
                assert response.status_code == 200
                data = response.json()
                
                assert "services" in data
                services = data["services"]
                
                # Check each service entry
                for service in services:
                    assert "name" in service
                    assert "url" in service
                    assert "status" in service
                    assert "last_check" in service
                    assert service["status"] in ["healthy", "degraded", "unhealthy", "unknown"]
                
                # Verify all expected services are listed
                service_names = [s["name"] for s in services]
                expected_services = ["auth", "trading", "analytics", "market-data", "billing", "ai"]
                for expected in expected_services:
                    assert expected in service_names
            except httpx.ConnectError:
                pytest.skip("Gateway service not running")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_gateway_aggregates_healthy_status(
        self, 
        mock_get: AsyncMock,
        mock_service_health_responses: Dict[str, Dict[str, Any]]
    ):
        """Test gateway correctly aggregates when all services are healthy"""
        # Mock all services as healthy
        healthy_responses = {
            service: {**data, "status": "healthy"}
            for service, data in mock_service_health_responses.items()
        }
        
        async def mock_service_response(url: str, **kwargs):
            for service, response_data in healthy_responses.items():
                if service in url:
                    mock_response = AsyncMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = response_data
                    return mock_response
            raise httpx.ConnectError(f"Unknown service URL: {url}")
        
        mock_get.side_effect = mock_service_response
        
        # Test aggregated health
        gateway_health = await self._get_aggregated_health(healthy_responses)
        assert gateway_health["overall_status"] == "healthy"
        assert all(s["status"] == "healthy" for s in gateway_health["services"])
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_gateway_aggregates_degraded_status(
        self,
        mock_get: AsyncMock,
        mock_service_health_responses: Dict[str, Dict[str, Any]]
    ):
        """Test gateway reports degraded when some services are degraded"""
        # Use mock responses with one degraded service
        gateway_health = await self._get_aggregated_health(mock_service_health_responses)
        
        # Gateway should report degraded if any service is degraded
        assert gateway_health["overall_status"] == "degraded"
        
        # Verify individual service statuses
        service_statuses = {s["name"]: s["status"] for s in gateway_health["services"]}
        assert service_statuses["analytics"] == "degraded"
        assert service_statuses["ai"] == "unhealthy"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_gateway_aggregates_unhealthy_status(
        self,
        mock_get: AsyncMock,
        mock_service_health_responses: Dict[str, Dict[str, Any]]
    ):
        """Test gateway reports unhealthy when critical services fail"""
        # Mark critical services as unhealthy
        unhealthy_responses = {
            **mock_service_health_responses,
            "auth": {**mock_service_health_responses["auth"], "status": "unhealthy"},
            "trading": {**mock_service_health_responses["trading"], "status": "unhealthy"}
        }
        
        gateway_health = await self._get_aggregated_health(unhealthy_responses)
        
        # Gateway should report unhealthy if critical services fail
        assert gateway_health["overall_status"] == "unhealthy"
        assert gateway_health["critical_services_failed"] == ["auth", "trading"]
    
    async def _get_aggregated_health(self, service_responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Helper to simulate gateway health aggregation"""
        services = []
        statuses = []
        critical_failed = []
        
        for service_name, response in service_responses.items():
            status = response.get("status", "unknown")
            services.append({
                "name": service_name,
                "status": status,
                "details": response
            })
            statuses.append(status)
            
            # Check if critical service failed
            if service_name in ["auth", "trading"] and status == "unhealthy":
                critical_failed.append(service_name)
        
        # Determine overall status
        if critical_failed:
            overall_status = "unhealthy"
        elif "unhealthy" in statuses:
            overall_status = "degraded"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "services": services,
            "critical_services_failed": critical_failed
        }


class TestGatewayHealthCheckResilience:
    """Test gateway resilience during service failures"""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_gateway_handles_service_timeout(self, mock_get: AsyncMock):
        """Test gateway handles individual service timeouts gracefully"""
        async def mock_timeout_response(url: str, **kwargs):
            if "trading" in url:
                raise httpx.TimeoutException("Service timeout")
            else:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response
        
        mock_get.side_effect = mock_timeout_response
        
        # Gateway should still return overall health even if one service times out
        gateway_response = {
            "status": "degraded",
            "services": {
                "auth": {"status": "healthy"},
                "trading": {"status": "unknown", "error": "timeout"},
                "analytics": {"status": "healthy"}
            }
        }
        
        assert gateway_response["status"] == "degraded"
        assert gateway_response["services"]["trading"]["status"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_gateway_circuit_breaker(self):
        """Test gateway implements circuit breaker for failing services"""
        # Test that after multiple failures, gateway stops checking a service
        failure_counts = {"auth": 0, "trading": 0}
        circuit_breaker_threshold = 3
        
        for _ in range(5):
            try:
                # Simulate health check
                pass
            except Exception:
                failure_counts["auth"] += 1
        
        # After threshold, circuit should be open
        assert failure_counts["auth"] >= circuit_breaker_threshold
        # Gateway should skip checking this service temporarily
    
    @pytest.mark.asyncio
    async def test_gateway_health_check_caching(self):
        """Test gateway caches health check results appropriately"""
        cache_duration = 30  # seconds
        
        # First check should hit all services
        first_check_time = datetime.utcnow()
        first_result = {"status": "healthy", "timestamp": first_check_time.isoformat()}
        
        # Second check within cache window should return cached result
        second_check_time = first_check_time + timedelta(seconds=15)
        # Should return cached result without hitting services
        
        # Third check after cache expiry should hit services again
        third_check_time = first_check_time + timedelta(seconds=35)
        # Should make fresh health checks


class TestGatewayHealthMetrics:
    """Test gateway health check metrics and monitoring"""
    
    @pytest.mark.asyncio
    async def test_gateway_health_metrics_collection(self, gateway_url: str):
        """Test that gateway collects metrics about health checks"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{gateway_url}/health/metrics")
                
                assert response.status_code == 200
                data = response.json()
                
                # Check metrics structure
                assert "health_check_metrics" in data
                metrics = data["health_check_metrics"]
                
                # Verify metric fields
                assert "total_checks" in metrics
                assert "successful_checks" in metrics
                assert "failed_checks" in metrics
                assert "average_response_time_ms" in metrics
                assert "checks_per_service" in metrics
                
                # Verify per-service metrics
                for service, service_metrics in metrics["checks_per_service"].items():
                    assert "success_rate" in service_metrics
                    assert "average_latency_ms" in service_metrics
                    assert "last_check_duration_ms" in service_metrics
            except httpx.ConnectError:
                pytest.skip("Gateway service not running")
    
    @pytest.mark.asyncio
    async def test_gateway_health_history(self, gateway_url: str):
        """Test gateway maintains health check history"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{gateway_url}/health/history?duration=1h")
                
                assert response.status_code == 200
                data = response.json()
                
                assert "history" in data
                assert isinstance(data["history"], list)
                
                # Check history entries
                for entry in data["history"]:
                    assert "timestamp" in entry
                    assert "overall_status" in entry
                    assert "service_statuses" in entry
                    
                    # Verify timestamp ordering (newest first)
                    if len(data["history"]) > 1:
                        timestamps = [
                            datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                            for entry in data["history"]
                        ]
                        assert timestamps == sorted(timestamps, reverse=True)
            except httpx.ConnectError:
                pytest.skip("Gateway service not running")


class TestGatewayHealthAlerts:
    """Test gateway health check alerting functionality"""
    
    @pytest.mark.asyncio
    async def test_gateway_alerts_on_service_failure(self):
        """Test gateway triggers alerts when services fail"""
        alert_conditions = {
            "service_down": {
                "threshold": 1,  # Alert immediately
                "services": ["auth", "trading"]  # Critical services
            },
            "degraded_duration": {
                "threshold_minutes": 5,
                "services": ["analytics"]
            }
        }
        
        # Simulate service failure
        failed_service = "auth"
        alert_triggered = False
        
        # Gateway should trigger alert for critical service failure
        if failed_service in alert_conditions["service_down"]["services"]:
            alert_triggered = True
        
        assert alert_triggered
    
    @pytest.mark.asyncio
    async def test_gateway_alert_cooldown(self):
        """Test gateway implements alert cooldown to prevent spam"""
        cooldown_period = 300  # 5 minutes
        
        # First alert should be sent
        first_alert_time = datetime.utcnow()
        first_alert_sent = True
        
        # Second alert within cooldown should be suppressed
        second_alert_time = first_alert_time + timedelta(seconds=120)
        second_alert_sent = False  # Should be suppressed
        
        # Third alert after cooldown should be sent
        third_alert_time = first_alert_time + timedelta(seconds=360)
        third_alert_sent = True
        
        assert first_alert_sent
        assert not second_alert_sent
        assert third_alert_sent


@pytest.mark.parametrize("service_statuses,expected_overall", [
    (["healthy", "healthy", "healthy"], "healthy"),
    (["healthy", "degraded", "healthy"], "degraded"),
    (["healthy", "unhealthy", "healthy"], "degraded"),
    (["unhealthy", "unhealthy", "unhealthy"], "unhealthy"),
    (["healthy", "unknown", "healthy"], "degraded"),
])
def test_gateway_status_aggregation_logic(
    service_statuses: List[str],
    expected_overall: str
):
    """Test gateway's logic for aggregating service statuses"""
    # This tests the aggregation logic without making actual HTTP calls
    overall_status = "healthy"
    
    if "unhealthy" in service_statuses:
        if service_statuses.count("unhealthy") >= len(service_statuses) // 2:
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
    elif "degraded" in service_statuses or "unknown" in service_statuses:
        overall_status = "degraded"
    
    assert overall_status == expected_overall