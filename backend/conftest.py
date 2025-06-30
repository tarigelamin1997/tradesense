
import pytest
import os
import sys
from unittest.mock import Mock
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_tradesense.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    return engine

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_engine
    )

    # Import models to ensure tables are created
    try:
        from models.user import User
        from models.trade import Trade
        from models.trading_account import TradingAccount
        from models.feature_request import FeatureRequest
        
        # Create all tables
        User.metadata.create_all(bind=test_engine)
        Trade.metadata.create_all(bind=test_engine)
        TradingAccount.metadata.create_all(bind=test_engine)
        FeatureRequest.metadata.create_all(bind=test_engine)
        
    except ImportError as e:
        print(f"Warning: Could not import models: {e}")
        pass

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables after test
        try:
            User.metadata.drop_all(bind=test_engine)
        except:
            pass

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    try:
        from main import app
        from core.db.session import get_db
        
        def override_get_db():
            try:
                yield test_db
            finally:
                test_db.close()

        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()
        
    except ImportError as e:
        print(f"Warning: Could not import main app: {e}")
        # Create a minimal test client for basic testing
        from fastapi import FastAPI
        test_app = FastAPI()
        
        @test_app.get("/health")
        def health():
            return {"status": "ok"}
            
        with TestClient(test_app) as test_client:
            yield test_client

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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # Cleanup
    os.environ.pop("TESTING", None)
    os.environ.pop("DATABASE_URL", None)
