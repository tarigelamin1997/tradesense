import pytest
import os
import sys
from unittest.mock import Mock
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.core.db.session import get_db
import shutil

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Delete test.db before and after the test session."""
    db_path = Path("./test.db")
    if db_path.exists():
        db_path.unlink()
    yield
    if db_path.exists():
        db_path.unlink()

@pytest.fixture(scope="session")
def setup_models_and_tables(request):
    """Import models and create/drop tables only once per session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    from backend.core.db.session import Base
    import backend.models.user, backend.models.trade, backend.models.trading_account, backend.models.feature_request, backend.models.tag, backend.models.portfolio, backend.models.playbook, backend.models.trade_review, backend.models.trade_note, backend.models.strategy, backend.models.mental_map, backend.models.pattern_cluster, backend.models.milestone, backend.models.daily_emotion_reflection
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    def teardown():
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
    request.addfinalizer(teardown)
    return engine

@pytest.fixture(scope="session")
def test_engine(setup_models_and_tables):
    """Provide the test database engine (session-scoped)."""
    return setup_models_and_tables

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session (function-scoped)."""
    from backend.core.db.session import Base
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    from backend.main import app
    def override_get_db():
        yield test_db  # do not close here; let the test_db fixture handle closing
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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    os.environ.pop("TESTING", None)
    os.environ.pop("DATABASE_URL", None)
