# TradeSense API Documentation

## Overview

The TradeSense API provides programmatic access to trading analytics, portfolio management, and trade journaling features. 

**Base URL**: `https://api.tradesense.com`  
**API Version**: `v1`  
**Protocol**: `HTTPS`  
**Data Format**: `JSON`

## Authentication

TradeSense uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "123",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

## Rate Limiting

API rate limits vary by subscription tier:

| Tier | Requests/Minute | Requests/Hour | Concurrent |
|------|-----------------|---------------|------------|
| Free | 60 | 1,000 | 5 |
| Pro | 300 | 10,000 | 20 |
| Enterprise | 1,000 | 100,000 | 100 |

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Endpoints

### Authentication

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh-token>
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <access-token>
```

### Trades

#### List Trades
```http
GET /api/v1/trades?limit=50&offset=0&symbol=AAPL&start_date=2024-01-01
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (int): Number of results (default: 50, max: 100)
- `offset` (int): Pagination offset
- `symbol` (string): Filter by symbol
- `start_date` (date): Filter by start date
- `end_date` (date): Filter by end date
- `trade_type` (string): BUY or SELL
- `min_profit` (float): Minimum profit/loss
- `max_profit` (float): Maximum profit/loss

**Response:**
```json
{
  "trades": [
    {
      "id": "123",
      "symbol": "AAPL",
      "trade_type": "BUY",
      "quantity": 100,
      "entry_price": 150.50,
      "exit_price": 155.75,
      "entry_date": "2024-01-15T10:30:00Z",
      "exit_date": "2024-01-16T14:20:00Z",
      "profit_loss": 525.00,
      "profit_loss_percentage": 3.49,
      "notes": "Earnings play",
      "tags": ["earnings", "swing"],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### Create Trade
```http
POST /api/v1/trades
Authorization: Bearer <token>
Content-Type: application/json

{
  "symbol": "AAPL",
  "trade_type": "BUY",
  "quantity": 100,
  "entry_price": 150.50,
  "exit_price": 155.75,
  "entry_date": "2024-01-15T10:30:00Z",
  "exit_date": "2024-01-16T14:20:00Z",
  "notes": "Earnings play",
  "tags": ["earnings", "swing"]
}
```

#### Update Trade
```http
PUT /api/v1/trades/{trade_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "notes": "Updated notes",
  "tags": ["earnings", "swing", "profitable"]
}
```

#### Delete Trade
```http
DELETE /api/v1/trades/{trade_id}
Authorization: Bearer <token>
```

#### Bulk Upload Trades
```http
POST /api/v1/trades/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: trades.csv
```

**CSV Format:**
```csv
symbol,trade_type,quantity,entry_price,exit_price,entry_date,exit_date,notes
AAPL,BUY,100,150.50,155.75,2024-01-15,2024-01-16,Earnings play
GOOGL,SELL,50,140.00,138.50,2024-01-17,2024-01-18,Overvalued
```

### Analytics

#### Dashboard Overview
```http
GET /api/v1/analytics/dashboard
Authorization: Bearer <token>
```

**Response:**
```json
{
  "summary": {
    "total_trades": 250,
    "winning_trades": 180,
    "losing_trades": 70,
    "win_rate": 72.0,
    "total_profit_loss": 15750.50,
    "average_profit": 125.25,
    "profit_factor": 2.35,
    "sharpe_ratio": 1.85
  },
  "recent_performance": {
    "daily": 250.50,
    "weekly": 1250.75,
    "monthly": 5500.00,
    "yearly": 15750.50
  },
  "top_performers": [
    {
      "symbol": "AAPL",
      "total_profit": 3500.00,
      "trade_count": 25,
      "win_rate": 80.0
    }
  ]
}
```

#### Performance Metrics
```http
GET /api/v1/analytics/performance?period=monthly&start_date=2024-01-01
Authorization: Bearer <token>
```

**Query Parameters:**
- `period`: daily, weekly, monthly, yearly
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `symbol`: Filter by symbol

#### Win Rate Analysis
```http
GET /api/v1/analytics/win-rate?group_by=symbol
Authorization: Bearer <token>
```

#### Profit/Loss Analysis
```http
GET /api/v1/analytics/profit-loss?group_by=month
Authorization: Bearer <token>
```

#### Trade Streaks
```http
GET /api/v1/analytics/streaks
Authorization: Bearer <token>
```

**Response:**
```json
{
  "current_streak": {
    "type": "winning",
    "count": 5,
    "total_profit": 1250.50
  },
  "best_winning_streak": {
    "count": 12,
    "total_profit": 3500.00,
    "start_date": "2024-01-01",
    "end_date": "2024-01-15"
  },
  "worst_losing_streak": {
    "count": 3,
    "total_loss": -450.00,
    "start_date": "2024-02-01",
    "end_date": "2024-02-03"
  }
}
```

### Journal

#### List Journal Entries
```http
GET /api/v1/journal/entries?limit=20
Authorization: Bearer <token>
```

#### Create Journal Entry
```http
POST /api/v1/journal/entries
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Market Analysis for Week 3",
  "content": "The market showed signs of...",
  "mood": "confident",
  "tags": ["analysis", "weekly-review"],
  "linked_trades": ["trade-123", "trade-456"]
}
```

#### Update Journal Entry
```http
PUT /api/v1/journal/entries/{entry_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Updated content...",
  "mood": "neutral"
}
```

### Portfolio

#### Portfolio Summary
```http
GET /api/v1/portfolio/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_value": 125000.00,
  "cash_balance": 25000.00,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "average_cost": 150.00,
      "current_price": 165.00,
      "market_value": 16500.00,
      "unrealized_pnl": 1500.00,
      "unrealized_pnl_percentage": 10.0
    }
  ],
  "allocation": {
    "stocks": 80.0,
    "cash": 20.0
  }
}
```

### Playbooks

#### List Playbooks
```http
GET /api/v1/playbooks
Authorization: Bearer <token>
```

#### Create Playbook
```http
POST /api/v1/playbooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Earnings Gap Strategy",
  "description": "Trading strategy for earnings gaps",
  "rules": {
    "entry": ["Gap > 5%", "Volume > 2x average"],
    "exit": ["Profit target: 10%", "Stop loss: 5%"]
  },
  "tags": ["earnings", "gap", "momentum"]
}
```

### WebSocket

#### Real-time Updates
```javascript
const ws = new WebSocket('wss://api.tradesense.com/api/v1/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Subscribe to updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['trades', 'analytics']
}));
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "symbol",
      "reason": "Symbol is required"
    }
  },
  "request_id": "req_123abc"
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input parameters
- `AUTHENTICATION_ERROR`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Webhooks

Configure webhooks to receive real-time notifications:

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["trade.created", "trade.updated", "analytics.daily"],
  "secret": "your-webhook-secret"
}
```

Webhook payload:
```json
{
  "event": "trade.created",
  "timestamp": "2024-01-16T10:30:00Z",
  "data": {
    "trade": {
      "id": "123",
      "symbol": "AAPL",
      "profit_loss": 525.00
    }
  },
  "signature": "sha256=..."
}
```

## SDK Examples

### Python
```python
import requests

class TradesenseAPI:
    def __init__(self, api_key):
        self.base_url = "https://api.tradesense.com/api/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_trades(self, **params):
        response = requests.get(
            f"{self.base_url}/trades",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def create_trade(self, trade_data):
        response = requests.post(
            f"{self.base_url}/trades",
            headers=self.headers,
            json=trade_data
        )
        return response.json()

# Usage
api = TradesenseAPI("your-api-key")
trades = api.get_trades(symbol="AAPL", limit=50)
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

class TradesenseAPI {
  constructor(apiKey) {
    this.client = axios.create({
      baseURL: 'https://api.tradesense.com/api/v1',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }
  
  async getTrades(params = {}) {
    const response = await this.client.get('/trades', { params });
    return response.data;
  }
  
  async createTrade(tradeData) {
    const response = await this.client.post('/trades', tradeData);
    return response.data;
  }
}

// Usage
const api = new TradesenseAPI('your-api-key');
const trades = await api.getTrades({ symbol: 'AAPL', limit: 50 });
```

## Best Practices

1. **Rate Limiting**: Implement exponential backoff for rate limit errors
2. **Pagination**: Always use pagination for large datasets
3. **Caching**: Cache frequently accessed data client-side
4. **Error Handling**: Implement proper error handling for all API calls
5. **Security**: Never expose API keys in client-side code
6. **Compression**: Use gzip compression for large responses
7. **Filtering**: Use query parameters to filter data server-side

## Changelog

### v1.0.0 (2024-01-16)
- Initial API release
- Authentication endpoints
- Trade management
- Analytics endpoints
- Journal functionality
- WebSocket support

## Support

- **Documentation**: https://docs.tradesense.com
- **API Status**: https://status.tradesense.com
- **Support Email**: api-support@tradesense.com
- **Developer Forum**: https://forum.tradesense.com/developers