"""
Simple test to verify test infrastructure works
"""
import pytest
from unittest.mock import Mock

def test_simple():
    """Simple test that should always pass"""
    assert True

def test_mock():
    """Test using mocks"""
    mock_obj = Mock()
    mock_obj.some_method.return_value = "test"
    assert mock_obj.some_method() == "test"

@pytest.fixture
def simple_fixture():
    """Simple fixture"""
    return {"test": "data"}

def test_with_fixture(simple_fixture):
    """Test using a fixture"""
    assert simple_fixture["test"] == "data" 