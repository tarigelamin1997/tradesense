"""
Test trade-related endpoints and functionality
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.models.trade import Trade


class TestTradeEndpoints:
    """Test trade CRUD endpoints"""

    def test_create_trade_success(self, client, auth_headers, test_user):
        """Test successful trade creation"""
        trade_data = {
            "symbol": "AAPL",
            "direction": "long",
            "quantity": 100.0,
            "entry_price": 150.0,
            "exit_price": 155.0,
            "entry_time": "2024-01-15T10:30:00",
            "exit_time": "2024-01-15T15:30:00",
            "strategy_tag": "momentum",
            "confidence_score": 8,
            "notes": "Test trade"
        }

        response = client.post("/api/v1/trades/", json=trade_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == trade_data["symbol"]
        assert data["user_id"] == str(test_user.id)
        assert "id" in data

    def test_create_trade_invalid_data(self, client, auth_headers):
        """Test trade creation with invalid data"""
        trade_data = {
            "symbol": "",  # Invalid empty symbol
            "direction": "invalid_direction",
            "quantity": -100.0,  # Invalid negative quantity
        }

        response = client.post("/api/v1/trades/", json=trade_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_get_trades_list(self, client, auth_headers, sample_trade_record):
        """Test retrieving trades list"""
        response = client.get("/api/v1/trades/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert len(data["trades"]) >= 1
        assert data["trades"][0]["symbol"] == sample_trade_record.symbol

    def test_get_trade_by_id(self, client, auth_headers, sample_trade_record):
        """Test retrieving specific trade by ID"""
        response = client.get(f"/api/v1/trades/{sample_trade_record.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_trade_record.id
        assert data["symbol"] == sample_trade_record.symbol

    def test_get_nonexistent_trade(self, client, auth_headers):
        """Test retrieving non-existent trade"""
        response = client.get("/api/v1/trades/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_update_trade(self, client, auth_headers, sample_trade_record):
        """Test updating trade"""
        update_data = {
            "notes": "Updated test trade",
            "confidence_score": 9
        }

        response = client.put(
            f"/api/v1/trades/{sample_trade_record.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == update_data["notes"]
        assert data["confidence_score"] == update_data["confidence_score"]

    def test_delete_trade(self, client, auth_headers, sample_trade_record):
        """Test deleting trade"""
        response = client.delete(f"/api/v1/trades/{sample_trade_record.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify trade is deleted
        response = client.get(f"/api/v1/trades/{sample_trade_record.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_trade_filtering(self, client, auth_headers, db_session, test_user):
        """Test trade filtering functionality"""
        # Create multiple trades
        trades = [
            Trade(
                user_id=test_user.id,
                symbol="AAPL",
                direction="long",
                quantity=100,
                entry_price=150,
                exit_price=155,
                entry_time=datetime.now() - timedelta(days=1),
                exit_time=datetime.now() - timedelta(days=1, hours=-5)
            ),
            Trade(
                user_id=test_user.id,
                symbol="TSLA",
                direction="short",
                quantity=50,
                entry_price=800,
                exit_price=790,
                entry_time=datetime.now() - timedelta(days=2),
                exit_time=datetime.now() - timedelta(days=2, hours=-3)
            )
        ]

        for trade in trades:
            db_session.add(trade)
        db_session.commit()

        # Test symbol filter
        response = client.get("/api/v1/trades/?symbol=AAPL", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "AAPL"

        # Test direction filter
        response = client.get("/api/v1/trades/?direction=short", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["direction"] == "short"

    def test_trade_pagination(self, client, auth_headers, db_session, test_user):
        """Test trade pagination"""
        # Create multiple trades
        for i in range(15):
            trade = Trade(
                user_id=test_user.id,
                symbol=f"TEST{i}",
                direction="long",
                quantity=100,
                entry_price=100 + i,
                exit_price=105 + i,
                entry_time=datetime.now() - timedelta(days=i),
                exit_time=datetime.now() - timedelta(days=i, hours=-5)
            )
            db_session.add(trade)
        db_session.commit()

        # Test first page
        response = client.get("/api/v1/trades/?page=1&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 10
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["total_pages"] >= 2

    def test_unauthorized_access_other_user_trade(self, client, db_session, test_user_data):
        """Test that users cannot access other users' trades"""
        # Create another user and their trade
        from backend.models.user import User
        from backend.core.security import SecurityManager

        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash=SecurityManager.hash_password("password123")
        )
        db_session.add(other_user)
        db_session.commit()

        other_trade = Trade(
            user_id=other_user.id,
            symbol="RESTRICTED",
            direction="long",
            quantity=100,
            entry_price=100,
            exit_price=105,
            entry_time=datetime.now(),
            exit_time=datetime.now()
        )
        db_session.add(other_trade)
        db_session.commit()

        # Create token for first user
        token_data = {"user_id": str(other_user.id), "username": other_user.username}
        token = SecurityManager.create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access the trade - should fail
        response = client.get(f"/api/v1/trades/{other_trade.id}", headers=headers)
        assert response.status_code in [403, 404]  # Forbidden or Not Found