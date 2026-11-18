# Backend Services Deployment Guide for Railway

## Prerequisites
- Railway CLI installed
- Railway account with project created
- Environment variables ready

## Step-by-Step Deployment

### 1. Deploy Gateway Service (Main Entry Point)
```bash
cd /home/tarigelamin/Desktop/tradesense/services/gateway
railway link
railway up
```

### 2. Deploy Auth Service
```bash
cd /home/tarigelamin/Desktop/tradesense/services/auth
railway link
railway up
```

### 3. Deploy Trading Service
```bash
cd /home/tarigelamin/Desktop/tradesense/services/trading
railway link
railway up
```

### 4. Deploy Analytics Service
```bash
cd /home/tarigelamin/Desktop/tradesense/services/analytics
railway link
railway up
```

### 5. Deploy Market Data Service
```bash
cd /home/tarigelamin/Desktop/tradesense/services/market-data
railway link
railway up
```

### 6. Deploy Billing Service
```bash
cd /home/tarigelamin/Desktop/tradesense/services/billing
railway link
railway up
```

### 7. Deploy AI Service
```bash
cd /home/tarigelamin/Desktop/tradesense/services/ai
railway link
railway up
```

## Environment Variables (Set in Railway Dashboard)

For **ALL** services, add these core variables:
```
# CORS Configuration
CORS_ORIGINS=https://frontend-7uz3djyzl-tarig-ahmeds-projects.vercel.app,https://tradesense.vercel.app,https://frontend-self-nu-47.vercel.app

# Security
JWT_SECRET_KEY=<generate-secure-32-char-key>
MASTER_ENCRYPTION_KEY=<generate-secure-32-char-key>

# Features
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true
```

### Service-Specific Variables

**Gateway Service:**
```
# Service URLs (update after deploying each service)
AUTH_SERVICE_URL=https://<auth-service>.railway.app
TRADING_SERVICE_URL=https://<trading-service>.railway.app
ANALYTICS_SERVICE_URL=https://<analytics-service>.railway.app
MARKET_DATA_SERVICE_URL=https://<market-data-service>.railway.app
BILLING_SERVICE_URL=https://<billing-service>.railway.app
AI_SERVICE_URL=https://<ai-service>.railway.app
```

**Database Services (Auth, Trading, Analytics):**
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**Redis Services (if needed):**
```
REDIS_URL=redis://default:password@host:6379
```

## Verify Deployment

1. Check Railway dashboard for deployment status
2. Get the production URLs for each service
3. Update the Gateway service with the correct service URLs
4. Test the API endpoint:
   ```bash
   curl https://tradesense-gateway-production.up.railway.app/health
   ```

## Update Frontend

Once backend is deployed, ensure the frontend has the correct Gateway URL:
1. Go to Vercel dashboard
2. Settings > Environment Variables
3. Set: `PUBLIC_API_URL=https://tradesense-gateway-production.up.railway.app`
4. Redeploy frontend

## Troubleshooting

- If services fail to deploy, check Railway logs
- Ensure all required environment variables are set
- Verify database connections are working
- Check service health endpoints: `/health`