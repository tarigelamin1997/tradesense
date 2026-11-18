import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)