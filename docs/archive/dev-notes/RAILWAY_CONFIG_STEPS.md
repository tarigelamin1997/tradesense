# Railway Configuration Step-by-Step

## Order of Configuration (Important!)

### Step 1: Auth Service (Do First)
**URL**: https://railway.com/project/c24752c8-ae7a-4577-9579-709ac623bea1

1. Click "New" → "Database" → "Add PostgreSQL"
2. Go to Variables tab, add:
   ```
   JWT_SECRET_KEY=your-secret-key-change-in-production-123456789
   ```
3. Wait for redeploy

### Step 2: Trading Service
**URL**: https://railway.com/project/20d52e60-bb93-485e-a6c1-44cc0ecc4715

1. Click "New" → "Database" → "Add PostgreSQL"
2. Go to Variables tab, add:
   ```
   AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
   ```
3. Wait for redeploy

### Step 3: Analytics Service
**URL**: https://railway.com/project/340578fb-7187-4c75-bf38-1adb4d85a1a8

1. Click "New" → "Database" → "Add PostgreSQL"
2. Go to Variables tab, add:
   ```
   AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
   TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app
   ```

### Step 4: Market Data Service
**URL**: https://railway.com/project/5a0154b1-c741-4f17-9c5f-41afc86d387a

1. Click "New" → "Database" → "Add Redis"
2. No additional variables needed

### Step 5: Billing Service
**URL**: https://railway.com/project/66278fb6-b5e7-43b6-ac6b-4144235b1519

1. Click "New" → "Database" → "Add PostgreSQL"
2. Go to Variables tab, add:
   ```
   AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
   STRIPE_PRICE_BASIC=price_1OHeLmGFunV6wPMQbasic123
   STRIPE_PRICE_PRO=price_1OHeLmGFunV6wPMQpro456
   STRIPE_PRICE_PREMIUM=price_1OHeLmGFunV6wPMQpremium789
   ```

### Step 6: AI Service
**URL**: https://railway.com/project/bd8e53a4-aa1a-41c2-8c7e-080593160c96

1. Click "New" → "Database" → "Add PostgreSQL"
2. Go to Variables tab, add:
   ```
   AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
   TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app
   ANALYTICS_SERVICE_URL=https://tradesense-analytics-production.up.railway.app
   OPENAI_API_KEY=sk-test-your-openai-key-here
   ```

### Step 7: Gateway Service (Do Last)
**URL**: https://railway.com/project/e155abc9-0cd8-4c6f-b31d-572fa2548058

Go to Variables tab, add:
```
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app
ANALYTICS_SERVICE_URL=https://tradesense-analytics-production.up.railway.app
MARKET_DATA_SERVICE_URL=https://tradesense-market-data-production.up.railway.app
BILLING_SERVICE_URL=https://tradesense-billing-production.up.railway.app
AI_SERVICE_URL=https://tradesense-ai-production.up.railway.app
```

## Quick Check Command

After each configuration, run:
```bash
./monitor-deployments.sh
```

## Important Notes

1. **Database URLs are auto-configured** - Railway automatically sets DATABASE_URL when you add PostgreSQL
2. **Redis URL is auto-configured** - Railway automatically sets REDIS_URL when you add Redis
3. **Services will restart** after adding variables - this is normal
4. **Wait for each service** to show as UP before configuring the next

Start with Auth Service!