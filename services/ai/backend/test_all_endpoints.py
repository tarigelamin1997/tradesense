#!/usr/bin/env python3
"""
TradeSense Backend API Endpoint Tester
This script tests all API endpoints and generates a comprehensive status report
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "Password123!"
TIMEOUT = 10

# Results storage
results = {
    "timestamp": datetime.now().isoformat(),
    "base_url": BASE_URL,
    "endpoints": {},
    "summary": {
        "total": 0,
        "working": 0,
        "partial": 0,
        "broken": 0,
        "untested": 0
    }
}

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_result(endpoint: str, method: str, status: str, message: str, response_time: float = 0):
    """Log test result with color coding"""
    color = Colors.GREEN if status == "✅ Working" else Colors.YELLOW if status == "🟡 Partial" else Colors.RED
    print(f"{color}[{method}] {endpoint}: {status} - {message} ({response_time:.2f}s){Colors.END}")
    
    results["endpoints"][f"{method} {endpoint}"] = {
        "status": status,
        "message": message,
        "response_time": response_time
    }
    results["summary"]["total"] += 1
    
    if status == "✅ Working":
        results["summary"]["working"] += 1
    elif status == "🟡 Partial":
        results["summary"]["partial"] += 1
    elif status == "❌ Broken":
        results["summary"]["broken"] += 1
    else:
        results["summary"]["untested"] += 1

def test_endpoint(method: str, endpoint: str, auth_token: Optional[str] = None, 
                  data: Optional[Dict] = None, expected_status: List[int] = [200]) -> Dict:
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=TIMEOUT)
        else:
            return {"error": f"Unknown method: {method}"}
        
        response_time = time.time() - start_time
        
        if response.status_code in expected_status:
            try:
                return {
                    "status": "success",
                    "data": response.json(),
                    "status_code": response.status_code,
                    "response_time": response_time
                }
            except:
                return {
                    "status": "success",
                    "data": response.text,
                    "status_code": response.status_code,
                    "response_time": response_time
                }
        else:
            return {
                "status": "error",
                "error": f"Unexpected status code: {response.status_code}",
                "data": response.text,
                "status_code": response.status_code,
                "response_time": response_time
            }
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Request timeout", "response_time": TIMEOUT}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Connection error - is the server running?", "response_time": 0}
    except Exception as e:
        return {"status": "error", "error": str(e), "response_time": time.time() - start_time}

def get_auth_token() -> Optional[str]:
    """Get authentication token"""
    # First try to register the test user
    register_data = {
        "email": TEST_USER_EMAIL,
        "username": "testuser",
        "password": TEST_USER_PASSWORD
    }
    test_endpoint("POST", "/api/v1/auth/register", data=register_data, expected_status=[200, 400])
    
    # Then login
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    result = test_endpoint("POST", "/api/v1/auth/login", data=login_data)
    
    if result["status"] == "success" and "data" in result:
        if isinstance(result["data"], dict):
            return result["data"].get("access_token")
    return None

def test_health_endpoints():
    """Test health check endpoints"""
    print(f"\n{Colors.BLUE}=== Testing Health Endpoints ==={Colors.END}")
    
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/health", None),
        ("GET", "/api/v1/health", None),
        ("GET", "/api/v1/health/db", None),
        ("GET", "/api/v1/performance/metrics", None),
    ]
    
    for method, endpoint, expected in endpoints:
        result = test_endpoint(method, endpoint)
        if result["status"] == "success":
            log_result(endpoint, method, "✅ Working", "Health check active", result.get("response_time", 0))
        else:
            log_result(endpoint, method, "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))

def test_auth_endpoints():
    """Test authentication endpoints"""
    print(f"\n{Colors.BLUE}=== Testing Authentication Endpoints ==={Colors.END}")
    
    # Test registration
    register_data = {
        "email": f"test_{int(time.time())}@example.com",
        "username": f"testuser_{int(time.time())}",
        "password": "TestPassword123!"
    }
    result = test_endpoint("POST", "/api/v1/auth/register", data=register_data)
    if result["status"] == "success":
        log_result("/api/v1/auth/register", "POST", "✅ Working", "User registration works", result.get("response_time", 0))
    else:
        log_result("/api/v1/auth/register", "POST", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))
    
    # Test login
    auth_token = get_auth_token()
    if auth_token:
        log_result("/api/v1/auth/login", "POST", "✅ Working", "Login successful", 0)
    else:
        log_result("/api/v1/auth/login", "POST", "❌ Broken", "Login failed", 0)
    
    # Test profile
    if auth_token:
        result = test_endpoint("GET", "/api/v1/auth/profile", auth_token)
        if result["status"] == "success":
            log_result("/api/v1/auth/profile", "GET", "✅ Working", "Profile retrieval works", result.get("response_time", 0))
        else:
            log_result("/api/v1/auth/profile", "GET", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))
    
    return auth_token

def test_trade_endpoints(auth_token: Optional[str]):
    """Test trade management endpoints"""
    print(f"\n{Colors.BLUE}=== Testing Trade Endpoints ==={Colors.END}")
    
    if not auth_token:
        log_result("/api/v1/trades", "ALL", "❓ Untested", "No auth token available", 0)
        return
    
    # Test list trades
    result = test_endpoint("GET", "/api/v1/trades", auth_token)
    if result["status"] == "success":
        log_result("/api/v1/trades", "GET", "✅ Working", "Trade listing works", result.get("response_time", 0))
    else:
        log_result("/api/v1/trades", "GET", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))
    
    # Test create trade
    trade_data = {
        "symbol": "AAPL",
        "entry_time": datetime.now().isoformat(),
        "exit_time": (datetime.now() + timedelta(hours=1)).isoformat(),
        "entry_price": 150.00,
        "exit_price": 152.50,
        "quantity": 100,
        "trade_type": "long"
    }
    result = test_endpoint("POST", "/api/v1/trades", auth_token, trade_data)
    if result["status"] == "success":
        log_result("/api/v1/trades", "POST", "✅ Working", "Trade creation works", result.get("response_time", 0))
        
        # If creation worked, test other operations
        if isinstance(result["data"], dict) and "id" in result["data"]:
            trade_id = result["data"]["id"]
            
            # Test get single trade
            result = test_endpoint("GET", f"/api/v1/trades/{trade_id}", auth_token)
            if result["status"] == "success":
                log_result(f"/api/v1/trades/:id", "GET", "✅ Working", "Single trade retrieval works", result.get("response_time", 0))
            else:
                log_result(f"/api/v1/trades/:id", "GET", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))
            
            # Test update trade
            update_data = {"exit_price": 153.00}
            result = test_endpoint("PUT", f"/api/v1/trades/{trade_id}", auth_token, update_data)
            if result["status"] == "success":
                log_result(f"/api/v1/trades/:id", "PUT", "✅ Working", "Trade update works", result.get("response_time", 0))
            else:
                log_result(f"/api/v1/trades/:id", "PUT", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))
            
            # Test delete trade
            result = test_endpoint("DELETE", f"/api/v1/trades/{trade_id}", auth_token)
            if result["status"] == "success":
                log_result(f"/api/v1/trades/:id", "DELETE", "✅ Working", "Trade deletion works", result.get("response_time", 0))
            else:
                log_result(f"/api/v1/trades/:id", "DELETE", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))
    else:
        log_result("/api/v1/trades", "POST", "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))

def test_analytics_endpoints(auth_token: Optional[str]):
    """Test analytics endpoints"""
    print(f"\n{Colors.BLUE}=== Testing Analytics Endpoints ==={Colors.END}")
    
    if not auth_token:
        log_result("/api/v1/analytics", "ALL", "❓ Untested", "No auth token available", 0)
        return
    
    analytics_endpoints = [
        ("GET", "/api/v1/analytics/summary", "Performance summary"),
        ("GET", "/api/v1/analytics/streaks", "Win/loss streaks"),
        ("GET", "/api/v1/analytics/emotions", "Emotional analysis"),
        ("GET", "/api/v1/analytics/patterns", "Pattern detection"),
        ("GET", "/api/v1/analytics/heatmap", "Trading heatmap"),
        ("GET", "/api/v1/analytics/timeline", "Timeline analysis"),
    ]
    
    for method, endpoint, description in analytics_endpoints:
        result = test_endpoint(method, endpoint, auth_token)
        if result["status"] == "success":
            log_result(endpoint, method, "✅ Working", f"{description} works", result.get("response_time", 0))
        else:
            log_result(endpoint, method, "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))

def test_other_endpoints(auth_token: Optional[str]):
    """Test remaining endpoints"""
    print(f"\n{Colors.BLUE}=== Testing Other Endpoints ==={Colors.END}")
    
    if not auth_token:
        log_result("Other endpoints", "ALL", "❓ Untested", "No auth token available", 0)
        return
    
    other_endpoints = [
        # Portfolio
        ("GET", "/api/v1/portfolio", "Portfolio listing"),
        ("POST", "/api/v1/portfolio", "Portfolio creation", {"name": "Test Portfolio", "initial_balance": 10000}),
        
        # Features
        ("GET", "/api/v1/features", "Feature requests"),
        
        # Market Data
        ("GET", "/api/v1/market-data/quote?symbol=AAPL", "Market quotes"),
        
        # Intelligence
        ("GET", "/api/v1/intelligence/insights", "Trade insights"),
        
        # Journal
        ("GET", "/api/v1/journal", "Journal entries"),
        
        # Playbooks
        ("GET", "/api/v1/playbooks", "Playbook listing"),
        
        # Tags
        ("GET", "/api/v1/tags", "Tag listing"),
        
        # Uploads
        ("GET", "/api/v1/uploads/status", "Upload status"),
    ]
    
    for item in other_endpoints:
        method = item[0]
        endpoint = item[1]
        description = item[2]
        data = item[3] if len(item) > 3 else None
        
        result = test_endpoint(method, endpoint, auth_token, data)
        if result["status"] == "success":
            log_result(endpoint, method, "✅ Working", f"{description} works", result.get("response_time", 0))
        else:
            status_code = result.get("status_code", 0)
            if status_code == 404:
                log_result(endpoint, method, "🟡 Partial", f"{description} - Not implemented", result.get("response_time", 0))
            else:
                log_result(endpoint, method, "❌ Broken", result.get("error", "Unknown error"), result.get("response_time", 0))

def generate_report():
    """Generate final report"""
    print(f"\n{Colors.BLUE}=== Final Report ==={Colors.END}")
    print(f"Total Endpoints Tested: {results['summary']['total']}")
    print(f"{Colors.GREEN}✅ Working: {results['summary']['working']} ({results['summary']['working']/results['summary']['total']*100:.1f}%){Colors.END}")
    print(f"{Colors.YELLOW}🟡 Partial: {results['summary']['partial']} ({results['summary']['partial']/results['summary']['total']*100:.1f}%){Colors.END}")
    print(f"{Colors.RED}❌ Broken: {results['summary']['broken']} ({results['summary']['broken']/results['summary']['total']*100:.1f}%){Colors.END}")
    print(f"❓ Untested: {results['summary']['untested']} ({results['summary']['untested']/results['summary']['total']*100:.1f}%)")
    
    # Save detailed report
    with open("endpoint_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: endpoint_test_results.json")
    
    # Generate markdown report
    markdown_report = f"""# TradeSense API Endpoint Test Report
Generated: {results['timestamp']}

## Summary
- **Total Endpoints**: {results['summary']['total']}
- **✅ Working**: {results['summary']['working']} ({results['summary']['working']/results['summary']['total']*100:.1f}%)
- **🟡 Partial**: {results['summary']['partial']} ({results['summary']['partial']/results['summary']['total']*100:.1f}%)
- **❌ Broken**: {results['summary']['broken']} ({results['summary']['broken']/results['summary']['total']*100:.1f}%)
- **❓ Untested**: {results['summary']['untested']} ({results['summary']['untested']/results['summary']['total']*100:.1f}%)

## Detailed Results

| Endpoint | Method | Status | Message | Response Time |
|----------|--------|--------|---------|---------------|
"""
    
    for endpoint, data in sorted(results["endpoints"].items()):
        markdown_report += f"| {endpoint.split(' ', 1)[1]} | {endpoint.split(' ', 1)[0]} | {data['status']} | {data['message']} | {data['response_time']:.2f}s |\n"
    
    with open("endpoint_test_report.md", "w") as f:
        f.write(markdown_report)
    print(f"Markdown report saved to: endpoint_test_report.md")

def main():
    """Main test runner"""
    print(f"{Colors.BLUE}=== TradeSense Backend API Endpoint Tester ==={Colors.END}")
    print(f"Testing API at: {BASE_URL}")
    print(f"Starting tests...\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"{Colors.GREEN}✅ Server is running{Colors.END}\n")
    except:
        print(f"{Colors.RED}❌ Server is not running at {BASE_URL}{Colors.END}")
        print("Please start the backend server with: uvicorn main:app --reload")
        return
    
    # Run tests
    test_health_endpoints()
    auth_token = test_auth_endpoints()
    test_trade_endpoints(auth_token)
    test_analytics_endpoints(auth_token)
    test_other_endpoints(auth_token)
    
    # Generate report
    generate_report()

if __name__ == "__main__":
    main()