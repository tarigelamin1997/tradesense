#!/usr/bin/env python3
"""
Simple health check script for Railway deployments
"""
import sys
import requests
import os

def check_health():
    port = os.getenv("PORT", "8000")
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
            return 0
        else:
            print(f"❌ Health check failed: Status {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())