import requests
import sys

# Get endpoint from command line argument
endpoint = sys.argv[1] if len(sys.argv) > 1 else "/api/v1/reviews/"

# Login first to get fresh token
login_url = "http://127.0.0.1:9100/api/v1/auth/login"
login_data = {
    "username": "trader123",
    "password": "SecurePass123!"
}

try:
    # Login
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        sys.exit(1)
    
    token = login_response.json()["access_token"]
    
    # Test the endpoint
    test_url = f"http://127.0.0.1:9100{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(test_url, headers=headers)
    print(f"Endpoint: {endpoint}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")  # First 200 chars
    
except Exception as e:
    print(f"Error: {e}") 