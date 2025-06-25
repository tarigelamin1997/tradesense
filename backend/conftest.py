
"""
Test configuration and shared fixtures for TradeSense backend
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
from unittest.mock import Mock, patch

from backend.main import app
from backend.core.config import settings
from backend.core.security import SecurityManager
from backend.db.connection import get_db, Base
from backend.models.trade import Trade


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
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
    app.dependency_overrides[get_db] = override_get_db
    
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
def test_user_token(test_user_data):
    """Create a test user token"""
    token_data = {
        "user_id": "test-user-123",
        "username": test_user_data["username"],
        "email": test_user_data["email"]
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
def sample_trade_record(db_session, sample_trade_data):
    """Create a sample trade record in the database"""
    trade = Trade(
        user_id="test-user-123",
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


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch.object(settings, 'debug', True), \
         patch.object(settings, 'jwt_secret', 'test-secret-key'), \
         patch.object(settings, 'jwt_expiration_hours', 1):
        yield settings


# Helper functions for tests
def create_test_user(db_session, user_data=None):
    """Helper to create a test user in the database"""
    if user_data is None:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": SecurityManager.hash_password("TestPassword123")
        }
    
    # Mock user creation since we don't have User model yet
    # This would be replaced with actual User model creation
    return {"id": "test-user-123", **user_data}


def assert_error_response(response, status_code, error_type=None):
    """Helper to assert error responses"""
    assert response.status_code == status_code
    data = response.json()
    assert "error" in data
    if error_type:
        assert data["error"] == error_type
