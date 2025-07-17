# Trading Alerts Implementation

## Overview

TradeSense now features a comprehensive automated trading alerts system that monitors trading activity, market conditions, and account metrics to notify users of important events in real-time.

## Alert Types

### 1. Price Alerts
- **Price Above/Below**: Trigger when an asset reaches a specific price
- **Price Change %**: Alert on significant percentage moves

### 2. Performance Alerts
- **Daily/Weekly P&L**: Monitor profit/loss targets
- **Win Rate**: Alert when win rate drops below threshold
- **Win/Loss Streaks**: Notify on consecutive winning or losing trades

### 3. Risk Alerts
- **Drawdown**: Alert when portfolio drawdown exceeds limits
- **Position Size**: Warn about large position sizes
- **Exposure Limits**: Monitor total market exposure

### 4. Pattern Alerts
- **Pattern Detection**: Alert when technical patterns are identified
- **Strategy Signals**: Notify on strategy-specific conditions

### 5. Market Alerts
- **Volume Spikes**: Detect unusual trading volume
- **Volatility**: Alert on market volatility changes
- **News Sentiment**: Monitor news impact (future feature)

### 6. Account Alerts
- **Margin Calls**: Critical margin level warnings
- **Account Balance**: Low balance notifications
- **Trade Execution**: Confirm trade executions

## Technical Architecture

### Backend Components

1. **Alert Service** (`/src/backend/alerts/alert_service.py`)
   - Core alert evaluation engine
   - Runs every 60 seconds to check conditions
   - Supports complex multi-condition alerts
   - Handles notification delivery

2. **Database Schema**
   - `trading_alerts`: Stores alert configurations
   - `alert_history`: Tracks trigger history
   - `alert_templates`: Predefined alert templates
   - `market_data_cache`: Real-time data for alerts

3. **API Endpoints**
   - `/api/v1/alerts/create` - Create new alert
   - `/api/v1/alerts/list` - List user alerts
   - `/api/v1/alerts/{id}` - Get/update/delete alert
   - `/api/v1/alerts/{id}/toggle` - Enable/disable alert
   - `/api/v1/alerts/test/{id}` - Test alert manually
   - `/api/v1/alerts/templates/list` - Get templates
   - `/api/v1/alerts/history/list` - View trigger history
   - `/api/v1/alerts/stats/overview` - Alert statistics

### Frontend Components

1. **Alert Management Page** (`/frontend/src/routes/alerts/+page.svelte`)
   - Dashboard showing all alerts
   - Template browser
   - Trigger history viewer
   - Real-time notification display

2. **Create Alert Modal** (`/frontend/src/lib/components/alerts/CreateAlertModal.svelte`)
   - 3-step wizard interface
   - Dynamic condition builder
   - Channel selection
   - Advanced settings

## Features

### 1. Multi-Channel Notifications
- **Email**: Detailed HTML emails with trigger data
- **SMS**: Concise text messages via Twilio
- **In-App**: Real-time WebSocket notifications
- **Webhook**: POST to custom URLs for integrations

### 2. Alert Configuration
- **Conditions**: Multiple conditions with AND logic
- **Cooldown**: Prevent alert spam (1-1440 minutes)
- **Daily Limits**: Cap triggers per day
- **Expiration**: Auto-expire time-based alerts
- **Priority Levels**: Low, Medium, High, Critical

### 3. Smart Features
- **Symbol Filtering**: Monitor specific tickers
- **Strategy Filtering**: Alert on specific strategies
- **Rate Limiting**: 5 failed attempts trigger lockout
- **Template System**: Quick setup from presets

### 4. Subscription Tiers
- **Free**: 5 alerts
- **Starter**: 20 alerts
- **Pro**: 50 alerts
- **Premium**: 100 alerts

## User Flow

### Creating an Alert

1. **Choose Type**: Select from categories or use template
2. **Set Conditions**: Define trigger criteria
3. **Configure Notifications**: Select channels and settings
4. **Activate**: Alert begins monitoring immediately

### Alert Lifecycle

1. **Active**: Monitoring conditions
2. **Triggered**: Condition met, notifications sent
3. **Cooldown**: Waiting before next trigger
4. **Disabled**: Manually paused
5. **Expired**: Reached expiration date

## Configuration

### Environment Variables

```bash
# Twilio (for SMS alerts)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# Alert Settings
ALERT_EVALUATION_INTERVAL=60  # seconds
ALERT_MAX_RETRIES=3
ALERT_TIMEOUT=30  # seconds
```

### Notification Templates

Customize notification messages:

```json
{
  "notification_template": {
    "email_subject": "🚨 {{alert_name}} Triggered",
    "sms_message": "TradeSense: {{alert_name}} - {{current_value}}"
  }
}
```

## Real-Time Updates

### WebSocket Integration

```javascript
// Frontend WebSocket connection
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'notification' && data.data.type === 'alert') {
    // Show in-app notification
    showNotification(data.data);
  }
};
```

### Push Notifications (Future)
- Mobile app integration
- Browser push notifications
- Desktop notifications

## Monitoring & Metrics

### Prometheus Metrics
- `tradesense_alerts_created_total` - Alert creation count
- `tradesense_alerts_triggered_total` - Trigger count by type
- `tradesense_notifications_sent_total` - Notifications by channel
- `tradesense_alert_errors_total` - Evaluation errors

### Admin Dashboard
- Total alerts by type
- Trigger frequency analysis
- Channel success rates
- User adoption metrics

## Best Practices

### 1. Alert Design
- **Be Specific**: Clear, actionable conditions
- **Avoid Noise**: Use appropriate cooldowns
- **Test First**: Use test feature before activating
- **Review Regularly**: Remove outdated alerts

### 2. Performance
- **Limit Conditions**: Max 5 conditions per alert
- **Symbol Scope**: Filter by symbols when possible
- **Reasonable Cooldowns**: Minimum 60 minutes recommended

### 3. Notifications
- **Channel Selection**: Match urgency to channel
- **Quiet Hours**: Configure in notification preferences
- **Webhook Security**: Use HTTPS and authentication

## Examples

### Daily P&L Alert
```json
{
  "name": "Daily Profit Target",
  "type": "daily_pnl",
  "conditions": [{
    "field": "current_value",
    "operator": "gte",
    "value": 1000
  }],
  "channels": ["email", "in_app"],
  "priority": "high",
  "cooldown_minutes": 1440
}
```

### Loss Streak Warning
```json
{
  "name": "3 Losses Alert",
  "type": "loss_streak",
  "conditions": [{
    "field": "current_value",
    "operator": "gte",
    "value": 3
  }],
  "channels": ["email", "sms"],
  "priority": "critical",
  "cooldown_minutes": 360
}
```

### Price Target Alert
```json
{
  "name": "SPY Above 500",
  "type": "price_above",
  "conditions": [{
    "field": "current_price",
    "operator": "gt",
    "value": 500
  }],
  "channels": ["in_app"],
  "symbols": ["SPY"],
  "priority": "medium",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

## Troubleshooting

### Common Issues

1. **Alert Not Triggering**
   - Check conditions are properly set
   - Verify data is available
   - Review cooldown settings
   - Check expiration date

2. **Notifications Not Received**
   - Verify channel configuration
   - Check notification preferences
   - Review spam folders (email)
   - Confirm phone number (SMS)

3. **Too Many Alerts**
   - Increase cooldown period
   - Set daily limits
   - Review conditions
   - Use priority levels

## Future Enhancements

1. **Machine Learning Alerts**
   - Anomaly detection
   - Predictive alerts
   - Pattern learning

2. **Advanced Conditions**
   - OR logic support
   - Nested conditions
   - Time-based windows

3. **Integration Expansion**
   - Slack notifications
   - Discord webhooks
   - Trading platform APIs

4. **Mobile Features**
   - Push notifications
   - Alert management app
   - Voice alerts