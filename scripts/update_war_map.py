
#!/usr/bin/env python3
"""
TradeSense War Map Maintenance Script

This script helps keep the project-war-map.md file updated with current status.
Run this periodically or integrate with CI/CD to maintain accurate project tracking.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

def check_database_tables():
    """Check which database tables exist to verify feature completeness."""
    db_path = Path(__file__).parent.parent / "backend" / "tradesense.db"
    
    if not db_path.exists():
        return {"status": "❌", "tables": 0}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        expected_tables = [
            'users', 'trades', 'playbooks', 'feature_requests', 
            'feature_votes', 'trade_notes', 'portfolio_snapshots'
        ]
        
        existing_tables = [t[0] for t in tables]
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        
        conn.close()
        
        return {
            "status": "✅" if len(missing_tables) == 0 else "⚠️",
            "tables": len(existing_tables),
            "missing": missing_tables
        }
    except Exception as e:
        return {"status": "❌", "error": str(e)}

def check_api_endpoints():
    """Check if key API endpoints exist in the backend."""
    backend_path = Path(__file__).parent.parent / "backend" / "api" / "v1"
    
    expected_routers = [
        "auth", "trades", "uploads", "playbooks", "analytics", 
        "features", "portfolio", "users"
    ]
    
    existing_routers = []
    for router in expected_routers:
        router_path = backend_path / router / "router.py"
        if router_path.exists():
            existing_routers.append(router)
    
    completion_rate = len(existing_routers) / len(expected_routers) * 100
    
    return {
        "status": "✅" if completion_rate >= 90 else "⚠️" if completion_rate >= 70 else "❌",
        "completion": f"{completion_rate:.0f}%",
        "existing": existing_routers,
        "missing": [r for r in expected_routers if r not in existing_routers]
    }

def check_frontend_features():
    """Check frontend feature implementation."""
    frontend_path = Path(__file__).parent.parent / "frontend" / "src" / "features"
    
    expected_features = [
        "auth", "analytics", "dashboard", "trades", 
        "upload", "voting", "portfolio"
    ]
    
    existing_features = []
    if frontend_path.exists():
        for feature in expected_features:
            feature_path = frontend_path / feature
            if feature_path.exists() and (feature_path / "components").exists():
                existing_features.append(feature)
    
    completion_rate = len(existing_features) / len(expected_features) * 100
    
    return {
        "status": "✅" if completion_rate >= 90 else "⚠️" if completion_rate >= 70 else "❌",
        "completion": f"{completion_rate:.0f}%",
        "existing": existing_features,
        "missing": [f for f in expected_features if f not in existing_features]
    }

def generate_status_report():
    """Generate a comprehensive status report."""
    print("🔍 TradeSense War Map Status Check")
    print("=" * 50)
    
    # Database check
    db_status = check_database_tables()
    print(f"📊 Database Status: {db_status['status']}")
    print(f"   Tables: {db_status.get('tables', 'Unknown')}")
    if 'missing' in db_status and db_status['missing']:
        print(f"   Missing: {', '.join(db_status['missing'])}")
    
    # Backend API check
    api_status = check_api_endpoints()
    print(f"🔧 Backend APIs: {api_status['status']} ({api_status['completion']})")
    if api_status['missing']:
        print(f"   Missing: {', '.join(api_status['missing'])}")
    
    # Frontend check
    frontend_status = check_frontend_features()
    print(f"🎨 Frontend Features: {frontend_status['status']} ({frontend_status['completion']})")
    if frontend_status['missing']:
        print(f"   Missing: {', '.join(frontend_status['missing'])}")
    
    # Overall assessment
    all_statuses = [db_status['status'], api_status['status'], frontend_status['status']]
    overall = "✅" if all(s == "✅" for s in all_statuses) else "⚠️"
    
    print(f"\n🎯 Overall Project Status: {overall}")
    print(f"📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return {
        "database": db_status,
        "backend": api_status,
        "frontend": frontend_status,
        "overall": overall,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    generate_status_report()
