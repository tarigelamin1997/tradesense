# A/B Testing Framework Guide

TradeSense includes a comprehensive A/B testing framework for running experiments and optimizing the user experience.

## Overview

The A/B testing framework allows you to:
- Test different variations of features
- Measure impact on key metrics
- Make data-driven decisions
- Roll out changes gradually

## Core Concepts

### Experiments
An experiment tests one or more variations (variants) against a control group to measure impact on specific metrics.

### Variants
Different versions of a feature being tested. Each experiment must have:
- One control variant (baseline)
- One or more treatment variants
- Traffic allocation (weights must sum to 1.0)

### Metrics
Measurable outcomes tracked for each variant:
- **Conversion**: Binary events (signup, purchase)
- **Revenue**: Monetary values
- **Engagement**: User interactions
- **Retention**: User return rates
- **Custom**: Any trackable metric

### Assignment Methods
- **Deterministic**: Consistent assignment based on user ID
- **Random**: Random assignment per request
- **Sticky**: Remembers previous assignments
- **Cohort-based**: Assignment based on user cohorts

## API Usage

### For Frontend Developers

#### Get Variant Assignment
```javascript
// Get all experiment assignments for current user
const assignments = await api.get('/experiments/assignments');

// Get specific experiment assignment
const assignment = await api.get('/experiments/assignment/pricing_page_v2');
if (assignment) {
    // Use variant configuration
    const { variant_id, config } = assignment;
    if (config.show_value_bullets) {
        // Show value propositions
    }
}
```

#### Track Conversions
```javascript
// Track a conversion event
await api.post('/experiments/track', {
    experiment_id: 'pricing_page_v2',
    metric_id: 'pro_conversion',
    value: 1.0,
    metadata: {
        plan: 'pro',
        price: 29.99
    }
});
```

### For Administrators

#### Create Experiment
```javascript
const experiment = {
    id: 'new_feature_test',
    name: 'New Feature Test',
    description: 'Testing new feature adoption',
    hypothesis: 'New feature will increase engagement by 25%',
    variants: [
        {
            id: 'control',
            name: 'Without Feature',
            weight: 0.5,
            is_control: true,
            config: { show_feature: false }
        },
        {
            id: 'with_feature',
            name: 'With Feature',
            weight: 0.5,
            config: { show_feature: true }
        }
    ],
    metrics: [
        {
            id: 'feature_adoption',
            name: 'Feature Adoption Rate',
            type: 'conversion',
            event_name: 'feature_used',
            success_criteria: { is_primary: true, min_improvement: 0.25 }
        }
    ],
    targeting_rules: {
        new_users_only: { max_days: 7 }
    },
    min_sample_size: 1000
};

await api.post('/experiments/create', experiment);
```

#### Start/Stop Experiment
```javascript
// Start experiment
await api.post('/experiments/experiment_id/start');

// Stop experiment
await api.post('/experiments/experiment_id/stop?reason=Reached+significance');
```

#### View Results
```javascript
const results = await api.get('/experiments/experiment_id/results');
// Returns statistical analysis including p-values, confidence intervals, and lift
```

## Targeting Rules

### New Users Only
```json
{
    "new_users_only": {
        "max_days": 7
    }
}
```

### Subscription Tier
```json
{
    "subscription_tier": {
        "tiers": ["free", "basic"]
    }
}
```

### Percentage Rollout
```json
{
    "percentage_rollout": {
        "percentage": 50
    }
}
```

### Custom Attributes
```json
{
    "custom_attribute": {
        "attribute": "country",
        "value": "US"
    }
}
```

## Pre-built Experiments

The framework includes templates for common experiments:

### Pricing Page Test
- Tests different pricing page layouts
- Measures conversion to paid plans
- Targets free tier users only

### Onboarding Flow Test
- Compares streamlined vs full onboarding
- Measures completion rates
- Targets new users only

### Email Frequency Test
- Tests daily vs weekly vs bi-weekly emails
- Measures engagement and unsubscribe rates
- Uses percentage rollout for safety

## Statistical Analysis

### Sample Size Calculation
```javascript
const sampleSize = await api.post('/experiments/calculate-sample-size', {
    baseline_rate: 0.05,           // 5% baseline conversion
    minimum_detectable_effect: 0.2, // 20% relative improvement
    power: 0.8,                    // 80% statistical power
    significance_level: 0.05       // 95% confidence
});
```

### Duration Estimation
```javascript
const duration = await api.get(
    '/experiments/experiment_id/duration?daily_traffic=1000'
);
```

## Best Practices

1. **Clear Hypothesis**: Define what you're testing and expected outcome
2. **Single Variable**: Test one change at a time for clear results
3. **Adequate Sample Size**: Ensure statistical significance
4. **Run Full Duration**: Don't stop experiments early
5. **Monitor Metrics**: Watch for unexpected negative impacts
6. **Document Results**: Record learnings for future reference

## Implementation Examples

### Feature Toggle
```svelte
<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    
    let showNewFeature = false;
    
    onMount(async () => {
        const assignment = await api.get('/experiments/assignment/new_feature_v1');
        if (assignment?.config?.show_feature) {
            showNewFeature = true;
            
            // Track exposure
            await api.post('/experiments/track', {
                experiment_id: 'new_feature_v1',
                metric_id: 'feature_exposure'
            });
        }
    });
</script>

{#if showNewFeature}
    <NewFeatureComponent />
{:else}
    <OldFeatureComponent />
{/if}
```

### Conversion Tracking
```javascript
// In subscription flow
async function upgradeToPro() {
    // Process upgrade...
    
    // Track experiment conversion
    const assignments = await api.get('/experiments/assignments');
    for (const assignment of assignments) {
        if (assignment.experiment_id.includes('pricing')) {
            await api.post('/experiments/track', {
                experiment_id: assignment.experiment_id,
                metric_id: 'pro_conversion',
                value: 29.99,
                metadata: { plan: 'pro' }
            });
        }
    }
}
```

## Database Schema

### Core Tables
- `experiments`: Experiment configurations
- `experiment_assignments`: User-variant mappings
- `experiment_events`: All tracked events
- `experiment_results`: Cached analysis results

### Event Types
- `assignment`: User assigned to variant
- `exposure`: User saw the variant
- `conversion`: User completed target action

## Monitoring

- Check experiment dashboard at `/admin/experiments`
- Monitor sample sizes and conversion rates
- Watch for SRM (Sample Ratio Mismatch)
- Review statistical significance before decisions

## Common Issues

### Low Statistical Power
- Increase sample size
- Extend experiment duration
- Focus on larger effect sizes

### Sample Ratio Mismatch
- Check assignment logic
- Verify targeting rules
- Look for technical issues

### Inconclusive Results
- May need larger sample
- Effect size might be too small
- Consider different metrics