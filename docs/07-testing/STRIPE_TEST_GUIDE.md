# TradeSense Stripe Integration Testing Guide

## 🚀 Quick Start Testing

### 1. Frontend URLs
- **Main App**: http://localhost:3001
- **Pricing Page**: http://localhost:3001/pricing
- **Billing Portal**: http://localhost:3001/billing
- **Checkout Success**: http://localhost:3001/payment-success

### 2. Backend URLs
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

### 3. Test Credentials

#### Test User Account
```
Email: test@example.com
Password: Test123456
```

#### Stripe Test Cards
- **Success**: 4242 4242 4242 4242
- **3D Secure**: 4000 0025 0000 3155
- **Declined**: 4000 0000 0000 9995

Use any:
- Future expiry: 12/34
- CVC: 123
- ZIP: 12345

### 4. Required Environment Variables

Create `.env` file in backend directory:
```bash
# Stripe Keys (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Price IDs (create in Stripe Dashboard)
STRIPE_PRICE_STARTER_MONTHLY=price_xxx
STRIPE_PRICE_STARTER_YEARLY=price_xxx
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_xxx
STRIPE_PRICE_PROFESSIONAL_YEARLY=price_xxx
STRIPE_PRICE_TEAM_MONTHLY=price_xxx
STRIPE_PRICE_TEAM_YEARLY=price_xxx
```

### 5. Testing Flow

#### A. Test Subscription Creation
1. Go to http://localhost:3001/pricing
2. Click "Get Started" on Starter plan
3. Enter test card details
4. Complete checkout
5. Verify redirect to success page

#### B. Test Billing Portal
1. Login to your account
2. Go to http://localhost:3001/billing
3. Click "Manage Subscription"
4. Test updating payment method
5. Test canceling subscription

#### C. Test Feature Gating
1. Try accessing features as free user
2. Upgrade to paid plan
3. Verify premium features are unlocked
4. Downgrade and verify features are locked

#### D. Test Webhooks (Advanced)
1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login: `stripe login`
3. Forward webhooks: `stripe listen --forward-to localhost:8000/api/v1/billing/webhook`
4. Trigger test events: `stripe trigger payment_intent.succeeded`

### 6. API Testing with cURL

#### Create Checkout Session
```bash
curl -X POST http://localhost:8000/api/v1/billing/create-checkout-session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "price_id": "price_starter_monthly",
    "success_url": "http://localhost:3001/payment-success",
    "cancel_url": "http://localhost:3001/pricing"
  }'
```

#### Get Current Subscription
```bash
curl http://localhost:8000/api/v1/billing/subscription \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Create Portal Session
```bash
curl -X POST http://localhost:8000/api/v1/billing/create-portal-session \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"return_url": "http://localhost:3001/billing"}'
```

### 7. Troubleshooting

#### Frontend Issues
- Check console for errors: F12 → Console
- Verify API URL in frontend config
- Check network requests: F12 → Network

#### Backend Issues
- Check logs: `tail -f backend_working.log`
- Verify Stripe keys are set
- Check database connection

#### Common Errors
1. "No such price": Create products/prices in Stripe Dashboard
2. "Invalid API key": Check STRIPE_SECRET_KEY in .env
3. "CORS error": Verify backend CORS settings
4. "Feature locked": Check subscription status

### 8. Next Steps

1. **Set up Stripe account**: https://dashboard.stripe.com/register
2. **Create products**: Dashboard → Products → Add product
3. **Set up webhooks**: Dashboard → Webhooks → Add endpoint
4. **Configure environment**: Add all keys to .env
5. **Test complete flow**: Register → Subscribe → Use features → Cancel

## 📞 Need Help?

- Stripe Docs: https://stripe.com/docs
- Test Cards: https://stripe.com/docs/testing
- Webhook Testing: https://stripe.com/docs/webhooks/test