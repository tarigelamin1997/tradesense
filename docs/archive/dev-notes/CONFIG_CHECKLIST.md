# Railway Configuration Checklist

## Pre-Configuration Check
- [ ] All services showing in Railway dashboard
- [ ] Railway Hobby plan active ($5/month)

## Service Configuration

### ☐ Auth Service
- [ ] PostgreSQL database added
- [ ] JWT_SECRET_KEY environment variable set
- [ ] Service redeployed and showing as UP

### ☐ Trading Service  
- [ ] PostgreSQL database added
- [ ] AUTH_SERVICE_URL environment variable set
- [ ] Service redeployed and showing as UP

### ☐ Analytics Service
- [ ] PostgreSQL database added
- [ ] AUTH_SERVICE_URL environment variable set
- [ ] TRADING_SERVICE_URL environment variable set
- [ ] Service redeployed and showing as UP

### ☐ Market Data Service
- [ ] Redis database added
- [ ] Service redeployed and showing as UP

### ☐ Billing Service
- [ ] PostgreSQL database added
- [ ] AUTH_SERVICE_URL environment variable set
- [ ] STRIPE_SECRET_KEY environment variable set
- [ ] STRIPE_PRICE_BASIC environment variable set
- [ ] STRIPE_PRICE_PRO environment variable set
- [ ] STRIPE_PRICE_PREMIUM environment variable set
- [ ] Service redeployed and showing as UP

### ☐ AI Service
- [ ] PostgreSQL database added
- [ ] AUTH_SERVICE_URL environment variable set
- [ ] TRADING_SERVICE_URL environment variable set
- [ ] ANALYTICS_SERVICE_URL environment variable set
- [ ] OPENAI_API_KEY environment variable set
- [ ] Service redeployed and showing as UP

### ☐ Gateway Service
- [ ] All service URLs added as environment variables
- [ ] Service redeployed and showing as UP

## Post-Configuration Tests

### ☐ Basic Health Checks
- [ ] Run `./monitor-detailed.sh` - all services showing UP
- [ ] Gateway health check shows all services as healthy

### ☐ Full Flow Test
- [ ] Run `./test-railway-flow.sh`
- [ ] User registration works
- [ ] Login returns JWT token
- [ ] Trade creation works
- [ ] Analytics returns data
- [ ] Market data returns quotes

## Final Steps
- [ ] Update CORS for frontend deployment
- [ ] Document production URLs
- [ ] Set up monitoring/alerts

## Quick Commands

Monitor services:
```bash
./monitor-detailed.sh
```

Test complete flow:
```bash
./test-railway-flow.sh
```

Check specific service:
```bash
curl https://tradesense-[service]-production.up.railway.app/health
```