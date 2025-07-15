import requests

# Login endpoint
login_url = "http://127.0.0.1:9100/api/v1/auth/login"

# Login credentials
login_data = {
    "username": "trader123",
    "password": "SecurePass123!"
}

try:
    # Login to get token
    response = requests.post(login_url, json=login_data)
    print(f"Login Status Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"Login successful!")
        print(f"Token: {token_data['access_token']}")
        
        # Now test the playbooks endpoint with the fresh token
        playbooks_url = "http://127.0.0.1:9100/api/v1/playbooks/"
        headers = {
            "Authorization": f"Bearer {token_data['access_token']}"
        }
        
        playbooks_response = requests.get(playbooks_url, headers=headers)
        print(f"\nPlaybooks Status Code: {playbooks_response.status_code}")
        print(f"Playbooks Response: {playbooks_response.text}")
    else:
        print(f"Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}") 