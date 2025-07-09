"""
Unit tests that don't require database setup
"""
import pytest
from unittest.mock import Mock, patch

def test_basic_unit():
    """Basic unit test that should always pass"""
    assert 1 + 1 == 2

def test_mock_function():
    """Test mocking a function"""
    mock_obj = Mock()
    mock_obj.some_method.return_value = 5
    result = mock_obj.some_method()
    assert result == 5
    mock_obj.some_method.assert_called_once()

class TestSimpleClass:
    """Test class for simple unit tests"""
    
    def test_class_method(self):
        """Test a class method"""
        assert self.__class__.__name__ == "TestSimpleClass"
    
    def test_with_mock_object(self):
        """Test with a mock object"""
        mock_obj = Mock()
        mock_obj.method.return_value = "test_value"
        assert mock_obj.method() == "test_value"

@pytest.fixture
def simple_data():
    """Simple fixture that doesn't require database"""
    return {"name": "test", "value": 42}

def test_with_simple_fixture(simple_data):
    """Test using a simple fixture"""
    assert simple_data["name"] == "test"
    assert simple_data["value"] == 42 