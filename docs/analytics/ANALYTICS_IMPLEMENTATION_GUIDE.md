# TradeSense Analytics Implementation Guide

## Overview

TradeSense implements comprehensive user analytics to track behavior, measure feature adoption, and provide insights for data-driven product decisions. The analytics system is privacy-focused and GDPR-compliant.

## Architecture

### Components

1. **Backend Analytics**
   - Event collection and storage
   - Real-time processing
   - Batch analytics
   - Data aggregation

2. **Frontend Analytics**
   - Automatic page tracking
   - User interactions
   - Performance metrics
   - Error tracking

3. **Analytics API**
   - RESTful endpoints
   - Real-time data access
   - Export capabilities

## Event Types

### User Events
- `page_view` - Page visits
- `sign_up` - New user registration
- `login` - User login
- `logout` - User logout

### Trade Events
- `trade_created` - New trade added
- `trade_updated` - Trade modified
- `trade_deleted` - Trade removed
- `trade_imported` - Bulk import

### Feature Events
- `analytics_viewed` - Analytics dashboard accessed
- `report_generated` - Report created
- `journal_entry_created` - Journal entry added
- `playbook_created` - Trading playbook created

### Subscription Events
- `subscription_started` - New subscription
- `subscription_upgraded` - Plan upgrade
- `subscription_downgraded` - Plan downgrade
- `subscription_cancelled` - Cancellation

### Engagement Events
- `feature_discovered` - Feature first use
- `tutorial_completed` - Onboarding completion
- `help_accessed` - Help/support accessed
- `feedback_submitted` - User feedback

## Frontend Implementation

### Basic Setup

```javascript
import analytics from '$lib/analytics';

// Track page view (automatic)
// Handled by analytics library

// Track user action
analytics.trackAction('button_clicked', 'navigation', {
    button_name: 'Dashboard',
    section: 'header'
});

// Track feature usage
analytics.trackFeature('advanced_analytics', {
    filters_used: ['date_range', 'symbol'],
    chart_type: 'candlestick'
});
```

### Trade Tracking

```javascript
// After creating a trade
analytics.trackTrade('create', {
    id: trade.id,
    symbol: trade.symbol,
    trade_type: trade.trade_type,
    quantity: trade.quantity,
    entry_price: trade.entry_price,
    profit_loss: trade.profit_loss
});

// After importing trades
analytics.track('trade_imported', {
    count: trades.length,
    source: 'csv',
    symbols: [...new Set(trades.map(t => t.symbol))]
});
```

### Form Tracking

```javascript
// Track form interactions
analytics.trackForm('trade_entry', 'started');

// On submission
analytics.trackForm('trade_entry', 'submitted', {
    fields_filled: 8,
    time_to_complete: 45 // seconds
});

// On abandonment
analytics.trackForm('trade_entry', 'abandoned', {
    last_field: 'exit_price',
    percent_complete: 75
});
```

### Performance Tracking

```javascript
// Track custom timing
const startTime = performance.now();

// ... perform operation ...

analytics.trackTiming('api_call', 'fetch_trades', 
    performance.now() - startTime,
    { endpoint: '/api/v1/trades' }
);
```

### Error Tracking

```javascript
try {
    // ... code that might fail ...
} catch (error) {
    analytics.trackError(error, {
        context: 'trade_submission',
        user_action: 'save_trade'
    });
}
```

## Backend Implementation

### Tracking Events

```python
from src.backend.analytics import track_feature_usage, track_trade_analytics

# In API endpoints
@router.post("/trades")
async def create_trade(trade: TradeCreate, user: User = Depends(get_current_user)):
    # ... create trade logic ...
    
    # Track the event
    await track_trade_analytics(
        user_id=str(user.id),
        trade_id=str(new_trade.id),
        action="create",
        trade_details={
            "symbol": trade.symbol,
            "trade_type": trade.trade_type,
            "quantity": trade.quantity,
            "value": trade.entry_price * trade.quantity
        }
    )
    
    return new_trade

# Track feature usage
@track_feature_usage("advanced_analytics")
async def get_advanced_analytics(user: User = Depends(get_current_user)):
    # ... analytics logic ...
    return analytics_data
```

### Querying Analytics

```python
from src.backend.analytics import user_analytics, product_analytics

# Get user journey
journey = await user_analytics.get_user_journey(
    user_id=user_id,
    start_date=datetime.utcnow() - timedelta(days=30)
)

# Get product metrics
metrics = await product_analytics.get_product_metrics()

# Cohort analysis
cohorts = await user_analytics.get_cohort_analysis(
    cohort_type="signup_month",
    metric="retention"
)

# Funnel analysis
funnel = await user_analytics.get_funnel_analysis(
    funnel_steps=["sign_up", "trade_created", "subscription_started"]
)
```

## Analytics API

### Track Event
```http
POST /api/v1/analytics/track
Authorization: Bearer <token>

{
    "event_type": "feature_discovered",
    "properties": {
        "feature_name": "advanced_analytics",
        "source": "dashboard_link"
    },
    "page_url": "https://tradesense.com/analytics"
}
```

### Get User Journey
```http
GET /api/v1/analytics/user/journey?start_date=2024-01-01
Authorization: Bearer <token>
```

### Product Metrics (Admin)
```http
GET /api/v1/analytics/product/metrics
Authorization: Bearer <admin-token>
```

### Funnel Analysis (Admin)
```http
POST /api/v1/analytics/funnel/analysis
Authorization: Bearer <admin-token>

{
    "funnel_steps": ["sign_up", "trade_created", "subscription_started"],
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

## Privacy & Compliance

### Data Collection Principles

1. **Minimal Data Collection**
   - Only collect necessary data
   - No personal information in properties
   - Hash sensitive data (IP addresses)

2. **User Consent**
   - Cookie consent banner
   - Opt-out mechanism
   - Clear privacy policy

3. **Data Retention**
   - 90-day default retention
   - Automatic purging
   - User deletion rights

### GDPR Compliance

```python
# User data export
@router.get("/api/v1/user/data-export")
async def export_user_data(user: User = Depends(get_current_user)):
    # Export all user data including analytics
    return await generate_user_data_export(user.id)

# Data deletion
@router.delete("/api/v1/user/data")
async def delete_user_data(user: User = Depends(get_current_user)):
    # Delete all user data including analytics
    await delete_all_user_data(user.id)
```

## Best Practices

### 1. Event Naming
- Use consistent naming convention
- Be descriptive but concise
- Use underscores for separation
- Group related events

### 2. Properties
- Include relevant context
- Avoid high-cardinality values
- Don't include PII
- Keep property names consistent

### 3. Performance
- Batch events when possible
- Use async tracking
- Implement retry logic
- Monitor queue size

### 4. Testing
```javascript
// Test analytics in development
if (import.meta.env.DEV) {
    window.analytics = analytics;
    analytics.debug = true;
}
```

## Dashboards & Reports

### Key Metrics Dashboard
- Daily/Weekly/Monthly Active Users
- Feature adoption rates
- User retention
- Conversion funnels
- Revenue metrics

### User Behavior Dashboard
- User journeys
- Feature discovery paths
- Drop-off points
- Engagement patterns

### Performance Dashboard
- Page load times
- API response times
- Error rates
- Web Vitals

## Alerts & Monitoring

Configure alerts for:
- Significant drop in user activity
- High error rates
- Failed event processing
- Queue buildup

## Troubleshooting

### Events Not Tracking
1. Check network tab for failed requests
2. Verify authentication token
3. Check event type validity
4. Review browser console for errors

### Missing Data
1. Verify event batching settings
2. Check Redis connectivity
3. Review background job processing
4. Confirm database writes

### Performance Issues
1. Adjust batch size
2. Increase flush interval
3. Optimize database indexes
4. Scale Redis if needed

## Future Enhancements

1. **Machine Learning**
   - Predictive analytics
   - Anomaly detection
   - User segmentation

2. **Real-time Analytics**
   - Live dashboards
   - Instant notifications
   - Stream processing

3. **Advanced Features**
   - Session replay
   - Heatmaps
   - A/B testing integration