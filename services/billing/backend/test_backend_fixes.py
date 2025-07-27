#!/usr/bin/env python3
"""
Test backend after critical fixes
"""
import sys
import os
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, inspect, text
from core.db.session import get_db, engine
from models import User, Trade
import requests
import json

print("🔍 Testing Backend Fixes...")
print("=" * 60)

# Test 1: PostgreSQL Connection
print("\n1️⃣ Testing PostgreSQL Connection...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ PostgreSQL connected: {version[:30]}...")
        
        # Check database type
        print(f"✅ Database URL: {engine.url}")
        
        # Count records
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM trades"))
        trade_count = result.scalar()
        print(f"✅ Users: {user_count}, Trades: {trade_count}")
except Exception as e:
    print(f"❌ PostgreSQL Error: {e}")

# Test 2: Date Column Types
print("\n2️⃣ Testing Date Column Types...")
try:
    inspector = inspect(engine)
    columns = inspector.get_columns('trades')
    date_cols = {}
    for col in columns:
        if 'time' in col['name'] or 'created' in col['name']:
            date_cols[col['name']] = str(col['type'])
    
    all_timestamp = all('TIMESTAMP' in str(t) or 'DateTime' in str(t) for t in date_cols.values())
    if all_timestamp:
        print(f"✅ All date columns are TIMESTAMP type:")
        for name, type_ in date_cols.items():
            print(f"   - {name}: {type_}")
    else:
        print(f"❌ Some date columns are not TIMESTAMP:")
        for name, type_ in date_cols.items():
            print(f"   - {name}: {type_}")
except Exception as e:
    print(f"❌ Date column check error: {e}")

# Test 3: Indexes
print("\n3️⃣ Testing Database Indexes...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'trades' 
            AND indexname LIKE 'idx_%'
        """))
        indexes = [row[0] for row in result.fetchall()]
        
        if len(indexes) > 5:
            print(f"✅ Found {len(indexes)} performance indexes on trades table")
            for idx in indexes[:5]:
                print(f"   - {idx}")
            print(f"   ... and {len(indexes) - 5} more")
        else:
            print(f"⚠️  Only {len(indexes)} indexes found on trades table")
except Exception as e:
    print(f"❌ Index check error: {e}")

# Test 4: Date Query (Analytics Test)
print("\n4️⃣ Testing Date Queries...")
try:
    db = next(get_db())
    # Test date comparison
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=365)
    
    # This should work now with proper TIMESTAMP columns
    trades = db.query(Trade).filter(
        Trade.entry_time >= start_date
    ).limit(5).all()
    
    print(f"✅ Date query successful! Found {len(trades)} trades after {start_date.date()}")
    
    # Test analytics-style query
    from sqlalchemy import func
    result = db.query(
        func.count(Trade.id).label('count'),
        func.sum(Trade.pnl).label('total_pnl')
    ).filter(
        Trade.user_id == User.id,
        Trade.entry_time >= start_date
    ).first()
    
    if result:
        print(f"✅ Analytics query works: {result.count} trades, ${result.total_pnl:.2f} P&L")
except Exception as e:
    print(f"❌ Date query error: {e}")
finally:
    db.close()

# Test 5: API Response Format
print("\n5️⃣ Testing API Response Format...")
try:
    # Test health endpoint
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health endpoint working: {data}")
    
    # Test if analytics endpoint returns wrapped format
    # First login to get token
    login_resp = requests.post("http://localhost:8000/api/v1/auth/login", 
        json={"email": "test@example.com", "password": "Password123!"})
    
    if login_resp.status_code == 200:
        token = login_resp.json().get("access_token")
        
        # Test analytics endpoint
        headers = {"Authorization": f"Bearer {token}"}
        analytics_resp = requests.get("http://localhost:8000/api/v1/analytics/summary", 
            headers=headers)
        
        if analytics_resp.status_code == 200:
            data = analytics_resp.json()
            # Check if response is wrapped
            if "success" in data and "data" in data:
                print(f"✅ Analytics returns wrapped response format")
                print(f"   - success: {data['success']}")
                print(f"   - has data: {'data' in data}")
                print(f"   - has message: {'message' in data}")
            else:
                print(f"⚠️  Analytics returns unwrapped format: {list(data.keys())}")
        else:
            print(f"❌ Analytics endpoint error: {analytics_resp.status_code}")
    else:
        print(f"❌ Login failed: {login_resp.status_code}")
except Exception as e:
    print(f"❌ API test error: {e}")

print("\n" + "=" * 60)
print("📊 Summary of Fixes:")
print("1. PostgreSQL: Check connection above")
print("2. Date Columns: Check TIMESTAMP conversion above")
print("3. Indexes: Check performance indexes above")
print("4. Date Queries: Check analytics queries above")
print("5. Response Format: Check API format above")
print("\n✅ Run this script after uvicorn is running to verify all fixes!")