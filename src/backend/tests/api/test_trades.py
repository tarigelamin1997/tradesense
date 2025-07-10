import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime
from models.user import User
from core.db.session import SessionLocal
from core.security import SecurityManager

class TestTradesAPI:
    TEST_USER_ID = "test_user_123"
    TEST_USER_EMAIL = "test@example.com"
    TEST_USER_TOKEN = SecurityManager.create_access_token(
        data={"user_id": TEST_USER_ID, "email": TEST_USER_EMAIL}
    )
    TEST_USER_HEADERS = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}

    def test_create_trade_success(self, client, test_db, test_user):
        """Test successful trade creation"""
        from models.user import User
        user = test_db.query(User).filter(User.id == "test_user_123").first()
        print(f"[DEBUG][test_create_trade_success] User in DB at test start: {user}")
        sample_trade_data = {
            "entry_price": 150.0,
            "entry_time": "2024-01-01T10:00:00",
            "exit_price": 155.0,
            "exit_time": "2024-01-01T15:00:00",
            "symbol": "AAPL",
            "position": "long",
            "size": 10,
            "strategy": "momentum",
            "direction": "long",
            "quantity": 10
        }
        response = client.post("/api/v1/trades/", json=sample_trade_data, headers=self.TEST_USER_HEADERS)
        assert response.status_code == 201

    def test_get_trades_list(self, client, test_db, test_user):
        """Test getting trades list"""
        from models.user import User
        user = test_db.query(User).filter(User.id == "test_user_123").first()
        print(f"[DEBUG][test_get_trades_list] User in DB at test start: {user}")
        response = client.get("/api/v1/trades/", headers=self.TEST_USER_HEADERS)
        assert response.status_code == 200

    def test_create_trade_without_auth(self, client, test_db):
        """Test creating trade without authentication"""
        sample_trade_data = {
            "entry_price": 150.0,
            "entry_time": "2024-01-01T10:00:00",
            "exit_price": 155.0,
            "exit_time": "2024-01-01T15:00:00",
            "symbol": "AAPL",
            "position": "long",
            "size": 10,
            "strategy": "momentum",
            "direction": "long",
            "quantity": 10
        }
        response = client.post("/api/v1/trades/", json=sample_trade_data)
        assert response.status_code == 401

    def test_create_trade_invalid_data(self, client, test_db, test_user):
        """Test creating trade with invalid data"""
        from models.user import User
        user = test_db.query(User).filter(User.id == "test_user_123").first()
        print(f"[DEBUG][test_create_trade_invalid_data] User in DB at test start: {user}")
        invalid_data = {
            "symbol": "AAPL",
            "entry_price": -100,  # Invalid negative price
            "size": 0,  # Invalid zero size
            "position": "long",
            "direction": "long",
            "quantity": 0
        }
        response = client.post("/api/v1/trades/", json=invalid_data, headers=self.TEST_USER_HEADERS)
        assert response.status_code == 422

    def test_get_trade_by_id(self, client, test_db, test_user):
        """Test getting specific trade by ID"""
        from models.user import User
        user = test_db.query(User).filter(User.id == "test_user_123").first()
        print(f"[DEBUG][test_get_trade_by_id] User in DB at test start: {user}")
        sample_trade_data = {
            "entry_price": 150.0,
            "entry_time": "2024-01-01T10:00:00",
            "exit_price": 155.0,
            "exit_time": "2024-01-01T15:00:00",
            "symbol": "AAPL",
            "position": "long",
            "size": 10,
            "strategy": "momentum",
            "direction": "long",
            "quantity": 10
        }
        create_response = client.post("/api/v1/trades/", json=sample_trade_data, headers=self.TEST_USER_HEADERS)
        assert create_response.status_code == 201
        data = create_response.json()
        trade_id = data.get("id") or data.get("trade_id")
        if not trade_id:
            print("[DEBUG] Trade creation response:", data)
        assert trade_id is not None
        response = client.get(f"/api/v1/trades/{trade_id}", headers=self.TEST_USER_HEADERS)
        assert response.status_code == 200