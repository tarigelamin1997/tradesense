# Railway Environment Variables Quick Setup

## 🚨 IMMEDIATE FIX - Auth Service

The auth service deployment failed because `SECRET_KEY` is missing. Here's how to fix it:

### 1. Go to Railway Dashboard
1. Open your Railway project
2. Click on the `tradesense-auth` service
3. Go to "Variables" tab

### 2. Add Required Variables (Copy & Paste)

```bash
# REQUIRED - Must add these now
SECRET_KEY=your-secret-key-here-32-chars-minimum!
JWT_SECRET_KEY=another-32-char-secure-key-here!!

# CORS - Add your Vercel URLs
CORS_ORIGINS=https://frontend-7uz3djyzl-tarig-ahmeds-projects.vercel.app,https://tradesense.vercel.app,https://frontend-self-nu-47.vercel.app,http://localhost:3000,http://localhost:3001

# Security Features
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true

# Optional (can add later)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID_STARTER=price_...
STRIPE_PRICE_ID_PRO=price_...
REDIS_URL=redis://...
SMTP_HOST=smtp.gmail.com
OPENAI_API_KEY=sk-...
```

### 3. Generate Secure Keys

Use this Python command to generate secure keys:
```python
import secrets
print("SECRET_KEY=" + secrets.token_urlsafe(32))
print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
```

Or use this bash command:
```bash
openssl rand -base64 32
```

### 4. Redeploy
After adding variables, Railway will automatically redeploy.

## 📋 Complete Environment Variables for All Services

### Gateway Service
```bash
SECRET_KEY=<generate-32-chars>
JWT_SECRET_KEY=<same-as-auth-service>
CORS_ORIGINS=<same-as-above>

# Service Discovery (update after deploying each service)
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app
ANALYTICS_SERVICE_URL=https://tradesense-analytics-production.up.railway.app
MARKET_DATA_SERVICE_URL=https://tradesense-market-data-production.up.railway.app
BILLING_SERVICE_URL=https://tradesense-billing-production.up.railway.app
AI_SERVICE_URL=https://tradesense-ai-production.up.railway.app
```

### Trading Service
```bash
SECRET_KEY=<same-as-auth>
JWT_SECRET_KEY=<same-as-auth>
CORS_ORIGINS=<same-as-above>
DATABASE_URL=<railway-provides-this>
```

### Analytics Service
```bash
SECRET_KEY=<same-as-auth>
JWT_SECRET_KEY=<same-as-auth>
CORS_ORIGINS=<same-as-above>
DATABASE_URL=<railway-provides-this>
```

### Other Services (Market Data, Billing, AI)
Same pattern - use the same SECRET_KEY and JWT_SECRET_KEY across all services.

## 🔧 Quick Fix Steps

1. **Generate keys now:**
   ```bash
   python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32)); print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```

2. **Add to Railway:**
   - Go to Railway dashboard
   - Click on tradesense-auth service
   - Variables tab
   - Add the generated keys

3. **Watch deployment:**
   - Railway will auto-redeploy
   - Check logs for success

## 📍 Getting Service URLs

After each service deploys successfully:
1. Go to service in Railway
2. Settings tab
3. Copy the deployment URL
4. Update Gateway service variables with these URLs

## ⚡ Pro Tip

Use Railway's bulk variable import:
1. Copy all variables to a text file
2. In Railway Variables tab, click "Raw Editor"
3. Paste all variables at once