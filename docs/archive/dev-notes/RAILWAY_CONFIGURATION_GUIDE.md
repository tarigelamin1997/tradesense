# Railway Configuration Guide

## 🔧 Step-by-Step Configuration

### 1. Gateway Service Configuration
**Project**: https://railway.com/project/e155abc9-0cd8-4c6f-b31d-572fa2548058

**Variables to add:**
1. Go to the Gateway service
2. Click on "Variables" tab
3. Add these:
```
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app
ANALYTICS_SERVICE_URL=https://tradesense-analytics-production.up.railway.app
MARKET_DATA_SERVICE_URL=https://tradesense-market-data-production.up.railway.app
BILLING_SERVICE_URL=https://tradesense-billing-production.up.railway.app
AI_SERVICE_URL=https://tradesense-ai-production.up.railway.app
```

### 2. Auth Service Configuration
**Project**: https://railway.com/project/c24752c8-ae7a-4577-9579-709ac623bea1

**Add PostgreSQL:**
1. Click "New" button
2. Select "Database" → "Add PostgreSQL"
3. Wait for database to provision

**Variables to add:**
```
JWT_SECRET_KEY=your-very-secret-key-change-this-in-production-123456789
```

### 3. Trading Service Configuration  
**Project**: https://railway.com/project/20d52e60-bb93-485e-a6c1-44cc0ecc4715

**Add PostgreSQL:**
1. Click "New" button
2. Select "Database" → "Add PostgreSQL"
3. Wait for database to provision

**Variables to add:**
```
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
```

## 📝 Quick Copy Commands

After configuration, you can check the services:

```bash
# Check all services
./check-railway-services.sh

# Test the complete flow (once services are up)
./test-railway-flow.sh
```