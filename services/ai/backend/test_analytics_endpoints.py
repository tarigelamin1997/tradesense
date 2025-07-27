#!/usr/bin/env python3
"""Test all analytics endpoints to identify issues"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPass123"

def get_auth_token():
    """Login and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_endpoint(method, path, token, data=None):
    """Test an endpoint and show the response"""
    headers = {"Authorization": f"Bearer {token}"}
    
    if method == "GET":
        response = requests.get(f"{BASE_URL}{path}", headers=headers, params=data)
    else:
        response = requests.post(f"{BASE_URL}{path}", headers=headers, json=data)
    
    print(f"\n{'='*60}")
    print(f"{method} {path}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            # Check structure
            if isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
                
                # Check for wrapped responses
                if 'data' in data:
                    print("⚠️  WRAPPED RESPONSE DETECTED")
                    print(f"   Wrapper keys: {list(data.keys())}")
                    print(f"   Data type: {type(data['data'])}")
                    if isinstance(data['data'], dict):
                        print(f"   Data keys: {list(data['data'].keys())}")
            
            # Show sample
            response_str = json.dumps(data, indent=2)
            if len(response_str) > 500:
                print(f"Response preview: {response_str[:500]}...")
            else:
                print(f"Full response: {response_str}")
                
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response: {response.text[:200]}...")
    else:
        print(f"Error response: {response.text[:500]}...")
    
    return response

def main():
    print("🔍 Testing TradeSense Backend Endpoints\n")
    
    # Get auth token
    print("Step 1: Testing authentication...")
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without auth token")
        return
    
    print(f"✅ Got auth token: {token[:20]}...\n")
    
    # Test dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print("Step 2: Testing API endpoints...")
    
    # Test all analytics endpoints
    endpoints = [
        # User endpoints
        ("GET", "/api/v1/auth/me", None),
        
        # Analytics endpoints
        ("GET", "/api/v1/analytics/summary", {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }),
        
        # Try other potential analytics endpoints
        ("GET", "/api/v1/analytics/dashboard", None),
        ("GET", "/api/v1/analytics/performance", None),
        ("GET", "/api/v1/analytics/equity-curve", None),
        ("GET", "/api/v1/analytics/monthly-pnl", None),
        ("GET", "/api/v1/analytics/emotion-impact", None),
        ("GET", "/api/v1/analytics/strategy-performance", None),
        
        # Trade endpoints
        ("GET", "/api/v1/trades", {"limit": 5}),
    ]
    
    results = []
    for method, path, params in endpoints:
        resp = test_endpoint(method, path, token, params)
        results.append((path, resp.status_code))
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print("-"*60)
    
    working = []
    broken = []
    not_found = []
    
    for path, status in results:
        if status == 200:
            working.append(path)
        elif status == 404:
            not_found.append(path)
        else:
            broken.append((path, status))
    
    print(f"\n✅ Working endpoints ({len(working)}):")
    for p in working:
        print(f"   - {p}")
        
    if not_found:
        print(f"\n❌ Not Found (404) endpoints ({len(not_found)}):")
        for p in not_found:
            print(f"   - {p}")
            
    if broken:
        print(f"\n❌ Broken endpoints ({len(broken)}):")
        for p, s in broken:
            print(f"   - {p} (Status: {s})")
    
    print("\n✅ Backend endpoint testing complete!")

if __name__ == "__main__":
    main()