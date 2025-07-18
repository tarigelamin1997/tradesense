# TradeSense API Endpoints Documentation
**Version:** 1.0  
**Base URL:** `https://api.tradesense.com/api/v1`  
**Authentication:** Bearer JWT Token

## Authentication Endpoints

### POST /auth/register
Create a new user account
```json
Request:
{
  "username": "string",
  "email": "string",
  "password": "string"
}

Response: 201
{
  "id": 123,
  "username": "string",
  "email": "string",
  "email_verified": false,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### POST /auth/login
Authenticate user and receive tokens
```json
Request:
{
  "username": "string",
  "password": "string"
}

Response: 200
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh
Refresh access token
```json
Request:
{
  "refresh_token": "string"
}

Response: 200
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/logout
Invalidate refresh token
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "message": "Successfully logged out"
}
```

### POST /auth/verify-email/{token}
Verify email address
```json
Response: 200
{
  "message": "Email verified successfully"
}
```

### POST /auth/forgot-password
Request password reset
```json
Request:
{
  "email": "string"
}

Response: 200
{
  "message": "Password reset email sent"
}
```

### POST /auth/reset-password
Reset password with token
```json
Request:
{
  "token": "string",
  "new_password": "string"
}

Response: 200
{
  "message": "Password reset successfully"
}
```

## User Management Endpoints

### GET /users/me
Get current user profile
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "id": 123,
  "username": "string",
  "email": "string",
  "email_verified": true,
  "plan": "pro",
  "created_at": "2025-01-15T10:00:00Z",
  "settings": {}
}
```

### PUT /users/me
Update user profile
```json
Headers: Authorization: Bearer <token>

Request:
{
  "username": "string",
  "full_name": "string",
  "timezone": "America/New_York"
}

Response: 200
{
  "id": 123,
  "username": "string",
  "full_name": "string",
  "timezone": "America/New_York"
}
```

### PUT /users/settings
Update user settings
```json
Headers: Authorization: Bearer <token>

Request:
{
  "notifications": {
    "email_alerts": true,
    "weekly_reports": false
  },
  "display": {
    "theme": "light",
    "compact_mode": false
  }
}

Response: 200
{
  "message": "Settings updated successfully"
}
```

### POST /users/onboarding
Save onboarding preferences
```json
Headers: Authorization: Bearer <token>

Request:
{
  "goals": ["improve_consistency", "risk_management"],
  "experience": "intermediate",
  "markets": ["stocks", "options"],
  "trading_style": "day_trading"
}

Response: 200
{
  "message": "Onboarding completed"
}
```

## Trade Management Endpoints

### GET /trades
Get user's trades with filtering
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- search: string (symbol search)
- symbol: string
- side: long|short
- start_date: ISO date
- end_date: ISO date
- min_pnl: number
- max_pnl: number
- limit: number (default 100)
- offset: number (default 0)
- sort_by: entryDate|exitDate|pnl|symbol
- order: asc|desc

Response: 200
{
  "trades": [
    {
      "id": 1,
      "symbol": "AAPL",
      "side": "long",
      "entry_price": 150.50,
      "exit_price": 155.25,
      "quantity": 100,
      "entry_date": "2025-01-10T09:30:00Z",
      "exit_date": "2025-01-10T14:30:00Z",
      "pnl": 475.00,
      "pnl_percent": 3.16,
      "strategy": "momentum",
      "notes": "Strong breakout pattern"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

### POST /trades
Create a new trade
```json
Headers: Authorization: Bearer <token>

Request:
{
  "symbol": "AAPL",
  "side": "long",
  "entry_price": 150.50,
  "exit_price": 155.25,
  "quantity": 100,
  "entry_date": "2025-01-10T09:30:00Z",
  "exit_date": "2025-01-10T14:30:00Z",
  "strategy": "momentum",
  "notes": "Strong breakout pattern"
}

Response: 201
{
  "id": 123,
  "symbol": "AAPL",
  "pnl": 475.00,
  "pnl_percent": 3.16
}
```

### GET /trades/{id}
Get specific trade details
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "id": 123,
  "symbol": "AAPL",
  "side": "long",
  "entry_price": 150.50,
  "exit_price": 155.25,
  "quantity": 100,
  "entry_date": "2025-01-10T09:30:00Z",
  "exit_date": "2025-01-10T14:30:00Z",
  "pnl": 475.00,
  "pnl_percent": 3.16,
  "strategy": "momentum",
  "notes": "Strong breakout pattern",
  "created_at": "2025-01-10T15:00:00Z",
  "updated_at": "2025-01-10T15:00:00Z"
}
```

### PUT /trades/{id}
Update a trade
```json
Headers: Authorization: Bearer <token>

Request:
{
  "notes": "Updated notes",
  "strategy": "breakout"
}

Response: 200
{
  "id": 123,
  "message": "Trade updated successfully"
}
```

### DELETE /trades/{id}
Delete a trade
```json
Headers: Authorization: Bearer <token>

Response: 204 No Content
```

### POST /trades/import
Import trades from CSV
```json
Headers: 
- Authorization: Bearer <token>
- Content-Type: multipart/form-data

Request:
- file: CSV file
- broker: td_ameritrade|interactive_brokers|etrade|custom
- mapping: JSON (for custom format)

Response: 201
{
  "imported": 45,
  "failed": 2,
  "errors": [
    {
      "row": 23,
      "error": "Invalid date format"
    }
  ]
}
```

### GET /trades/export
Export trades to file
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- format: csv|json|excel
- start_date: ISO date
- end_date: ISO date

Response: 200
Content-Type: text/csv or application/json
Content-Disposition: attachment; filename="trades_2025-01-15.csv"
```

## Journal Endpoints

### GET /journal/entries
Get journal entries
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- search: string
- mood: string
- start_date: ISO date
- end_date: ISO date
- limit: number
- offset: number

Response: 200
{
  "entries": [
    {
      "id": 1,
      "title": "Great trading day",
      "content": "<p>Today was exceptional...</p>",
      "mood": "confident",
      "confidence": 8,
      "tags": ["breakout", "momentum"],
      "trade_ids": [123, 124],
      "created_at": "2025-01-15T16:00:00Z"
    }
  ],
  "total": 50
}
```

### POST /journal/entries
Create journal entry
```json
Headers: Authorization: Bearer <token>

Request:
{
  "title": "Great trading day",
  "content": "<p>Today was exceptional...</p>",
  "mood": "confident",
  "confidence": 8,
  "tags": ["breakout", "momentum"],
  "trade_ids": [123, 124]
}

Response: 201
{
  "id": 123,
  "message": "Journal entry created"
}
```

### GET /journal/entries/{id}
Get specific journal entry
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "id": 123,
  "title": "Great trading day",
  "content": "<p>Today was exceptional...</p>",
  "mood": "confident",
  "confidence": 8,
  "tags": ["breakout", "momentum"],
  "trade_ids": [123, 124],
  "created_at": "2025-01-15T16:00:00Z",
  "updated_at": "2025-01-15T16:00:00Z"
}
```

### PUT /journal/entries/{id}
Update journal entry
```json
Headers: Authorization: Bearer <token>

Request:
{
  "title": "Updated title",
  "content": "<p>Updated content...</p>"
}

Response: 200
{
  "message": "Journal entry updated"
}
```

### DELETE /journal/entries/{id}
Delete journal entry
```json
Headers: Authorization: Bearer <token>

Response: 204 No Content
```

### GET /journal/insights
Get AI-powered journal insights
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- timeframe: 7d|30d|90d

Response: 200
{
  "insights": [
    {
      "type": "pattern",
      "title": "Overtrading on Mondays",
      "description": "You tend to take 40% more trades on Mondays",
      "severity": "medium",
      "suggestions": ["Consider reducing position sizes", "Review Monday trades"]
    }
  ]
}
```

## Portfolio Endpoints

### GET /portfolio
Get portfolio overview
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- timeframe: 7d|30d|90d|1y|all
- asset_class: stocks|options|futures

Response: 200
{
  "total_value": 125430.50,
  "total_pnl": 12543.25,
  "total_pnl_percent": 11.12,
  "positions": [...],
  "allocations": [...],
  "performance": [...]
}
```

### GET /portfolio/positions
Get current positions
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- asset_class: stocks|options|futures
- sort_by: value|pnl|allocation

Response: 200
{
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "avg_cost": 150.25,
      "current_price": 185.50,
      "value": 18550.00,
      "pnl": 3525.00,
      "pnl_percent": 23.45,
      "allocation": 14.8
    }
  ]
}
```

### GET /portfolio/performance
Get portfolio performance over time
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- timeframe: 7d|30d|90d|1y|all
- interval: daily|weekly|monthly

Response: 200
{
  "performance": [
    {
      "date": "2025-01-01",
      "value": 100000,
      "pnl": 0,
      "pnl_percent": 0
    },
    {
      "date": "2025-01-15",
      "value": 112543,
      "pnl": 12543,
      "pnl_percent": 12.54
    }
  ]
}
```

### GET /portfolio/allocations
Get asset allocation breakdown
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "allocations": [
    {
      "asset": "Technology",
      "value": 45000,
      "percentage": 35.9
    },
    {
      "asset": "Healthcare",
      "value": 28000,
      "percentage": 22.3
    }
  ]
}
```

### GET /portfolio/risk-metrics
Get portfolio risk metrics
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "sharpe_ratio": 1.85,
  "max_drawdown": -12.5,
  "win_rate": 68.5,
  "profit_factor": 2.3,
  "avg_win": 485.50,
  "avg_loss": -211.25
}
```

## Analytics Endpoints

### GET /analytics/performance
Get performance analytics
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- timeframe: 7d|30d|90d|1y|all
- group_by: day|week|month

Response: 200
{
  "metrics": {
    "total_trades": 150,
    "win_rate": 68.5,
    "profit_factor": 2.3,
    "total_pnl": 12543.25,
    "avg_win": 485.50,
    "avg_loss": -211.25,
    "best_trade": 2150.00,
    "worst_trade": -875.00
  },
  "daily_pnl": [...],
  "cumulative_pnl": [...]
}
```

### GET /analytics/execution-quality
Get execution quality metrics
```json
Headers: Authorization: Bearer <token>

Query Parameters:
- timeframe: 7d|30d|90d

Response: 200
{
  "metrics": {
    "avg_slippage": 0.05,
    "fill_rate": 98.5,
    "avg_hold_time": "4h 23m",
    "timing_efficiency": 0.82
  },
  "details": [...]
}
```

### GET /analytics/strategies
Get strategy performance comparison
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "strategies": [
    {
      "name": "momentum",
      "trades": 45,
      "win_rate": 71.1,
      "total_pnl": 8456.25,
      "avg_pnl": 187.92
    },
    {
      "name": "mean_reversion",
      "trades": 38,
      "win_rate": 65.8,
      "total_pnl": 4087.00,
      "avg_pnl": 107.55
    }
  ]
}
```

## Playbook Endpoints

### GET /playbook/strategies
Get trading strategies
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "strategies": [
    {
      "id": 1,
      "name": "Morning Breakout",
      "description": "Trade breakouts in first hour",
      "rules": [...],
      "performance": {
        "trades": 45,
        "win_rate": 71.1,
        "avg_pnl": 187.92
      }
    }
  ]
}
```

### POST /playbook/strategies
Create new strategy
```json
Headers: Authorization: Bearer <token>

Request:
{
  "name": "Morning Breakout",
  "description": "Trade breakouts in first hour",
  "rules": {
    "entry": ["Price breaks above opening range high"],
    "exit": ["Stop loss at range low", "Target 2:1 risk/reward"],
    "risk": ["Max 1% per trade"]
  }
}

Response: 201
{
  "id": 123,
  "message": "Strategy created"
}
```

## Billing Endpoints

### GET /billing/subscription
Get current subscription details
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "plan": "pro",
  "status": "active",
  "current_period_start": "2025-01-01",
  "current_period_end": "2025-02-01",
  "cancel_at_period_end": false,
  "payment_method": {
    "type": "card",
    "last4": "4242",
    "brand": "visa"
  }
}
```

### POST /billing/create-checkout-session
Create Stripe checkout session
```json
Headers: Authorization: Bearer <token>

Request:
{
  "price_id": "pro_monthly"
}

Response: 200
{
  "checkout_url": "https://checkout.stripe.com/pay/..."
}
```

### POST /billing/cancel-subscription
Cancel subscription
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "message": "Subscription will be cancelled at period end",
  "cancel_at": "2025-02-01"
}
```

### GET /billing/usage
Get API usage statistics
```json
Headers: Authorization: Bearer <token>

Response: 200
{
  "period": "2025-01",
  "api_calls": {
    "used": 15420,
    "limit": 30000
  },
  "storage": {
    "used_mb": 125,
    "limit_mb": 1000
  },
  "trades": {
    "count": 245,
    "limit": "unlimited"
  }
}
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "detail": "The password must be at least 8 characters long"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "detail": "Upgrade to Pro plan to access this feature"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "detail": "Trade with id 123 not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "detail": "Please retry after 60 seconds",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

## Rate Limiting

- **Free tier:** 100 requests/hour
- **Pro tier:** 1000 requests/hour  
- **Enterprise tier:** Unlimited

Rate limit headers included in all responses:
- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Pagination

List endpoints support pagination via:
- `limit`: Number of items per page (max 100)
- `offset`: Number of items to skip
- Response includes `total` count for pagination UI

## Webhooks (Coming Soon)

Enterprise customers can configure webhooks for:
- Trade creation/updates
- Journal entries
- Performance alerts
- Account events

---

**Note:** This documentation reflects the current API implementation. Some endpoints marked as "UI ready" may return mock data until backend integration is complete.