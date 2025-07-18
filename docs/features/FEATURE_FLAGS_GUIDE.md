# TradeSense Feature Flags Guide

## Overview

The TradeSense feature flags system enables controlled feature rollouts, A/B testing, and dynamic feature management without code deployments. This guide covers implementation, best practices, and common use cases.

## Architecture

### Components

1. **Backend Service** (`feature_flags.py`)
   - Flag evaluation logic
   - Targeting rules engine
   - Cache management
   - Analytics tracking

2. **API Endpoints** (`api/feature_flags.py`)
   - User evaluation endpoints
   - Admin management endpoints
   - Testing and analytics

3. **Frontend Client** (`featureFlags.js`)
   - Flag evaluation
   - Local caching
   - Usage tracking
   - Reactive updates

4. **Admin Interface** (`admin/feature-flags`)
   - Flag creation and management
   - Testing tools
   - Analytics dashboard

## Flag Types

### 1. Boolean Flags
Simple on/off toggles for features.

```python
{
    "key": "new_feature",
    "type": "boolean",
    "default_value": false
}
```

### 2. Percentage Rollout
Gradual feature rollout to a percentage of users.

```python
{
    "key": "beta_feature",
    "type": "percentage",
    "default_value": false,
    "targeting_rules": [{
        "user_percentage": 25
    }]
}
```

### 3. User List
Enable features for specific users.

```python
{
    "key": "early_access",
    "type": "user_list",
    "default_value": false,
    "targeting_rules": [{
        "user_ids": ["user123", "user456"]
    }]
}
```

### 4. A/B Test Variants
Multiple variants with weighted distribution.

```python
{
    "key": "checkout_flow",
    "type": "variant",
    "default_value": "control",
    "variants": {
        "control": {"weight": 50},
        "variant_a": {"weight": 25},
        "variant_b": {"weight": 25}
    }
}
```

## Targeting Rules

### Available Criteria

1. **User Tiers**
   ```json
   {
       "user_tiers": ["pro", "premium"]
   }
   ```

2. **User Percentage**
   ```json
   {
       "user_percentage": 50
   }
   ```

3. **Account Age**
   ```json
   {
       "created_after": "2024-01-01T00:00:00Z",
       "created_before": "2024-12-31T23:59:59Z"
   }
   ```

4. **Trading Activity**
   ```json
   {
       "has_traded": true,
       "min_trades": 10
   }
   ```

5. **Custom Attributes**
   ```json
   {
       "custom_attributes": {
           "beta_tester": true,
           "region": "US"
       }
   }
   ```

### Rule Combination

Multiple rules are evaluated with AND logic:

```json
{
    "targeting_rules": [
        {
            "user_tiers": ["pro", "premium"],
            "user_percentage": 50,
            "min_trades": 5
        }
    ]
}
```

## Frontend Usage

### Basic Usage

```javascript
import featureFlags, { isFeatureEnabled } from '$lib/featureFlags';

// Initialize on app start
await featureFlags.initialize();

// Check if feature is enabled
if (isFeatureEnabled('new_analytics_dashboard')) {
    // Show new dashboard
} else {
    // Show old dashboard
}
```

### Variant Testing

```javascript
import { getFeatureVariant } from '$lib/featureFlags';

const exportFormat = getFeatureVariant('export_format', 'csv');

switch (exportFormat) {
    case 'excel':
        exportAsExcel(data);
        break;
    case 'json':
        exportAsJSON(data);
        break;
    default:
        exportAsCSV(data);
}
```

### Reactive Updates

```svelte
<script>
import { flags } from '$lib/featureFlags';

$: showBetaFeatures = $flags.beta_features_enabled;
</script>

{#if showBetaFeatures}
    <BetaFeatures />
{/if}
```

### Track Usage

```javascript
import { trackFeatureUsage } from '$lib/featureFlags';

// Track when feature is viewed
trackFeatureUsage('ai_insights', 'viewed');

// Track when feature is used
trackFeatureUsage('ai_insights', 'generated_report');
```

## Backend Usage

### Evaluate Flags

```python
from src.backend.features.feature_flags import feature_flag_service

# Evaluate single flag
value = await feature_flag_service.evaluate_flag(
    flag_key="new_feature",
    user=current_user,
    db=db
)

# Evaluate all flags
all_flags = await feature_flag_service.evaluate_all_flags(
    user=current_user,
    db=db
)
```

### Create Custom Flags

```python
# Create a gradual rollout flag
await feature_flag_service.create_flag(
    key="gradual_rollout",
    name="Gradual Feature Rollout",
    description="Rolling out new feature gradually",
    flag_type=FeatureFlagType.PERCENTAGE,
    default_value=False,
    targeting_rules=[{
        "user_percentage": 10,
        "user_tiers": ["pro", "premium"]
    }],
    db=db
)

# Create A/B test
await feature_flag_service.create_flag(
    key="pricing_test",
    name="Pricing Page A/B Test",
    description="Testing different pricing displays",
    flag_type=FeatureFlagType.VARIANT,
    default_value="control",
    variants={
        "control": {"weight": 50},
        "monthly_focus": {"weight": 25},
        "annual_focus": {"weight": 25}
    },
    targeting_rules=[{
        "user_percentage": 100
    }],
    db=db
)
```

## API Endpoints

### User Endpoints

#### Get All Flags
```bash
GET /api/v1/feature-flags/evaluate
Authorization: Bearer <token>

Response:
{
    "flags": {
        "new_analytics": true,
        "export_format": "excel",
        "beta_features": false
    },
    "user_id": "123"
}
```

#### Get Single Flag
```bash
GET /api/v1/feature-flags/evaluate/new_analytics
Authorization: Bearer <token>

Response:
{
    "flag_key": "new_analytics",
    "value": true,
    "user_id": "123"
}
```

### Admin Endpoints

#### List All Flags
```bash
GET /api/v1/feature-flags/?include_inactive=true
Authorization: Bearer <admin-token>
```

#### Create Flag
```bash
POST /api/v1/feature-flags/
Authorization: Bearer <admin-token>
Content-Type: application/json

{
    "key": "new_feature",
    "name": "New Feature",
    "description": "Testing new feature",
    "type": "boolean",
    "default_value": false,
    "targeting_rules": [{
        "user_tiers": ["premium"]
    }]
}
```

#### Update Flag
```bash
PUT /api/v1/feature-flags/{flag_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
    "status": "active",
    "targeting_rules": [{
        "user_percentage": 50
    }]
}
```

## Best Practices

### 1. Naming Conventions

Use descriptive, consistent names:
- Feature toggles: `feature_name_enabled`
- A/B tests: `test_name_variant`
- Rollouts: `feature_name_rollout`

### 2. Gradual Rollouts

Start small and increase gradually:
1. 5% → Internal testing
2. 10% → Early adopters
3. 25% → Broader testing
4. 50% → Half rollout
5. 100% → Full release

### 3. Monitoring

Track key metrics:
- Evaluation frequency
- Error rates per variant
- Performance impact
- User engagement

### 4. Cleanup

Remove flags after full rollout:
1. Set to 100% for all users
2. Monitor for 1-2 weeks
3. Remove flag code
4. Delete flag configuration

### 5. Emergency Kill Switches

For risky features, implement kill switches:

```python
{
    "key": "risky_feature_enabled",
    "type": "boolean",
    "default_value": false,
    "metadata": {
        "emergency_contact": "oncall@tradesense.com",
        "rollback_instructions": "Set to false immediately"
    }
}
```

## Common Use Cases

### 1. Beta Features

```python
# Enable for beta testers
{
    "key": "beta_ai_insights",
    "targeting_rules": [{
        "user_ids": beta_tester_ids,
        "user_tiers": ["premium"]
    }]
}
```

### 2. Performance Testing

```python
# Test new algorithm on small percentage
{
    "key": "new_calculation_engine",
    "targeting_rules": [{
        "user_percentage": 5,
        "custom_attributes": {
            "high_volume_trader": true
        }
    }]
}
```

### 3. Pricing Experiments

```python
# A/B test pricing display
{
    "key": "pricing_display",
    "type": "variant",
    "variants": {
        "monthly_first": {"weight": 33},
        "annual_first": {"weight": 33},
        "side_by_side": {"weight": 34}
    }
}
```

### 4. Feature Sunset

```python
# Gradually remove old feature
{
    "key": "legacy_feature_hidden",
    "targeting_rules": [{
        "user_percentage": 10  # Start with 10%
    }]
}
```

## Analytics

### Tracking Events

Feature flag events are automatically tracked:

```sql
-- Get evaluation metrics
SELECT 
    flag_key,
    value,
    COUNT(*) as evaluations,
    COUNT(DISTINCT user_id) as unique_users
FROM feature_flag_evaluations
WHERE evaluated_at > NOW() - INTERVAL '7 days'
GROUP BY flag_key, value;
```

### A/B Test Analysis

```sql
-- Compare conversion rates
SELECT 
    variant,
    COUNT(DISTINCT user_id) as users,
    SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions,
    AVG(CASE WHEN converted THEN 1.0 ELSE 0.0 END) as conversion_rate
FROM ab_test_results
WHERE flag_key = 'checkout_flow'
GROUP BY variant;
```

## Troubleshooting

### Common Issues

1. **Flag Not Evaluating**
   - Check flag status (must be "active")
   - Verify targeting rules
   - Check user attributes

2. **Inconsistent Values**
   - Clear frontend cache
   - Check for overrides
   - Verify percentage calculation

3. **Performance Issues**
   - Enable caching
   - Reduce evaluation frequency
   - Batch flag requests

### Debug Mode

Enable debug logging:

```javascript
// Frontend
featureFlags.debug = true;

// Backend
import logging
logging.getLogger('feature_flags').setLevel(logging.DEBUG)
```

## Security Considerations

1. **Access Control**
   - Only admins can create/modify flags
   - Users can only evaluate their own flags
   - Audit all flag changes

2. **Data Privacy**
   - Don't expose sensitive targeting rules
   - Anonymize analytics data
   - Respect user preferences

3. **Rate Limiting**
   - Limit evaluation requests
   - Cache aggressively
   - Monitor for abuse

## Migration Guide

### Adding Feature Flags to Existing Features

1. **Identify Feature**
   ```javascript
   // Old code
   function showAdvancedAnalytics() {
       return user.tier === 'premium';
   }
   ```

2. **Create Flag**
   ```json
   {
       "key": "advanced_analytics_enabled",
       "targeting_rules": [{
           "user_tiers": ["premium"]
       }]
   }
   ```

3. **Update Code**
   ```javascript
   // New code
   function showAdvancedAnalytics() {
       return isFeatureEnabled('advanced_analytics_enabled');
   }
   ```

4. **Test & Deploy**
   - Test with different user types
   - Monitor flag evaluations
   - Gradually expand access

## Future Enhancements

1. **Scheduled Flags**
   - Time-based activation
   - Automatic sunset dates

2. **Dependencies**
   - Flag dependencies
   - Conditional flags

3. **Advanced Targeting**
   - Geographic targeting
   - Device-based rules
   - Behavioral targeting

4. **Integration**
   - Webhook notifications
   - Third-party analytics
   - CI/CD integration