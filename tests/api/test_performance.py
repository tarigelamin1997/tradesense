"""
Performance API Tests

Test suite for performance monitoring and optimization endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from backend.main import app
from backend.core.query_optimizer import query_optimizer
from backend.core.async_manager import task_manager

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Get authentication headers for testing"""
    # Login to get token
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestPerformanceMetrics:
    """Test performance metrics endpoints"""
    
    def test_get_performance_metrics(self, auth_headers):
        """Test getting performance metrics"""
        response = client.get("/api/v1/performance/metrics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "query_performance" in data["data"]
        assert "task_metrics" in data["data"]
        assert "cache_performance" in data["data"]
        assert "health_indicators" in data["data"]
        assert "timestamp" in data["data"]
    
    def test_get_slow_queries(self, auth_headers):
        """Test getting slow queries list"""
        response = client.get("/api/v1/performance/slow-queries?limit=5", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "slow_queries" in data["data"]
        assert "total_slow_queries" in data["data"]
        assert isinstance(data["data"]["slow_queries"], list)
    
    def test_clear_cache_all(self, auth_headers):
        """Test clearing all cache"""
        # Add some test data to cache
        query_optimizer.set_cached_result("test_key", "test_value", 300)
        cache_size_before = len(query_optimizer.query_cache)
        
        response = client.post("/api/v1/performance/cache/clear", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["cache_cleared"] > 0
        assert data["data"]["remaining_cache_size"] == 0
    
    def test_clear_cache_pattern(self, auth_headers):
        """Test clearing cache with pattern"""
        # Add test data
        query_optimizer.set_cached_result("analytics_test", "value1", 300)
        query_optimizer.set_cached_result("trades_test", "value2", 300)
        query_optimizer.set_cached_result("other_data", "value3", 300)
        
        response = client.post(
            "/api/v1/performance/cache/clear?pattern=analytics", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["pattern_used"] == "analytics"
        # Should still have other cache entries
        assert data["data"]["remaining_cache_size"] > 0

class TestTaskManagement:
    """Test background task management endpoints"""
    
    def test_get_task_status(self, auth_headers):
        """Test getting task status"""
        response = client.get("/api/v1/performance/tasks", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "tasks" in data["data"]
        assert "total_tasks" in data["data"]
        assert isinstance(data["data"]["tasks"], list)
    
    def test_get_task_status_with_filter(self, auth_headers):
        """Test getting task status with status filter"""
        response = client.get(
            "/api/v1/performance/tasks?status=completed&limit=10", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["status_filter"] == "completed"
    
    def test_get_task_status_invalid_filter(self, auth_headers):
        """Test getting task status with invalid status filter"""
        response = client.get(
            "/api/v1/performance/tasks?status=invalid_status", 
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_cancel_task(self, auth_headers):
        """Test cancelling a task"""
        # Create a test task
        task_id = task_manager.create_task(lambda: "test", task_id="test_cancel_task")
        
        response = client.delete(
            f"/api/v1/performance/tasks/{task_id}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["cancelled"] is True
    
    def test_cancel_nonexistent_task(self, auth_headers):
        """Test cancelling a non-existent task"""
        response = client.delete(
            "/api/v1/performance/tasks/nonexistent_task", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "cancelled" not in data["data"]

class TestOptimizationRecommendations:
    """Test optimization recommendations endpoint"""
    
    def test_get_optimization_recommendations(self, auth_headers):
        """Test getting optimization recommendations"""
        response = client.get(
            "/api/v1/performance/optimization/recommendations", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "recommendations" in data["data"]
        assert "total_recommendations" in data["data"]
        assert "critical_count" in data["data"]
        assert "high_count" in data["data"]
        assert "medium_count" in data["data"]
        assert isinstance(data["data"]["recommendations"], list)
    
    @patch('backend.core.query_optimizer.get_performance_metrics')
    def test_recommendations_with_slow_queries(self, mock_metrics, auth_headers):
        """Test recommendations when slow queries are detected"""
        mock_metrics.return_value = {
            "average_query_time": 2.5,
            "cache_hit_rate": 0.1,
            "slowest_queries": [("slow_query", 3.0)],
            "total_queries": 100
        }
        
        response = client.get(
            "/api/v1/performance/optimization/recommendations", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have recommendations for slow queries
        recommendations = data["data"]["recommendations"]
        assert len(recommendations) > 0
        
        # Check for critical recommendation
        critical_recs = [r for r in recommendations if r["priority"] == "critical"]
        assert len(critical_recs) > 0

class TestPerformanceIntegration:
    """Integration tests for performance monitoring"""
    
    def test_performance_metrics_consistency(self, auth_headers):
        """Test that performance metrics are consistent across calls"""
        response1 = client.get("/api/v1/performance/metrics", headers=auth_headers)
        response2 = client.get("/api/v1/performance/metrics", headers=auth_headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()["data"]
        data2 = response2.json()["data"]
        
        # Cache size should be consistent
        assert data1["cache_performance"]["cache_size"] == data2["cache_performance"]["cache_size"]
    
    def test_cache_clear_affects_metrics(self, auth_headers):
        """Test that clearing cache affects performance metrics"""
        # Get initial metrics
        initial_response = client.get("/api/v1/performance/metrics", headers=auth_headers)
        initial_cache_size = initial_response.json()["data"]["cache_performance"]["cache_size"]
        
        # Clear cache
        client.post("/api/v1/performance/cache/clear", headers=auth_headers)
        
        # Get metrics again
        final_response = client.get("/api/v1/performance/metrics", headers=auth_headers)
        final_cache_size = final_response.json()["data"]["cache_performance"]["cache_size"]
        
        # Cache should be cleared
        assert final_cache_size == 0
    
    def test_unauthorized_access(self):
        """Test that performance endpoints require authentication"""
        endpoints = [
            "/api/v1/performance/metrics",
            "/api/v1/performance/slow-queries",
            "/api/v1/performance/cache/clear",
            "/api/v1/performance/tasks",
            "/api/v1/performance/optimization/recommendations"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint) if endpoint != "/api/v1/performance/cache/clear" else client.post(endpoint)
            assert response.status_code == 401

class TestPerformanceEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_large_limit_parameter(self, auth_headers):
        """Test handling of large limit parameter"""
        response = client.get("/api/v1/performance/slow-queries?limit=1000", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not return more than reasonable limit
        assert len(data["data"]["slow_queries"]) <= 100
    
    def test_invalid_pattern_parameter(self, auth_headers):
        """Test handling of invalid pattern parameter"""
        response = client.post(
            "/api/v1/performance/cache/clear?pattern=invalid*pattern", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Should handle gracefully
    
    @patch('backend.core.query_optimizer.get_performance_metrics')
    def test_metrics_calculation_error(self, mock_metrics, auth_headers):
        """Test handling of metrics calculation errors"""
        mock_metrics.side_effect = Exception("Metrics calculation failed")
        
        response = client.get("/api/v1/performance/metrics", headers=auth_headers)
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data 