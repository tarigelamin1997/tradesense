#!/usr/bin/env python3
"""
Integration test for httpOnly cookie authentication
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """Test the complete authentication flow with httpOnly cookies"""
    
    # 1. First, let's register a test user
    print("1. Registering test user...")
    register_data = {
        "email": "cookietest@example.com",
        "username": "cookietester",
        "password": "TestPass123!"
    }
    
    session = requests.Session()
    
    try:
        response = session.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        print(f"   Registration status: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ User registered successfully")
        elif response.status_code == 400:
            print("   ⚠️ User might already exist, continuing...")
    except Exception as e:
        print(f"   ❌ Registration failed: {e}")
        return False
    
    # 2. Test login with cookies
    print("\n2. Testing login...")
    login_data = {
        "email": "cookietest@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if cookie was set
            cookies = session.cookies.get_dict()
            if 'auth-token' in cookies:
                print("   ✅ httpOnly cookie 'auth-token' was set!")
            else:
                print("   ❌ Cookie 'auth-token' was NOT set")
                print(f"   Available cookies: {list(cookies.keys())}")
            
            # Check response body
            data = response.json()
            print(f"   Response includes: {list(data.keys())}")
            
            # For backward compatibility, token should still be in response
            if 'access_token' in data:
                print("   ✅ access_token included in response (backward compatibility)")
        else:
            print(f"   ❌ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Login request failed: {e}")
        return False
    
    # 3. Test accessing protected endpoint with cookie
    print("\n3. Testing protected endpoint with cookie...")
    try:
        # Session should automatically send the cookie
        response = session.get(f"{BASE_URL}/api/v1/auth/me")
        print(f"   /me endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ Successfully accessed protected endpoint!")
            print(f"   User email: {user_data.get('email')}")
        else:
            print(f"   ❌ Failed to access protected endpoint: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Protected endpoint request failed: {e}")
        return False
    
    # 4. Test logout
    print("\n4. Testing logout...")
    try:
        response = session.post(f"{BASE_URL}/api/v1/auth/logout")
        print(f"   Logout status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Logout successful")
            
            # Check if cookie was cleared
            cookies_after = session.cookies.get_dict()
            if 'auth-token' not in cookies_after:
                print("   ✅ auth-token cookie was cleared")
            else:
                print("   ⚠️ auth-token cookie still present")
        else:
            print(f"   ❌ Logout failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Logout request failed: {e}")
        return False
    
    # 5. Verify we can't access protected endpoint after logout
    print("\n5. Verifying access denied after logout...")
    try:
        response = session.get(f"{BASE_URL}/api/v1/auth/me")
        print(f"   /me endpoint status after logout: {response.status_code}")
        
        if response.status_code == 401:
            print("   ✅ Access correctly denied after logout")
        else:
            print("   ❌ Still able to access protected endpoint after logout!")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    return True


if __name__ == "__main__":
    print("🔧 Testing httpOnly Cookie Authentication Implementation")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    import time
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"✅ Server is running (health check: {response.status_code})")
    except:
        print("❌ Server is not running! Please start the backend server first.")
        print("   Run: python -m uvicorn main:app --reload")
        exit(1)
    
    print()
    success = test_auth_flow()
    
    if success:
        print("\n✅ All authentication tests completed!")
    else:
        print("\n❌ Some tests failed!")