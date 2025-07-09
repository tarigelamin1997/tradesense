import requests

# Your token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZDc4NDdhYS02MDg0LTQ0N2ItYWFmZC1mZDlkNjkzZjU5YWQiLCJleHAiOjE3NTE1Mzc0MDh9.Im_xaOt1gJYLgwiu9f6HI2G6wByyfnC2DyonaVS3pRA"

# Test endpoint
url = "http://127.0.0.1:9100/api/v1/playbooks/"

# Make request with Bearer token
headers = {
    "Authorization": f"Bearer {token}"
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Raw Response: {response.text}")
    
    if response.status_code == 200:
        try:
            print(f"JSON Response: {response.json()}")
        except:
            print("Could not parse response as JSON")
except Exception as e:
    print(f"Error: {e}") 