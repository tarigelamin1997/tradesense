#!/usr/bin/env python3
import sys
import os

# Add backend to path
sys.path.insert(0, "/home/tarigelamin/Desktop/tradesense/src/backend")

# Load environment variables
from dotenv import load_dotenv
load_dotenv("/home/tarigelamin/Desktop/tradesense/src/backend/.env")

# Try to start the backend
try:
    print("Testing backend startup...")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")
    print(f"JWT_SECRET_KEY: {os.getenv('JWT_SECRET_KEY')}")
    
    # Import the app
    from main import app
    print("✅ Backend imported successfully!")
    
    # Test a simple endpoint
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/v1/health")
    print(f"Health check response: {response.status_code}")
    print(f"Response body: {response.json()}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()