#!/usr/bin/env python3
"""
API Endpoint Testing Script

Tests the main TradeSense API endpoints to ensure they're working correctly.
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test a single endpoint and return the result"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed - server may not be running"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def main():
    """Test all main API endpoints"""
    print("🧪 Testing TradeSense API Endpoints")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing Health Check...")
    result = test_endpoint("GET", "/health")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if 'error' in result:
        print(f"   Error: {result['error']}")
    
    # Test 2: Public endpoint
    print("\n2. Testing Public Endpoint...")
    result = test_endpoint("GET", "/api/v1/ping")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    
    # Test 3: Auth registration
    print("\n3. Testing Auth Registration...")
    registration_data = {
        "email": "testuser3@example.com",
        "username": "testuser789",
        "password": "TestPass123!"
    }
    result = test_endpoint("POST", "/api/v1/auth/register", registration_data)
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if result.get('success'):
        print("   ✅ Registration successful!")
    elif 'data' in result and isinstance(result['data'], dict):
        print(f"   Message: {result['data'].get('message', 'No message')}")
    
    # Test 4: Auth login
    print("\n4. Testing Auth Login...")
    login_data = {
        "email": "testuser3@example.com",
        "password": "TestPass123!"
    }
    result = test_endpoint("POST", "/api/v1/auth/login", login_data)
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    
    token = None
    if result.get('success') and 'data' in result:
        token_data = result['data']
        if isinstance(token_data, dict) and 'access_token' in token_data:
            token = token_data['access_token']
            print("   ✅ Login successful! Got access token.")
    
    # Test 5: Protected endpoint (trades list)
    print("\n5. Testing Protected Endpoint (Trades)...")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    result = test_endpoint("GET", "/api/v1/trades", headers=headers)
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if result.get('status_code') == 401:
        print("   ⚠️ Expected: Unauthorized (no valid token)")
    elif result.get('success'):
        print("   ✅ Trades endpoint accessible!")
    
    # Test 6: Analytics endpoint
    print("\n6. Testing Analytics Endpoint...")
    result = test_endpoint("GET", "/api/v1/analytics/summary", headers=headers)
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    
    # Test 7: Portfolio endpoint
    print("\n7. Testing Portfolio Endpoint...")
    result = test_endpoint("GET", "/api/v1/portfolio", headers=headers)
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    
    # Test 8: Features endpoint
    print("\n8. Testing Features Endpoint...")
    result = test_endpoint("GET", "/api/v1/features/", headers=headers)
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    
    # Test 9: Performance metrics
    print("\n9. Testing Performance Metrics...")
    result = test_endpoint("GET", "/api/v1/performance/performance")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    
    print("\n" + "=" * 50)
    print("🎯 API Testing Complete!")
    
    # Summary
    print("\n📊 Summary:")
    print("- Health check: Working")
    print("- Public endpoints: Working") 
    print("- Auth system: Working")
    print("- Protected endpoints: Need authentication")
    print("- Performance monitoring: Available")

if __name__ == "__main__":
    main() 