#!/usr/bin/env python3
"""
Detailed API Testing Script

Tests API endpoints and shows full error responses for debugging.
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint_detailed(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test a single endpoint and return detailed result"""
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
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "data": response_data,
            "headers": dict(response.headers),
            "url": url
        }
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed - server may not be running"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def main():
    """Test problematic endpoints with detailed output"""
    print("🔍 Detailed API Testing - Debugging Mode")
    print("=" * 60)
    
    # Test 1: Auth Registration (detailed)
    print("\n🔐 Testing Auth Registration (Detailed)...")
    registration_data = {
        "email": "debuguser@example.com",
        "username": "debuguser",
        "password": "TestPass123!"
    }
    result = test_endpoint_detailed("POST", "/api/v1/auth/register", registration_data)
    print(f"   URL: {result.get('url', 'N/A')}")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if 'data' in result:
        print(f"   Response: {json.dumps(result['data'], indent=2)}")
    if 'error' in result:
        print(f"   Error: {result['error']}")
    
    # Test 2: Auth Login (detailed)
    print("\n🔓 Testing Auth Login (Detailed)...")
    login_data = {
        "email": "debuguser@example.com",
        "password": "TestPass123!"
    }
    result = test_endpoint_detailed("POST", "/api/v1/auth/login", login_data)
    print(f"   URL: {result.get('url', 'N/A')}")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if 'data' in result:
        print(f"   Response: {json.dumps(result['data'], indent=2)}")
    if 'error' in result:
        print(f"   Error: {result['error']}")
    
    # Test 3: Analytics endpoint (detailed)
    print("\n📊 Testing Analytics Endpoint (Detailed)...")
    result = test_endpoint_detailed("GET", "/api/v1/analytics/summary")
    print(f"   URL: {result.get('url', 'N/A')}")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if 'data' in result:
        print(f"   Response: {json.dumps(result['data'], indent=2)}")
    if 'error' in result:
        print(f"   Error: {result['error']}")
    
    # Test 4: Features endpoint (detailed)
    print("\n🚀 Testing Features Endpoint (Detailed)...")
    result = test_endpoint_detailed("GET", "/api/v1/features/")
    print(f"   URL: {result.get('url', 'N/A')}")
    print(f"   Status: {result.get('status_code', 'ERROR')}")
    print(f"   Success: {result.get('success', False)}")
    if 'data' in result:
        print(f"   Response: {json.dumps(result['data'], indent=2)}")
    if 'error' in result:
        print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("🎯 Detailed Testing Complete!")

if __name__ == "__main__":
    main() 