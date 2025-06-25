
"""
Trades API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
from datetime import datetime, timedelta


class TestTradesAPI:
    """Test trades endpoints"""

    def test_create_trade_success(self, client, auth_headers, sample_trade_data):
        """Test successful trade creation"""
        with patch('backend.api.v1.trades.service.TradeService.create_trade') as mock_create:
            mock_create.return_value = {
                "id": "trade-123",
                **sample_trade_data,
                "user_id": "test-user-123",
                "created_at": datetime.now().isoformat()
            }
            
            response = client.post(
                "/api/v1/trades/", 
                json=sample_trade_data, 
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["data"]["symbol"] == sample_trade_data["symbol"]
            assert data["data"]["direction"] == sample_trade_data["direction"]

    def test_create_trade_unauthorized(self, client, sample_trade_data):
        """Test trade creation without authentication"""
        response = client.post("/api/v1/trades/", json=sample_trade_data)
        assert response.status_code == 401

    def test_create_trade_invalid_data(self, client, auth_headers):
        """Test trade creation with invalid data"""
        invalid_trade = {
            "symbol": "",  # Empty symbol
            "direction": "invalid",  # Invalid direction
            "quantity": -10,  # Negative quantity
            "entry_price": 0  # Zero price
        }
        
        response = client.post("/api/v1/trades/", json=invalid_trade, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_get_trades_success(self, client, auth_headers):
        """Test successful trades retrieval"""
        mock_trades = [
            {
                "id": "trade-1",
                "symbol": "AAPL",
                "direction": "long",
                "quantity": 100,
                "entry_price": 150.0,
                "pnl": 500.0,
                "user_id": "test-user-123"
            },
            {
                "id": "trade-2",
                "symbol": "TSLA",
                "direction": "short",
                "quantity": 50,
                "entry_price": 800.0,
                "pnl": -200.0,
                "user_id": "test-user-123"
            }
        ]
        
        with patch('backend.api.v1.trades.service.TradeService.get_trades') as mock_get:
            mock_get.return_value = mock_trades
            
            response = client.get("/api/v1/trades/", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 2
            assert data["data"][0]["symbol"] == "AAPL"

    def test_get_trades_with_filters(self, client, auth_headers):
        """Test trades retrieval with query filters"""
        with patch('backend.api.v1.trades.service.TradeService.get_trades') as mock_get:
            mock_get.return_value = []
            
            response = client.get(
                "/api/v1/trades/?symbol=AAPL&min_pnl=100&limit=50",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            # Verify filter parameters were passed to service
            mock_get.assert_called_once()

    def test_get_trades_pagination(self, client, auth_headers):
        """Test trades pagination"""
        with patch('backend.api.v1.trades.service.TradeService.get_trades') as mock_get:
            mock_get.return_value = []
            
            response = client.get(
                "/api/v1/trades/?skip=10&limit=20",
                headers=auth_headers
            )
            
            assert response.status_code == 200

    def test_get_trade_by_id_success(self, client, auth_headers):
        """Test getting a specific trade by ID"""
        trade_id = "trade-123"
        mock_trade = {
            "id": trade_id,
            "symbol": "AAPL",
            "direction": "long",
            "quantity": 100,
            "entry_price": 150.0,
            "user_id": "test-user-123"
        }
        
        with patch('backend.api.v1.trades.service.TradeService.get_trade_by_id') as mock_get:
            mock_get.return_value = mock_trade
            
            response = client.get(f"/api/v1/trades/{trade_id}", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["id"] == trade_id

    def test_get_trade_by_id_not_found(self, client, auth_headers):
        """Test getting non-existent trade"""
        trade_id = "nonexistent-trade"
        
        with patch('backend.api.v1.trades.service.TradeService.get_trade_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get(f"/api/v1/trades/{trade_id}", headers=auth_headers)
            
            assert response.status_code == 404

    def test_update_trade_success(self, client, auth_headers):
        """Test successful trade update"""
        trade_id = "trade-123"
        update_data = {
            "exit_price": 160.0,
            "exit_time": "2024-01-15T16:00:00",
            "notes": "Updated trade"
        }
        
        with patch('backend.api.v1.trades.service.TradeService.update_trade') as mock_update:
            mock_update.return_value = {
                "id": trade_id,
                "symbol": "AAPL",
                "exit_price": 160.0,
                "notes": "Updated trade"
            }
            
            response = client.put(
                f"/api/v1/trades/{trade_id}",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["exit_price"] == 160.0

    def test_delete_trade_success(self, client, auth_headers):
        """Test successful trade deletion"""
        trade_id = "trade-123"
        
        with patch('backend.api.v1.trades.service.TradeService.delete_trade') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/api/v1/trades/{trade_id}", headers=auth_headers)
            
            assert response.status_code == 204

    def test_delete_trade_not_found(self, client, auth_headers):
        """Test deleting non-existent trade"""
        trade_id = "nonexistent-trade"
        
        with patch('backend.api.v1.trades.service.TradeService.delete_trade') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete(f"/api/v1/trades/{trade_id}", headers=auth_headers)
            
            assert response.status_code == 404


class TestTradesAnalytics:
    """Test trades analytics endpoints"""

    def test_get_analytics_success(self, client, auth_headers):
        """Test successful analytics retrieval"""
        mock_analytics = {
            "total_trades": 50,
            "winning_trades": 30,
            "losing_trades": 20,
            "win_rate": 60.0,
            "total_pnl": 5000.0,
            "profit_factor": 2.5,
            "max_drawdown": 1500.0,
            "sharpe_ratio": 1.8
        }
        
        with patch('backend.api.v1.trades.service.TradeService.get_analytics') as mock_analytics_service:
            mock_analytics_service.return_value = mock_analytics
            
            response = client.get("/api/v1/trades/analytics", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total_trades"] == 50
            assert data["data"]["win_rate"] == 60.0

    def test_get_analytics_with_date_range(self, client, auth_headers):
        """Test analytics with date range filter"""
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        with patch('backend.api.v1.trades.service.TradeService.get_analytics') as mock_analytics:
            mock_analytics.return_value = {"total_trades": 10}
            
            response = client.get(
                f"/api/v1/trades/analytics?start_date={start_date}&end_date={end_date}",
                headers=auth_headers
            )
            
            assert response.status_code == 200

    def test_get_performance_summary(self, client, auth_headers):
        """Test performance summary endpoint"""
        mock_summary = {
            "daily_pnl": [100, -50, 200, 75],
            "monthly_returns": [{"month": "2024-01", "pnl": 1500}],
            "symbol_performance": [
                {"symbol": "AAPL", "trades": 10, "pnl": 1000},
                {"symbol": "TSLA", "trades": 5, "pnl": -200}
            ]
        }
        
        with patch('backend.api.v1.trades.service.TradeService.get_performance_summary') as mock_summary_service:
            mock_summary_service.return_value = mock_summary
            
            response = client.get("/api/v1/trades/performance", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "daily_pnl" in data["data"]
            assert "symbol_performance" in data["data"]


class TestBulkTradeOperations:
    """Test bulk trade operations"""

    def test_bulk_create_trades_success(self, client, auth_headers):
        """Test successful bulk trade creation"""
        bulk_trades = [
            {
                "symbol": "AAPL",
                "direction": "long",
                "quantity": 100,
                "entry_price": 150.0,
                "entry_time": "2024-01-15T10:30:00"
            },
            {
                "symbol": "TSLA",
                "direction": "short",
                "quantity": 50,
                "entry_price": 800.0,
                "entry_time": "2024-01-16T09:30:00"
            }
        ]
        
        with patch('backend.api.v1.trades.service.TradeService.bulk_create_trades') as mock_bulk:
            mock_bulk.return_value = {
                "success": True,
                "created_count": 2,
                "failed_count": 0,
                "errors": []
            }
            
            response = client.post(
                "/api/v1/trades/bulk",
                json={"trades": bulk_trades},
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["data"]["created_count"] == 2

    def test_bulk_create_trades_partial_failure(self, client, auth_headers):
        """Test bulk trade creation with some failures"""
        bulk_trades = [
            {
                "symbol": "AAPL",
                "direction": "long",
                "quantity": 100,
                "entry_price": 150.0,
                "entry_time": "2024-01-15T10:30:00"
            },
            {
                "symbol": "",  # Invalid trade
                "direction": "invalid",
                "quantity": -50,
                "entry_price": 0
            }
        ]
        
        with patch('backend.api.v1.trades.service.TradeService.bulk_create_trades') as mock_bulk:
            mock_bulk.return_value = {
                "success": True,
                "created_count": 1,
                "failed_count": 1,
                "errors": ["Trade 2: Invalid symbol and direction"]
            }
            
            response = client.post(
                "/api/v1/trades/bulk",
                json={"trades": bulk_trades},
                headers=auth_headers
            )
            
            assert response.status_code == 207  # Multi-status
            data = response.json()
            assert data["data"]["created_count"] == 1
            assert data["data"]["failed_count"] == 1


@pytest.mark.integration
class TestTradesIntegration:
    """Integration tests for trades workflow"""

    def test_complete_trade_lifecycle(self, client, auth_headers, sample_trade_data):
        """Test complete trade lifecycle: create -> read -> update -> delete"""
        # Create trade
        with patch('backend.api.v1.trades.service.TradeService.create_trade') as mock_create, \
             patch('backend.api.v1.trades.service.TradeService.get_trade_by_id') as mock_get, \
             patch('backend.api.v1.trades.service.TradeService.update_trade') as mock_update, \
             patch('backend.api.v1.trades.service.TradeService.delete_trade') as mock_delete:
            
            # 1. Create
            trade_id = "lifecycle-trade-123"
            mock_create.return_value = {"id": trade_id, **sample_trade_data}
            
            create_response = client.post(
                "/api/v1/trades/",
                json=sample_trade_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            
            # 2. Read
            mock_get.return_value = {"id": trade_id, **sample_trade_data}
            
            get_response = client.get(f"/api/v1/trades/{trade_id}", headers=auth_headers)
            assert get_response.status_code == 200
            
            # 3. Update
            update_data = {"exit_price": 160.0, "notes": "Updated"}
            mock_update.return_value = {"id": trade_id, **sample_trade_data, **update_data}
            
            update_response = client.put(
                f"/api/v1/trades/{trade_id}",
                json=update_data,
                headers=auth_headers
            )
            assert update_response.status_code == 200
            
            # 4. Delete
            mock_delete.return_value = True
            
            delete_response = client.delete(f"/api/v1/trades/{trade_id}", headers=auth_headers)
            assert delete_response.status_code == 204
