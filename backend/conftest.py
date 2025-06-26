
"""
Test configuration and shared fixtures for TradeSense backend
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import tempfile
import os
from unittest.mock import Mock, patch

from backend.main import app
from backend.core.config import settings
from backend.core.security import SecurityManager
from backend.db.connection import get_db, Base
from backend.models.trade import Trade
from backend.models.user import User


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123"
    }


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user in the database"""
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password_hash=SecurityManager.hash_password(test_user_data["password"])
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user):
    """Create a test user token"""
    token_data = {
        "user_id": str(test_user.id),
        "username": test_user.username,
        "email": test_user.email
    }
    return SecurityManager.create_access_token(token_data)


@pytest.fixture
def auth_headers(test_user_token):
    """Create authorization headers for testing"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return {
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


@pytest.fixture
def sample_trade_record(db_session, test_user, sample_trade_data):
    """Create a sample trade record in the database"""
    trade = Trade(
        user_id=test_user.id,
        **sample_trade_data
    )
    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)
    return trade


@pytest.fixture
def mock_file_upload():
    """Mock file upload for testing"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
        f.write("symbol,entry_time,exit_time,entry_price,exit_price,quantity,direction,pnl\n")
        f.write("AAPL,2024-01-15 10:30:00,2024-01-15 15:30:00,150.0,155.0,100,long,500.0\n")
        f.write("TSLA,2024-01-16 09:30:00,2024-01-16 16:00:00,800.0,790.0,10,long,-100.0\n")
        f.flush()

        yield f.name

    # Cleanup
    try:
        os.unlink(f.name)
    except:
        pass


# Helper functions for tests
def assert_error_response(response, status_code, error_type=None):
    """Helper to assert error responses"""
    assert response.status_code == status_code
    data = response.json()
    assert "error" in data or "detail" in data
    if error_type and "error" in data:
        assert data["error"] == error_type
