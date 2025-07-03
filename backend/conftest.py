import pytest
import os
import sys
import asyncio
from unittest.mock import Mock
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import shutil
import time

# Add the backend directory to Python path FIRST
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Now import backend modules
# from backend.core.db.session import get_db

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_tradesense.db"

# Patch event loop policy for Windows compatibility (RuntimeError: no running event loop)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Delete test.db before and after the test session."""
    db_path = Path("./test.db")
    
    # Clean up before tests
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            # On Windows, file might be locked - wait and retry
            time.sleep(1)
            try:
                db_path.unlink()
            except PermissionError:
                print(f"Warning: Could not delete {db_path} before tests")
    
    yield
    
    # Clean up after tests
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            # On Windows, file might be locked - wait and retry
            time.sleep(1)
            try:
                db_path.unlink()
            except PermissionError:
                print(f"Warning: Could not delete {db_path} after tests")
                # Try to rename instead
                try:
                    db_path.rename(f"{db_path}.old")
                except:
                    pass

@pytest.fixture(scope="session")
def setup_models_and_tables(request):
    """Import models and create/drop tables only once per session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    from backend.core.db.session import Base
    import backend.models.user, backend.models.trade, backend.models.trading_account, backend.models.feature_request, backend.models.tag, backend.models.portfolio, backend.models.playbook, backend.models.trade_review, backend.models.trade_note, backend.models.strategy, backend.models.mental_map, backend.models.pattern_cluster, backend.models.milestone, backend.models.daily_emotion_reflection
    
    # Drop all tables and indexes more aggressively
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not drop all tables: {e}")
        # Try to drop individual tables
        for table in reversed(Base.metadata.sorted_tables):
            try:
                table.drop(engine, checkfirst=True)
            except Exception as table_error:
                print(f"Warning: Could not drop table {table.name}: {table_error}")
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create all tables: {e}")
        # Try to create tables individually
        for table in Base.metadata.sorted_tables:
            try:
                table.create(engine, checkfirst=True)
            except Exception as table_error:
                print(f"Warning: Could not create table {table.name}: {table_error}")
    
    def teardown():
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception as e:
            print(f"Warning: Could not drop tables during teardown: {e}")
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
def test_user(test_db):
    """Ensure the test user exists in the test DB with id 'test_user_123'."""
    from backend.models.user import User
    test_user_id = "test_user_123"
    test_email = "test@example.com"
    test_username = "testuser"
    user = test_db.query(User).filter(
        (User.id == test_user_id) |
        (User.email == test_email) |
        (User.username == test_username)
    ).first()
    if user:
        # If the user exists but has a different id, update it
        if user.id != test_user_id:
            print(f"[DEBUG][test_user fixture] Updating user id from {user.id} to {test_user_id}")
            user.id = test_user_id
            test_db.commit()
            test_db.expire_all()
        print(f"[DEBUG][test_user fixture] Test user already exists: {user.id}")
    else:
        user = User(
            id=test_user_id,
            email=test_email,
            username=test_username,
            hashed_password="testhash",
            first_name="Test",
            last_name="User",
            trading_experience="intermediate",
            preferred_markets="stocks,forex",
            timezone="UTC",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.expire_all()
        print(f"[DEBUG][test_user fixture] Created test user: {user.id} in test database")
    return user

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override."""
    import main_minimal
    from backend.core.db.session import get_db
    def override_get_db():
        yield test_db
    main_minimal.app.dependency_overrides[get_db] = override_get_db
    client = TestClient(main_minimal.app)
    yield client
    main_minimal.app.dependency_overrides.clear()

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongTest123!",
        "first_name": "Test",
        "last_name": "User",
        "trading_experience": "intermediate",
        "preferred_markets": "stocks,forex",
        "timezone": "UTC"
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

@pytest.fixture(scope="session", autouse=True)
def set_app_db_override(test_engine):
    """Set the dependency override for get_db at the start of the test session."""
    import main_minimal
    from backend.core.db.session import get_db
    def override_get_db():
        from backend.conftest import test_db
        yield test_db
    main_minimal.app.dependency_overrides[get_db] = override_get_db
    yield
    main_minimal.app.dependency_overrides.clear()
