import requests

# Test public endpoint (no auth required)
url = "http://127.0.0.1:9100/api/v1/ping"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}") 