import pytest
import os
import sys
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from core.db.session import get_db
from main import app

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_tradesense.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    return engine

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create tables
    from models.user import User
    from models.trade import Trade
    from models.trading_account import TradingAccount

    User.metadata.create_all(bind=test_engine)
    Trade.metadata.create_all(bind=test_engine)
    TradingAccount.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables
        User.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return {
        "symbol": "AAPL",
        "entry_price": 150.00,
        "exit_price": 155.00,
        "quantity": 100,
        "side": "long",
        "entry_time": "2024-01-01T10:00:00",
        "exit_time": "2024-01-01T15:00:00",
        "pnl": 500.00
    }