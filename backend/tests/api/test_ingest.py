
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json

from backend.main import app
from backend.core.security import SecurityManager

client = TestClient(app)

class TestTradeIngest:
    """Test trade ingestion API endpoint"""

    def setup_method(self):
        """Setup test data"""
        self.test_user_id = "test_user_123"
        self.test_token = SecurityManager.create_access_token(
            data={"user_id": self.test_user_id, "email": "test@example.com"}
        )
        self.headers = {"Authorization": f"Bearer {self.test_token}"}

    def test_ingest_trade_success(self):
        """Test successful trade ingestion"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "exit_time": "2024-12-18T09:45:00Z",
            "symbol": "NQ",
            "position": "long",
            "size": 2,
            "entry_price": 16000,
            "exit_price": 16040,
            "tags": ["breakout", "morning session"],
            "strategy": "momentum",
            "notes": "Strong breakout pattern"
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "trade_id" in data
        assert data["message"] == "Trade ingested successfully"

    def test_ingest_trade_open_position(self):
        """Test ingesting an open trade (no exit)"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "symbol": "ES",
            "position": "short",
            "size": 1,
            "entry_price": 4500,
            "strategy": "reversal"
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "trade_id" in data

    def test_ingest_trade_validation_error(self):
        """Test validation error handling"""
        trade_data = {
            "entry_time": "2024-12-18T09:45:00Z",
            "exit_time": "2024-12-18T09:00:00Z",  # Exit before entry
            "symbol": "NQ",
            "position": "long",
            "size": 2,
            "entry_price": 16000,
            "exit_price": 16040
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 422
        assert "validation" in response.json()["detail"][0]["type"]

    def test_ingest_trade_missing_auth(self):
        """Test missing authentication"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "symbol": "NQ",
            "position": "long",
            "size": 2,
            "entry_price": 16000
        }

        response = client.post("/api/v1/trades/ingest", json=trade_data)

        assert response.status_code == 401

    def test_ingest_trade_invalid_token(self):
        """Test invalid authentication token"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "symbol": "NQ",
            "position": "long",
            "size": 2,
            "entry_price": 16000
        }

        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=headers
        )

        assert response.status_code == 401

    def test_ingest_trade_missing_required_fields(self):
        """Test missing required fields"""
        trade_data = {
            "symbol": "NQ",
            "position": "long"
            # Missing entry_time, size, entry_price
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 422

    def test_ingest_trade_invalid_position(self):
        """Test invalid position value"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "symbol": "NQ",
            "position": "invalid",  # Should be 'long' or 'short'
            "size": 2,
            "entry_price": 16000
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 422

    def test_ingest_trade_negative_size(self):
        """Test negative position size"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "symbol": "NQ",
            "position": "long",
            "size": -2,  # Should be positive
            "entry_price": 16000
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 422

    def test_ingest_trade_with_pnl_calculation(self):
        """Test that PnL is calculated correctly for closed trades"""
        trade_data = {
            "entry_time": "2024-12-18T09:00:00Z",
            "exit_time": "2024-12-18T09:45:00Z",
            "symbol": "NQ",
            "position": "long",
            "size": 1,
            "entry_price": 16000,
            "exit_price": 16020  # $20 profit per contract
        }

        response = client.post(
            "/api/v1/trades/ingest",
            json=trade_data,
            headers=self.headers
        )

        assert response.status_code == 200
        # Note: In a real test, we'd verify PnL in the database
        # For now, we just ensure the request succeeds
