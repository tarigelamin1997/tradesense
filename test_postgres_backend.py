#!/usr/bin/env python3
"""Test PostgreSQL backend functionality"""
import subprocess
import time
import requests
import json
import sys
import os

def start_backend():
    """Start the backend server"""
    print("Starting backend server...")
    # Kill any existing processes
    subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
    time.sleep(1)
    
    # Start backend
    backend_process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=os.path.join(os.path.dirname(__file__), "src", "backend"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                print("✓ Backend server started successfully")
                return backend_process
        except:
            time.sleep(1)
    
    print("✗ Failed to start backend server")
    backend_process.terminate()
    return None

def test_login():
    """Test login with PostgreSQL"""
    print("\nTesting login with PostgreSQL backend...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✓ Login successful!")
            data = response.json()
            print(f"  Username: {data.get('username')}")
            print(f"  Email: {data.get('email')}")
            print(f"  Token: {data.get('access_token')[:20]}...")
            return True
        else:
            print(f"✗ Login failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing login: {e}")
        return False

def test_user_list():
    """Test getting user list"""
    print("\nTesting user list...")
    
    try:
        # First login to get token
        login_response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            
            # Get user info
            response = requests.get(
                "http://localhost:8000/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                print("✓ User info retrieved successfully")
                user = response.json()
                print(f"  Current user: {user.get('username')} ({user.get('email')})")
                return True
            else:
                print(f"✗ Failed to get user info: {response.status_code}")
                return False
        else:
            print("✗ Could not login to test user list")
            return False
            
    except Exception as e:
        print(f"✗ Error testing user list: {e}")
        return False

def main():
    print("=== Testing TradeSense with PostgreSQL ===")
    
    # Check DATABASE_URL
    db_url = os.environ.get('DATABASE_URL', 'Not set')
    print(f"\nDATABASE_URL: {db_url}")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Could not start backend server")
        sys.exit(1)
    
    try:
        # Run tests
        all_passed = True
        
        if not test_login():
            all_passed = False
        
        if not test_user_list():
            all_passed = False
        
        print("\n" + "="*50)
        if all_passed:
            print("✅ All tests passed! PostgreSQL backend is working correctly.")
        else:
            print("❌ Some tests failed. Check the output above.")
        
    finally:
        # Stop backend
        print("\nStopping backend server...")
        backend_process.terminate()
        backend_process.wait()
        print("✓ Backend server stopped")

if __name__ == "__main__":
    # Activate virtual environment
    activate_script = os.path.join(os.path.dirname(__file__), "venv", "bin", "activate_this.py")
    if os.path.exists(activate_script):
        with open(activate_script) as f:
            exec(f.read(), {'__file__': activate_script})
    
    main()