import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime

class TestTradesAPI:

    @patch('api.deps.get_current_user')
    def test_create_trade_success(self, mock_get_user, client, sample_trade_data):
        """Test successful trade creation"""
        # Mock current user
        mock_user = Mock()
        mock_user.id = "test_user_id"
        mock_get_user.return_value = mock_user

        headers = {"Authorization": "Bearer fake_token"}
        response = client.post("/api/v1/trades/", json=sample_trade_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == sample_trade_data["symbol"]
        assert data["entry_price"] == sample_trade_data["entry_price"]
        assert data["quantity"] == sample_trade_data["quantity"]

    @patch('api.deps.get_current_user')
    def test_get_trades_list(self, mock_get_user, client):
        """Test getting trades list"""
        # Mock current user
        mock_user = Mock()
        mock_user.id = "test_user_id"
        mock_get_user.return_value = mock_user

        headers = {"Authorization": "Bearer fake_token"}
        response = client.get("/api/v1/trades/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_trade_without_auth(self, client, sample_trade_data):
        """Test creating trade without authentication"""
        response = client.post("/api/v1/trades/", json=sample_trade_data)

        assert response.status_code == 401

    @patch('api.deps.get_current_user')
    def test_create_trade_invalid_data(self, mock_get_user, client):
        """Test creating trade with invalid data"""
        # Mock current user
        mock_user = Mock()
        mock_user.id = "test_user_id"
        mock_get_user.return_value = mock_user

        invalid_data = {
            "symbol": "AAPL",
            "entry_price": -100,  # Invalid negative price
            "quantity": 0  # Invalid zero quantity
        }

        headers = {"Authorization": "Bearer fake_token"}
        response = client.post("/api/v1/trades/", json=invalid_data, headers=headers)

        assert response.status_code == 422  # Validation error

    @patch('api.deps.get_current_user')
    def test_get_trade_by_id(self, mock_get_user, client, sample_trade_data):
        """Test getting specific trade by ID"""
        # Mock current user
        mock_user = Mock()
        mock_user.id = "test_user_id"
        mock_get_user.return_value = mock_user

        headers = {"Authorization": "Bearer fake_token"}

        # Create a trade first
        create_response = client.post("/api/v1/trades/", json=sample_trade_data, headers=headers)
        trade_id = create_response.json()["id"]

        # Get the trade
        response = client.get(f"/api/v1/trades/{trade_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == trade_id
        assert data["symbol"] == sample_trade_data["symbol"]