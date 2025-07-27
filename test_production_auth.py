#!/usr/bin/env python3
"""
Test script for TradeSense production authentication endpoints
"""

import requests
import json
import sys
from datetime import datetime
from urllib.parse import urljoin

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Production URLs
GATEWAY_URL = "https://tradesense-gateway.onrender.com"
AUTH_URL = "https://tradesense-auth.onrender.com"
FRONTEND_URL = "https://frontend-self-nu-47.vercel.app"

# Test user credentials
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123"
}

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_result(name, success, details=""):
    """Print test result"""
    if success:
        print(f"{GREEN}✓{RESET} {name}")
    else:
        print(f"{RED}✗{RESET} {name}")
    if details:
        print(f"  {details}")

def test_endpoint(name, url, method="GET", data=None, headers=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if headers is None:
            headers = {}
        
        # Add default headers
        headers.update({
            "Accept": "application/json",
            "Origin": FRONTEND_URL
        })
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, data=data, headers=headers, timeout=10)
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers, timeout=10)
        else:
            response = requests.request(method, url, data=data, headers=headers, timeout=10)
        
        success = response.status_code == expected_status
        details = f"Status: {response.status_code}"
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                body = response.json()
                details += f", Response: {json.dumps(body, indent=2)}"
            except:
                details += f", Body: {response.text[:200]}"
        else:
            details += f", Body: {response.text[:200]}"
        
        # Check CORS headers for OPTIONS requests
        if method == "OPTIONS":
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            details += f"\nCORS Headers: {json.dumps(cors_headers, indent=2)}"
        
        print_result(name, success, details)
        return success, response
        
    except requests.exceptions.Timeout:
        print_result(name, False, "Request timed out")
        return False, None
    except requests.exceptions.ConnectionError as e:
        print_result(name, False, f"Connection error: {str(e)}")
        return False, None
    except Exception as e:
        print_result(name, False, f"Error: {str(e)}")
        return False, None

def main():
    """Run all tests"""
    print_header("TradeSense Production Authentication Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Gateway URL: {GATEWAY_URL}")
    print(f"Auth URL: {AUTH_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    
    # Test 1: Gateway Health
    print_header("1. Gateway Health Checks")
    test_endpoint("Gateway root", f"{GATEWAY_URL}/")
    test_endpoint("Gateway health", f"{GATEWAY_URL}/health")
    test_endpoint("Gateway services", f"{GATEWAY_URL}/services")
    
    # Test 2: Auth Service Direct
    print_header("2. Auth Service Direct Access")
    test_endpoint("Auth root", f"{AUTH_URL}/")
    test_endpoint("Auth health", f"{AUTH_URL}/health")
    
    # Test 3: CORS Preflight
    print_header("3. CORS Preflight Requests")
    
    cors_headers = {
        "Origin": FRONTEND_URL,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
    
    test_endpoint(
        "CORS preflight for /auth/token",
        f"{GATEWAY_URL}/auth/token",
        method="OPTIONS",
        headers=cors_headers,
        expected_status=200
    )
    
    test_endpoint(
        "CORS preflight for /api/auth/token",
        f"{GATEWAY_URL}/api/auth/token",
        method="OPTIONS",
        headers=cors_headers,
        expected_status=200
    )
    
    # Test 4: Auth Endpoints via Gateway
    print_header("4. Auth Endpoints via Gateway")
    
    # Test registration endpoint
    print("\nTesting registration endpoint:")
    reg_data = json.dumps({
        "email": TEST_USER["email"],
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    })
    
    success, response = test_endpoint(
        "Register via /auth/register",
        f"{GATEWAY_URL}/auth/register",
        method="POST",
        data=reg_data,
        headers={"Content-Type": "application/json"},
        expected_status=200
    )
    
    # Test login endpoint with form data
    print("\nTesting login endpoint:")
    login_data = f"username={TEST_USER['email']}&password={TEST_USER['password']}"
    
    success, response = test_endpoint(
        "Login via /auth/token (email)",
        f"{GATEWAY_URL}/auth/token",
        method="POST",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        expected_status=200
    )
    
    if success and response:
        try:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                print(f"\n{GREEN}Successfully obtained access token!{RESET}")
                
                # Test authenticated endpoint
                print("\nTesting authenticated endpoint:")
                test_endpoint(
                    "Get user info via /auth/me",
                    f"{GATEWAY_URL}/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                    expected_status=200
                )
        except:
            pass
    
    # Test 5: Frontend Integration
    print_header("5. Frontend Integration Check")
    
    print("Frontend should set environment variable:")
    print(f"  VITE_API_BASE_URL={GATEWAY_URL}")
    print("\nFrontend auth flow:")
    print("  1. POST to {GATEWAY_URL}/auth/register for new users")
    print("  2. POST to {GATEWAY_URL}/auth/token for login")
    print("  3. GET to {GATEWAY_URL}/auth/me to verify authentication")
    
    # Test 6: Common Issues
    print_header("6. Diagnostics Summary")
    
    # Check if services are reachable
    gateway_reachable = requests.get(f"{GATEWAY_URL}/health", timeout=5).status_code == 200
    auth_reachable = requests.get(f"{AUTH_URL}/health", timeout=5).status_code == 200
    
    print(f"\nService Status:")
    print(f"  Gateway: {'✓ Reachable' if gateway_reachable else '✗ Unreachable'}")
    print(f"  Auth: {'✓ Reachable' if auth_reachable else '✗ Unreachable'}")
    
    print(f"\nRecommendations:")
    if not gateway_reachable:
        print(f"  {RED}• Gateway is not responding. Check Render deployment logs{RESET}")
    if not auth_reachable:
        print(f"  {RED}• Auth service is not responding. Check Render deployment logs{RESET}")
    
    print(f"\nFrontend Configuration:")
    print(f"  • Ensure VITE_API_BASE_URL is set to: {GATEWAY_URL}")
    print(f"  • Ensure frontend URLs are added to CORS origins in gateway and auth service")
    print(f"  • Current frontend URL: {FRONTEND_URL}")

if __name__ == "__main__":
    main()