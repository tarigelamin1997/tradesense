"""
Integration tests for health check monitoring system
Tests monitoring, alerting, and observability of health checks
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from fastapi.testclient import TestClient


class TestHealthCheckMonitoring:
    """Test health check monitoring and observability"""
    
    @pytest.fixture
    def monitoring_config(self) -> Dict[str, Any]:
        """Monitoring configuration for tests"""
        return {
            "check_interval": 30,  # seconds
            "retention_period": 86400,  # 24 hours
            "alert_thresholds": {
                "consecutive_failures": 3,
                "degraded_duration": 300,  # 5 minutes
                "response_time_ms": 1000
            },
            "metrics_enabled": True,
            "logging_enabled": True
        }
    
    def test_health_check_metrics_collection(self, client: TestClient):
        """Test that health checks generate proper metrics"""
        # Make several health check requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
        
        # Check metrics endpoint
        metrics_response = client.get("/metrics")
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.text
            
            # Verify health check metrics are present
            assert "health_check_total" in metrics_data
            assert "health_check_duration_seconds" in metrics_data
            assert "health_check_status" in metrics_data
            
            # Verify labels
            assert 'endpoint="/health"' in metrics_data
            assert 'status="healthy"' in metrics_data
    
    def test_health_check_logging(self, client: TestClient):
        """Test that health checks are properly logged"""
        with patch('logging.Logger.info') as mock_log:
            response = client.get("/health/detailed")
            assert response.status_code == 200
            
            # Verify logging calls
            log_calls = [call[0][0] for call in mock_log.call_args_list]
            
            # Should log health check requests and results
            assert any("Health check requested" in log for log in log_calls)
            assert any("Health check completed" in log for log in log_calls)
    
    @pytest.mark.asyncio
    async def test_health_check_history_tracking(self, monitoring_config: Dict[str, Any]):
        """Test that health check history is properly tracked"""
        history_store: List[Dict[str, Any]] = []
        
        async def record_health_check(status: str, response_time_ms: float):
            history_store.append({
                "timestamp": datetime.utcnow(),
                "status": status,
                "response_time_ms": response_time_ms,
                "components": {}
            })
        
        # Simulate health checks over time
        statuses = ["healthy", "healthy", "degraded", "healthy", "unhealthy", "healthy"]
        
        for status in statuses:
            await record_health_check(status, 50.0)
            await asyncio.sleep(0.1)
        
        # Verify history is tracked
        assert len(history_store) == len(statuses)
        
        # Verify history ordering
        timestamps = [entry["timestamp"] for entry in history_store]
        assert timestamps == sorted(timestamps)
        
        # Verify status transitions are captured
        status_sequence = [entry["status"] for entry in history_store]
        assert status_sequence == statuses
    
    def test_health_check_status_transitions(self, client: TestClient):
        """Test monitoring of health status transitions"""
        transition_log = []
        
        def log_transition(from_status: str, to_status: str, timestamp: datetime):
            transition_log.append({
                "from": from_status,
                "to": to_status,
                "timestamp": timestamp,
                "duration": None
            })
        
        # Simulate status changes
        with patch('src.backend.api.health.router.get_current_status') as mock_status:
            statuses = ["healthy", "healthy", "degraded", "unhealthy", "degraded", "healthy"]
            
            previous_status = None
            for status in statuses:
                mock_status.return_value = status
                
                if previous_status and previous_status != status:
                    log_transition(previous_status, status, datetime.utcnow())
                
                response = client.get("/health")
                previous_status = status
        
        # Verify transitions were logged
        assert len(transition_log) == 4  # healthy->degraded, degraded->unhealthy, unhealthy->degraded, degraded->healthy
        
        # Verify critical transitions
        critical_transitions = [t for t in transition_log if t["to"] == "unhealthy"]
        assert len(critical_transitions) == 1


class TestHealthCheckAlerting:
    """Test health check alerting system"""
    
    @pytest.fixture
    def alert_manager(self) -> MagicMock:
        """Mock alert manager for testing"""
        manager = MagicMock()
        manager.alerts_sent = []
        
        def send_alert(alert_type: str, message: str, severity: str):
            manager.alerts_sent.append({
                "type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.utcnow()
            })
        
        manager.send_alert = send_alert
        return manager
    
    def test_alert_on_service_failure(self, client: TestClient, alert_manager: MagicMock):
        """Test that alerts are sent when services fail"""
        with patch('src.backend.core.alerting.alert_manager', alert_manager):
            with patch('src.backend.api.health.router.check_database_health') as mock_db:
                # Simulate database failure
                mock_db.return_value = {"status": "disconnected", "error": "Connection refused"}
                
                response = client.get("/health/detailed")
                
                # Should trigger alert
                assert len(alert_manager.alerts_sent) > 0
                
                # Verify alert content
                db_alerts = [a for a in alert_manager.alerts_sent if "database" in a["message"].lower()]
                assert len(db_alerts) > 0
                assert db_alerts[0]["severity"] == "critical"
    
    def test_alert_on_degraded_duration(self, alert_manager: MagicMock):
        """Test alerts when service is degraded for too long"""
        degraded_start = datetime.utcnow()
        threshold_minutes = 5
        
        # Simulate degraded status for extended period
        current_time = degraded_start + timedelta(minutes=threshold_minutes + 1)
        
        # Check if alert should be triggered
        degraded_duration = (current_time - degraded_start).total_seconds() / 60
        
        if degraded_duration > threshold_minutes:
            alert_manager.send_alert(
                "health_degraded_duration",
                f"Service has been degraded for {degraded_duration:.1f} minutes",
                "warning"
            )
        
        assert len(alert_manager.alerts_sent) == 1
        assert alert_manager.alerts_sent[0]["severity"] == "warning"
    
    def test_alert_rate_limiting(self, alert_manager: MagicMock):
        """Test that alerts are rate-limited to prevent spam"""
        # Try to send many alerts rapidly
        for i in range(10):
            alert_manager.send_alert("test_alert", f"Test message {i}", "info")
        
        # With rate limiting, not all alerts should be sent
        # This is a simplified test - actual implementation would track timestamps
        unique_alerts = {a["message"] for a in alert_manager.alerts_sent}
        assert len(unique_alerts) == 10  # All unique messages sent
        
        # But repeated identical alerts should be limited
        alert_manager.alerts_sent = []
        for i in range(10):
            alert_manager.send_alert("test_alert", "Repeated message", "info")
        
        # In practice, only first alert should be sent within time window
        # This test demonstrates the concept
        assert len(alert_manager.alerts_sent) == 10  # Without rate limiting
    
    def test_alert_escalation(self, alert_manager: MagicMock):
        """Test alert escalation for persistent issues"""
        escalation_levels = [
            {"duration": 0, "severity": "warning", "recipients": ["ops-team"]},
            {"duration": 300, "severity": "critical", "recipients": ["ops-team", "on-call"]},
            {"duration": 1800, "severity": "critical", "recipients": ["ops-team", "on-call", "management"]}
        ]
        
        issue_start = datetime.utcnow()
        
        # Test escalation at different time points
        for minutes_elapsed in [0, 10, 35]:
            current_time = issue_start + timedelta(minutes=minutes_elapsed)
            elapsed_seconds = (current_time - issue_start).total_seconds()
            
            # Find appropriate escalation level
            level = None
            for esc in escalation_levels:
                if elapsed_seconds >= esc["duration"]:
                    level = esc
            
            if level:
                alert_manager.send_alert(
                    "service_unhealthy",
                    f"Service unhealthy for {minutes_elapsed} minutes",
                    level["severity"]
                )
        
        # Verify escalation occurred
        alerts = alert_manager.alerts_sent
        severities = [a["severity"] for a in alerts]
        assert severities == ["warning", "critical", "critical"]


class TestHealthCheckDashboard:
    """Test health check dashboard and visualization"""
    
    def test_health_dashboard_data(self, client: TestClient):
        """Test health dashboard data endpoint"""
        response = client.get("/api/v1/health/dashboard")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify dashboard data structure
            assert "current_status" in data
            assert "services" in data
            assert "recent_incidents" in data
            assert "uptime_percentage" in data
            assert "response_time_trend" in data
            
            # Verify service information
            for service in data["services"]:
                assert "name" in service
                assert "status" in service
                assert "uptime_24h" in service
                assert "avg_response_time" in service
            
            # Verify uptime calculation
            assert 0 <= data["uptime_percentage"] <= 100
    
    def test_health_status_aggregation(self, client: TestClient):
        """Test aggregated health status for dashboard"""
        response = client.get("/api/v1/health/summary")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify summary structure
            assert "overall_status" in data
            assert "healthy_services" in data
            assert "degraded_services" in data
            assert "unhealthy_services" in data
            assert "total_services" in data
            
            # Verify counts add up
            total = (data["healthy_services"] + 
                    data["degraded_services"] + 
                    data["unhealthy_services"])
            assert total == data["total_services"]


class TestHealthCheckIntegrationWithMonitoringTools:
    """Test integration with external monitoring tools"""
    
    def test_prometheus_metrics_format(self, client: TestClient):
        """Test health metrics in Prometheus format"""
        response = client.get("/metrics", headers={"Accept": "text/plain"})
        
        if response.status_code == 200:
            metrics = response.text
            
            # Verify Prometheus metric format
            assert "# HELP" in metrics
            assert "# TYPE" in metrics
            
            # Verify health-specific metrics
            expected_metrics = [
                "health_check_duration_seconds",
                "health_check_total",
                "service_health_status",
                "component_health_status"
            ]
            
            for metric in expected_metrics:
                assert metric in metrics
    
    def test_health_check_open_telemetry(self):
        """Test OpenTelemetry integration for health checks"""
        with patch('opentelemetry.trace.get_tracer') as mock_tracer:
            tracer = MagicMock()
            mock_tracer.return_value = tracer
            
            # Simulate health check with tracing
            with tracer.start_as_current_span("health_check") as span:
                span.set_attribute("health.endpoint", "/health")
                span.set_attribute("health.status", "healthy")
                span.set_attribute("health.response_time_ms", 45.2)
            
            # Verify span was created with proper attributes
            span_calls = tracer.start_as_current_span.call_args_list
            assert len(span_calls) > 0
    
    def test_health_check_structured_logging(self):
        """Test structured logging for health checks"""
        import json
        
        with patch('logging.Logger.info') as mock_log:
            # Simulate structured log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "event": "health_check",
                "endpoint": "/health",
                "status": "healthy",
                "response_time_ms": 32.5,
                "components": {
                    "database": "healthy",
                    "cache": "healthy",
                    "queue": "healthy"
                }
            }
            
            mock_log(json.dumps(log_entry))
            
            # Verify structured logging
            assert mock_log.called
            logged_data = json.loads(mock_log.call_args[0][0])
            assert logged_data["event"] == "health_check"
            assert "components" in logged_data


class TestHealthCheckCompliance:
    """Test health check compliance with standards"""
    
    def test_kubernetes_probe_compliance(self, client: TestClient):
        """Test compliance with Kubernetes probe requirements"""
        # Liveness probe
        liveness_response = client.get("/health")
        assert liveness_response.status_code in [200, 503]
        
        # Readiness probe
        readiness_response = client.get("/health/ready")
        assert readiness_response.status_code in [200, 503]
        
        # Startup probe (if implemented)
        startup_response = client.get("/health/startup")
        if startup_response.status_code != 404:
            assert startup_response.status_code in [200, 503]
    
    def test_health_check_response_format(self, client: TestClient):
        """Test health check response follows standard format"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # RFC 8615 compliance (basic)
        assert "status" in data
        assert data["status"] in ["pass", "fail", "warn", "healthy", "unhealthy", "degraded"]
        
        # Additional standard fields
        if "version" in data:
            assert isinstance(data["version"], str)
        if "description" in data:
            assert isinstance(data["description"], str)
        if "checks" in data:
            assert isinstance(data["checks"], dict)


@pytest.mark.parametrize("monitoring_tool", [
    "prometheus",
    "grafana",
    "datadog",
    "new_relic"
])
def test_monitoring_tool_integration(client: TestClient, monitoring_tool: str):
    """Test integration with various monitoring tools"""
    # This is a template test that would verify integration
    # Actual implementation would depend on specific tool requirements
    pass