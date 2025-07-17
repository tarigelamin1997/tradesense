# Stripe Integration Setup Guide

## Overview
This guide will help you set up real Stripe integration for TradeSense, replacing the fake product IDs with actual Stripe products and prices.

## Prerequisites
- Stripe account (create one at https://stripe.com)
- Access to Stripe Dashboard
- Backend environment variables configured

## Step 1: Create Products in Stripe Dashboard

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Products** → **Add product**
3. Create the following products:

### TradeSense Pro
- **Name**: TradeSense Pro
- **Description**: For serious traders - unlimited trades, advanced analytics, real-time data
- **Pricing**:
  - Monthly: $29/month (create a recurring price)
  - Annual: $290/year (create a recurring price)
- **Features to add in metadata**:
  - `trades_per_month`: `-1` (unlimited)
  - `playbooks`: `10`
  - `advanced_analytics`: `true`

### TradeSense Enterprise
- **Name**: TradeSense Enterprise
- **Description**: For professional traders - AI insights, priority support, custom integrations
- **Pricing**:
  - Monthly: $99/month (create a recurring price)
  - Annual: $990/year (create a recurring price)
- **Features to add in metadata**:
  - `trades_per_month`: `-1` (unlimited)
  - `playbooks`: `-1` (unlimited)
  - `ai_insights`: `true`
  - `priority_support`: `true`

## Step 2: Get Price IDs

After creating products and prices:
1. Go to each product in Stripe Dashboard
2. Copy the **Price ID** (starts with `price_`)
3. Note down all price IDs:
   - Pro Monthly: `price_xxx...`
   - Pro Annual: `price_xxx...`
   - Enterprise Monthly: `price_xxx...`
   - Enterprise Annual: `price_xxx...`

## Step 3: Update Backend Configuration

1. Update `/src/backend/core/pricing_config.py`:
```python
STRIPE_PRODUCTS = {
    'professional': {
        'name': 'TradeSense Pro',
        'monthly_price_id': 'price_YOUR_PRO_MONTHLY_ID',  # Replace
        'annual_price_id': 'price_YOUR_PRO_ANNUAL_ID',    # Replace
        # ... rest of config
    },
    'team': {
        'name': 'TradeSense Enterprise',
        'monthly_price_id': 'price_YOUR_ENTERPRISE_MONTHLY_ID',  # Replace
        'annual_price_id': 'price_YOUR_ENTERPRISE_ANNUAL_ID',    # Replace
        # ... rest of config
    }
}
```

2. Update environment variables (`.env`):
```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_YOUR_SECRET_KEY  # Or sk_test_ for testing
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_PUBLISHABLE_KEY  # Or pk_test_ for testing
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Stripe Price IDs (optional if using pricing_config.py)
STRIPE_PRICE_PRO_MONTHLY=price_YOUR_PRO_MONTHLY_ID
STRIPE_PRICE_PRO_ANNUAL=price_YOUR_PRO_ANNUAL_ID
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_YOUR_ENTERPRISE_MONTHLY_ID
STRIPE_PRICE_ENTERPRISE_ANNUAL=price_YOUR_ENTERPRISE_ANNUAL_ID
```

## Step 4: Update Frontend Configuration

1. Update `/frontend/src/routes/pricing/+page.svelte`:
```javascript
{
    id: 'pro',
    // ... other fields
    stripeProductId: 'price_YOUR_PRO_MONTHLY_ID',
    annualProductId: 'price_YOUR_PRO_ANNUAL_ID',
},
{
    id: 'enterprise',
    // ... other fields
    stripeProductId: 'price_YOUR_ENTERPRISE_MONTHLY_ID',
    annualProductId: 'price_YOUR_ENTERPRISE_ANNUAL_ID'
}
```

2. Add Stripe publishable key to frontend environment:
```bash
# frontend/.env
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_PUBLISHABLE_KEY
```

## Step 5: Set Up Webhooks

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Set endpoint URL: `https://yourdomain.com/api/v1/billing/webhook`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the webhook signing secret and add to `.env` as `STRIPE_WEBHOOK_SECRET`

## Step 6: Test the Integration

### Test Mode
1. Use Stripe test keys (start with `sk_test_` and `pk_test_`)
2. Use test card numbers:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
3. Test the full flow:
   - User selects plan
   - Redirected to Stripe Checkout
   - Completes payment
   - Redirected back to success page
   - Subscription activated

### Verify Webhook Processing
1. Use Stripe CLI for local testing:
```bash
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

2. Trigger test events:
```bash
stripe trigger checkout.session.completed
```

## Step 7: Go Live Checklist

- [ ] Replace all test keys with live keys
- [ ] Update webhook endpoints to production URL
- [ ] Test with real payment method
- [ ] Enable production mode in Stripe Dashboard
- [ ] Set up monitoring and alerts
- [ ] Configure customer portal settings
- [ ] Set up email receipts

## Troubleshooting

### Common Issues

1. **"No price ID found" error**
   - Verify price IDs in `pricing_config.py` match Stripe Dashboard
   - Check environment variables are loaded correctly

2. **Webhook signature verification failed**
   - Ensure `STRIPE_WEBHOOK_SECRET` matches Dashboard
   - Check request headers are forwarded correctly

3. **Checkout session fails**
   - Verify API keys are correct
   - Check product/price IDs exist in Stripe
   - Ensure user has valid email address

### Debug Mode
Enable debug logging:
```python
# In billing router
logger.setLevel(logging.DEBUG)
```

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Validate webhooks** - Always verify signatures
3. **Use HTTPS** - Required for production
4. **Limit API access** - Use restricted keys when possible
5. **Monitor failed payments** - Set up alerts

## Next Steps

1. Set up subscription management UI
2. Implement usage-based billing (if needed)
3. Add invoice download functionality
4. Set up dunning emails for failed payments
5. Implement upgrade/downgrade flows

## Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Checkout Guide](https://stripe.com/docs/checkout)
- [Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)
- [Testing Guide](https://stripe.com/docs/testing)