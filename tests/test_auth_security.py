"""
Security tests for authentication system
Tests fixes for BUG-001, BUG-002, BUG-003
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_sql_injection_protection():
    """Test that SQL injection attempts are blocked"""
    # Test various SQL injection patterns
    injection_attempts = [
        {"username": "' OR '1'='1", "password": "' OR '1'='1"},
        {"username": "admin'--", "password": "password"},
        {"username": "admin'; DROP TABLE users;--", "password": "pass"},
        {"email": "test@test.com' OR 1=1--", "password": "pass"},
        {"username": "test\" OR \"1\"=\"1", "password": "pass"},
    ]
    
    for attempt in injection_attempts:
        response = client.post("/api/v1/auth/login", json=attempt)
        # Should reject with 400, not hang or crash
        assert response.status_code == 400
        assert "Invalid characters" in response.json()["detail"]

def test_empty_credentials_validation():
    """Test that empty credentials are rejected quickly"""
    # Test various empty credential combinations
    empty_attempts = [
        {"username": "", "password": ""},
        {"email": "", "password": ""},
        {"username": "", "password": "somepass"},
        {"email": "test@test.com", "password": ""},
    ]
    
    for attempt in empty_attempts:
        response = client.post("/api/v1/auth/login", json=attempt)
        # Should reject with 400, not hang
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

def test_oversized_input_protection():
    """Test protection against oversized inputs"""
    # Create a very long password to test DoS protection
    long_password = "a" * 2000
    
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": long_password
    })
    
    assert response.status_code == 400
    assert "Invalid input" in response.json()["detail"]

def test_concurrent_login_attempts():
    """Test that backend doesn't freeze under concurrent load"""
    import concurrent.futures
    import time
    
    def make_login_attempt():
        return client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    start_time = time.time()
    
    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_login_attempt) for _ in range(10)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    
    # All requests should complete within reasonable time (not hang)
    assert end_time - start_time < 10  # Should complete in under 10 seconds
    
    # Backend should still be responsive after concurrent attempts
    health_response = client.get("/health")
    assert health_response.status_code == 200

def test_special_characters_validation():
    """Test validation of special characters that could cause issues"""
    special_char_attempts = [
        {"username": "test;DELETE FROM users", "password": "pass"},
        {"username": "test\x00null", "password": "pass"},
        {"username": "test\nNewline", "password": "pass"},
        {"username": "test\r\nCRLF", "password": "pass"},
    ]
    
    for attempt in special_char_attempts:
        response = client.post("/api/v1/auth/login", json=attempt)
        # Should handle gracefully, not crash
        assert response.status_code in [400, 401]

def test_timeout_protection():
    """Test that authentication has timeout protection"""
    # This would require mocking a slow database response
    # For now, just verify the endpoint responds quickly
    import time
    
    start = time.time()
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    duration = time.time() - start
    
    # Should respond within 5 seconds (our timeout limit)
    assert duration < 5.0

def test_valid_login_still_works():
    """Ensure valid logins still work after security fixes"""
    # First register a test user
    register_response = client.post("/api/v1/auth/register", json={
        "email": "security@test.com",
        "username": "securitytest",
        "password": "SecurePass123!",
        "first_name": "Security",
        "last_name": "Test"
    })
    
    # Should be able to register
    assert register_response.status_code in [201, 400]  # 400 if user exists
    
    # Test login with valid credentials
    login_response = client.post("/api/v1/auth/login", json={
        "username": "securitytest",
        "password": "SecurePass123!"
    })
    
    # Valid login should work
    if register_response.status_code == 201:
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()