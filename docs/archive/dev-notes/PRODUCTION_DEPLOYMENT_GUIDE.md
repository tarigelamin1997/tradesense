# TradeSense Production Deployment Guide

## Backend Services (Railway) ✅

All backend services are deployed and healthy on Railway.

### Service URLs:
- **Gateway (Main API)**: https://tradesense-gateway-production.up.railway.app
- **Auth**: https://tradesense-auth-production.up.railway.app
- **Trading**: https://tradesense-trading-production.up.railway.app
- **Analytics**: https://tradesense-analytics-production.up.railway.app
- **Market Data**: https://tradesense-market-data-production.up.railway.app
- **Billing**: https://tradesense-billing-production.up.railway.app
- **AI**: https://tradesense-ai-production.up.railway.app

### ⚠️ IMPORTANT: Stripe Configuration Required

The Billing service is currently using a test Stripe key. Before accepting real payments:

1. **Get your Stripe API keys**:
   - Log in to [Stripe Dashboard](https://dashboard.stripe.com)
   - Go to Developers → API keys
   - Copy your **Secret key** (starts with `sk_live_` for production)

2. **Create Stripe Products and Prices**:
   - Create 3 products: Basic, Pro, Premium
   - Get the price IDs for each (format: `price_xxxxx`)

3. **Update Railway Environment Variables**:
   - Go to Billing service: https://railway.com/project/66278fb6-b5e7-43b6-ac6b-4144235b1519
   - Update these variables:
     ```
     STRIPE_SECRET_KEY=sk_live_your_actual_key_here
     STRIPE_PRICE_BASIC=price_your_basic_price_id
     STRIPE_PRICE_PRO=price_your_pro_price_id  
     STRIPE_PRICE_PREMIUM=price_your_premium_price_id
     ```

4. **Redeploy the Billing service** after updating

## Frontend Deployment (Next Steps)

The frontend will be deployed to Vercel and configured to use:
- API URL: `https://tradesense-gateway-production.up.railway.app`

## Security Notes

- All sensitive keys are stored as environment variables
- JWT tokens are used for authentication across services
- Each service has its own database for data isolation
- CORS will be configured after frontend deployment

## Monitoring

Check system health at: https://tradesense-gateway-production.up.railway.app/health