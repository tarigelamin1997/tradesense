
#!/usr/bin/env python3
"""Production startup script for TradeSense."""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup production logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/production.log'),
            logging.StreamHandler()
        ]
    )

def check_environment():
    """Check production environment requirements."""
    required_vars = ['TRADESENSE_MASTER_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    return True

def initialize_database():
    """Initialize database if needed."""
    try:
        from database_manager import db_manager
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection verified")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main startup function."""
    print("🚀 Starting TradeSense...")
    
    setup_logging()
    
    if not check_environment():
        sys.exit(1)
    
    if not initialize_database():
        sys.exit(1)
    
    print("✅ All systems ready")
    
    # Import and run the app
    from core.app_factory import TradeSenseApp
    app = TradeSenseApp()
    app.run()

if __name__ == "__main__":
    main()
