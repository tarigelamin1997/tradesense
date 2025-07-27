"""
Production startup script with security
"""
import os
import sys

# Add backend to path for shared modules
sys.path.insert(0, '/app/backend')

# Import and run secure main
from main_secure import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=1,  # Railway handles scaling
        loop="uvloop",
        access_log=False,
        server_header=False,
        date_header=False
    )
