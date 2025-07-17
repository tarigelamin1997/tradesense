# TradeSense Billing Implementation Guide

## Overview

The TradeSense billing system is built on Stripe and provides a complete subscription management solution with the following features:

- Multiple subscription tiers (Free, Starter, Professional, Team)
- 14-day free trial for all paid plans
- Monthly and yearly billing options
- Usage-based feature gating
- Self-service subscription management
- Secure webhook handling
- Automatic invoice generation

## Architecture

### Data Models

1. **Subscription** (`src/backend/models/billing.py`)
   - Tracks user subscription status and details
   - Links to Stripe subscription object
   - Manages trial periods and billing cycles

2. **Invoice** 
   - Records payment history
   - Stores invoice PDFs from Stripe
   - Tracks payment status

3. **UsageRecord**
   - Monitors feature usage per billing period
   - Enforces plan limits
   - Resets automatically each period

4. **PlanLimits**
   - Defines feature limits for each plan
   - Controls feature access flags
   - Easily configurable

### Service Layer

**StripeService** (`src/backend/services/stripe_service.py`)
- Handles all Stripe API interactions
- Manages subscription lifecycle
- Processes webhook events
- Enforces usage limits

### API Endpoints

All billing endpoints are available under `/api/v1/billing/`:

- `POST /create-checkout-session` - Start subscription checkout
- `POST /create-portal-session` - Access billing portal
- `GET /subscription` - Get current subscription details
- `GET /usage` - View usage statistics
- `PUT /update-plan` - Change subscription plan
- `DELETE /cancel-subscription` - Cancel subscription
- `GET /invoices` - View invoice history
- `POST /webhook` - Stripe webhook handler

## Setup Instructions

### 1. Environment Variables

Add the following to your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Stripe Price IDs
STRIPE_PRICE_STARTER_MONTHLY=price_starter_monthly_id
STRIPE_PRICE_STARTER_YEARLY=price_starter_yearly_id
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_professional_monthly_id
STRIPE_PRICE_PROFESSIONAL_YEARLY=price_professional_yearly_id
STRIPE_PRICE_TEAM_MONTHLY=price_team_monthly_id
STRIPE_PRICE_TEAM_YEARLY=price_team_yearly_id
```

### 2. Database Migrations

Run the billing tables migration:

```bash
cd src/backend
alembic upgrade head
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Stripe Setup

1. Create products and prices in Stripe Dashboard
2. Set up webhook endpoint: `https://yourdomain.com/api/v1/billing/webhook`
3. Configure webhook to send these events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

## Usage Examples

### Creating a Checkout Session

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/billing/create-checkout-session",
    json={
        "plan": "professional",
        "billing_cycle": "monthly",
        "success_url": "http://localhost:3000/payment-success",
        "cancel_url": "http://localhost:3000/pricing"
    },
    headers={"Authorization": f"Bearer {access_token}"}
)

checkout_url = response.json()["checkout_url"]
# Redirect user to checkout_url
```

### Feature Gating

Use the `requires_plan` decorator to protect endpoints:

```python
from api.v1.billing.router import requires_plan

@router.get("/advanced-analytics")
@requires_plan("professional")
async def get_advanced_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # This endpoint is only accessible to Professional and Team plans
    return {"data": "Advanced analytics"}
```

### Checking Usage Limits

```python
from services.stripe_service import StripeService

# Check if user can create more trades
can_trade, message = StripeService.check_usage_limits(
    user_id=user.id,
    metric="trades",
    db=db
)

if not can_trade:
    raise HTTPException(status_code=403, detail=message)

# Record usage
StripeService.record_usage(
    user_id=user.id,
    metric="trades",
    count=1,
    db=db
)
```

## Testing

### Local Testing with Stripe CLI

1. Install Stripe CLI
2. Login: `stripe login`
3. Forward webhooks: `stripe listen --forward-to localhost:8000/api/v1/billing/webhook`
4. Test cards:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Requires authentication: `4000 0025 0000 3155`

### Unit Tests

Run billing tests:

```bash
pytest src/backend/tests/test_billing.py -v
```

## Subscription Plans

### Free Plan
- 10 trades per month
- 1 portfolio
- 7-day data retention
- Basic features only

### Starter Plan ($29/month)
- 100 trades per month
- 1 portfolio
- 30-day data retention
- Basic features

### Professional Plan ($99/month)
- Unlimited trades
- 5 portfolios
- Unlimited data retention
- API access (1,000 calls/day)
- Advanced analytics
- Export features
- Priority support

### Team Plan ($299/month)
- Everything in Professional
- 5 team seats
- 10,000 API calls/day
- Team collaboration features
- White-label options

## Security Considerations

1. **Webhook Verification**: Always verify Stripe webhook signatures
2. **Idempotency**: Handle duplicate webhook events gracefully
3. **PCI Compliance**: Never store card details locally
4. **Rate Limiting**: Implement rate limits on billing endpoints
5. **Error Handling**: Log errors but don't expose sensitive details

## Troubleshooting

### Common Issues

1. **Webhook signature verification fails**
   - Ensure `STRIPE_WEBHOOK_SECRET` is correct
   - Check request body is raw bytes, not parsed JSON

2. **User already has subscription error**
   - Direct users to billing portal to manage existing subscription
   - Check for orphaned subscriptions in database

3. **Price not configured error**
   - Verify all price IDs are set in environment variables
   - Ensure prices exist in Stripe dashboard

### Debug Mode

Enable debug logging for billing:

```python
import logging
logging.getLogger('src.backend.services.stripe_service').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Metered Billing**: Track and bill for API usage
2. **Coupon Support**: Add discount codes
3. **Tax Handling**: Integrate Stripe Tax
4. **Revenue Analytics**: Build admin dashboard
5. **Dunning Management**: Handle failed payments better
6. **Multi-currency**: Support international pricing

## Support

For billing issues:
1. Check Stripe Dashboard for payment status
2. Review webhook logs in Stripe
3. Check application logs for errors
4. Contact support with subscription ID