# TradeSense API Reference

## Overview

The TradeSense API is a RESTful API that provides programmatic access to all TradeSense features. This document covers authentication, endpoints, request/response formats, and error handling.

**Base URL**: `https://api.tradesense.com`

## Authentication

All API requests require authentication using an API key passed in the `Authorization` header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key

1. Log in to your TradeSense account
2. Navigate to Settings → API Keys
3. Click "Create New Key"
4. Name your key and select permissions
5. Copy the generated key (it won't be shown again)

### Example Request

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.tradesense.com/api/v1/trades
```

## Response Format

All responses are JSON formatted. Successful responses have standard HTTP status codes (200, 201, 204).

### Success Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "symbol": "AAPL",
  "entry_date": "2024-01-15",
  "entry_price": 150.50
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "error_code": "INVALID_TRADE_DATA"
}
```

## Common Headers

| Header | Description | Example |
|--------|-------------|---------|
| `Content-Type` | Request content type | `application/json` |
| `Accept` | Response content type | `application/json` |
| `X-Request-ID` | Unique request identifier | `550e8400-e29b-41d4-a716` |

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```http
GET /api/v1/trades?limit=50&offset=100
```

Paginated responses include metadata:

```json
{
  "items": [...],
  "total": 250,
  "limit": 50,
  "offset": 100
}
```

## Rate Limiting

- **Free tier**: 100 requests per hour
- **Basic tier**: 1,000 requests per hour
- **Pro tier**: 10,000 requests per hour
- **Enterprise**: Custom limits

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640995200
```

## Endpoints

### Trades

#### List Trades

```http
GET /api/v1/trades
```

**Query Parameters:**
- `start_date` (string): Filter by start date (YYYY-MM-DD)
- `end_date` (string): Filter by end date (YYYY-MM-DD)
- `symbol` (string): Filter by symbol
- `trade_type` (string): Filter by type (long/short)
- `limit` (integer): Results per page (default: 100, max: 500)
- `offset` (integer): Number of results to skip

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "symbol": "AAPL",
      "entry_date": "2024-01-15",
      "exit_date": "2024-01-20",
      "entry_price": 150.50,
      "exit_price": 155.75,
      "quantity": 100,
      "trade_type": "long",
      "profit_loss": 525.00,
      "commission": 2.00,
      "notes": "Breakout trade",
      "tags": ["breakout", "tech"],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

#### Create Trade

```http
POST /api/v1/trades
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "entry_date": "2024-01-15",
  "entry_price": 150.50,
  "quantity": 100,
  "trade_type": "long",
  "exit_date": "2024-01-20",
  "exit_price": 155.75,
  "commission": 2.00,
  "notes": "Breakout trade",
  "tags": ["breakout", "tech"],
  "strategy": "momentum"
}
```

**Response:** `201 Created`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "symbol": "AAPL",
  "profit_loss": 525.00,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get Trade

```http
GET /api/v1/trades/{trade_id}
```

**Response:** Trade object

#### Update Trade

```http
PUT /api/v1/trades/{trade_id}
```

**Request Body:** Partial trade object with fields to update

**Response:** Updated trade object

#### Delete Trade

```http
DELETE /api/v1/trades/{trade_id}
```

**Response:** `204 No Content`

#### Bulk Create Trades

```http
POST /api/v1/trades/bulk
```

**Request Body:**
```json
{
  "trades": [
    {
      "symbol": "AAPL",
      "entry_date": "2024-01-15",
      "entry_price": 150.50,
      "quantity": 100,
      "trade_type": "long"
    },
    {
      "symbol": "MSFT",
      "entry_date": "2024-01-16",
      "entry_price": 380.25,
      "quantity": 50,
      "trade_type": "long"
    }
  ]
}
```

**Response:**
```json
{
  "created": 2,
  "errors": []
}
```

#### Import Trades from CSV

```http
POST /api/v1/trades/import
```

**Request:** Multipart form data
- `file`: CSV file
- `broker`: Broker name (generic, td_ameritrade, interactive_brokers, etc.)

**Response:**
```json
{
  "imported": 50,
  "errors": [
    {
      "row": 5,
      "error": "Invalid date format"
    }
  ]
}
```

### Analytics

#### Analytics Overview

```http
GET /api/v1/analytics/overview
```

**Query Parameters:**
- `start_date` (string): Start date for analysis
- `end_date` (string): End date for analysis

**Response:**
```json
{
  "total_trades": 150,
  "total_pnl": 15250.50,
  "win_rate": 0.65,
  "profit_factor": 2.3,
  "average_win": 250.75,
  "average_loss": -108.90,
  "best_trade": 1250.00,
  "worst_trade": -450.00,
  "total_commission": 300.00,
  "net_pnl": 14950.50,
  "sharpe_ratio": 1.85,
  "max_drawdown": -2500.00,
  "average_hold_time_days": 5.2
}
```

#### Performance Metrics

```http
GET /api/v1/analytics/performance
```

**Query Parameters:**
- `timeframe` (string): day, week, month, year, all

**Response:**
```json
{
  "periods": [
    {
      "period": "2024-01",
      "trades": 25,
      "pnl": 3250.50,
      "win_rate": 0.68,
      "return_percentage": 3.25
    }
  ],
  "cumulative_pnl": [
    {
      "date": "2024-01-01",
      "value": 0
    },
    {
      "date": "2024-01-31",
      "value": 3250.50
    }
  ]
}
```

#### Win/Loss Analysis

```http
GET /api/v1/analytics/win-loss
```

**Response:**
```json
{
  "total_wins": 98,
  "total_losses": 52,
  "win_rate": 0.65,
  "average_win": 250.75,
  "average_loss": -108.90,
  "largest_win": 1250.00,
  "largest_loss": -450.00,
  "profit_factor": 2.3,
  "expectancy": 85.25,
  "win_loss_ratio": 2.3
}
```

#### Analytics by Symbol

```http
GET /api/v1/analytics/by-symbol
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "trades": 45,
    "pnl": 5250.00,
    "win_rate": 0.71,
    "average_pnl": 116.67
  },
  {
    "symbol": "MSFT",
    "trades": 38,
    "pnl": 3800.00,
    "win_rate": 0.63,
    "average_pnl": 100.00
  }
]
```

### Journal

#### List Journal Entries

```http
GET /api/v1/journal
```

**Query Parameters:**
- `limit` (integer): Results per page
- `offset` (integer): Number of results to skip
- `tag` (string): Filter by tag

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Market Analysis - Tech Sector",
      "content": "Today's market showed...",
      "mood": "confident",
      "tags": ["analysis", "tech"],
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

#### Create Journal Entry

```http
POST /api/v1/journal
```

**Request Body:**
```json
{
  "title": "Post-Market Review",
  "content": "Today's trading session...",
  "mood": "neutral",
  "tags": ["review", "daily"]
}
```

#### Search Journal

```http
GET /api/v1/journal/search
```

**Query Parameters:**
- `q` (string): Search query

### Account

#### Get Profile

```http
GET /api/v1/account/profile
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "trader@example.com",
  "full_name": "John Trader",
  "subscription_tier": "pro",
  "created_at": "2023-01-15T10:00:00Z",
  "settings": {
    "timezone": "America/New_York",
    "currency": "USD",
    "theme": "dark"
  }
}
```

#### Update Profile

```http
PUT /api/v1/account/profile
```

**Request Body:**
```json
{
  "full_name": "John Trader",
  "settings": {
    "timezone": "America/Chicago",
    "theme": "light"
  }
}
```

#### Get API Usage

```http
GET /api/v1/account/usage
```

**Response:**
```json
{
  "period": "2024-01",
  "requests_made": 5420,
  "requests_limit": 10000,
  "storage_used_mb": 125,
  "storage_limit_mb": 1000,
  "trades_count": 850,
  "trades_limit": 10000
}
```

### Experiments (A/B Testing)

#### Get Experiment Assignments

```http
GET /api/v1/experiments/assignments
```

**Response:**
```json
[
  {
    "experiment_id": "pricing_page_v2",
    "variant_id": "clear_value_props",
    "variant_name": "Clear Value Props",
    "config": {
      "show_value_bullets": true,
      "highlight_savings": true
    }
  }
]
```

#### Track Conversion

```http
POST /api/v1/experiments/track
```

**Request Body:**
```json
{
  "experiment_id": "pricing_page_v2",
  "metric_id": "pro_conversion",
  "value": 29.99,
  "metadata": {
    "plan": "pro",
    "source": "pricing_page"
  }
}
```

### WebSocket API

#### Connection

```javascript
const ws = new WebSocket('wss://api.tradesense.com/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'YOUR_API_KEY'
  }));
};
```

#### Subscribe to Events

```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['trades', 'analytics']
}));
```

#### Event Format

```json
{
  "type": "trade_created",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "symbol": "AAPL",
    "profit_loss": 250.00
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | API key is invalid or expired |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INVALID_TRADE_DATA` | Trade data validation failed |
| `TRADE_NOT_FOUND` | Trade ID doesn't exist |
| `INSUFFICIENT_PERMISSIONS` | API key lacks required permissions |
| `SUBSCRIPTION_LIMIT_REACHED` | Account limit reached |
| `INVALID_DATE_RANGE` | Date range is invalid |
| `CSV_PARSE_ERROR` | CSV file couldn't be parsed |

## SDK Libraries

Official SDKs are available for:

- **Python**: `pip install tradesense`
- **JavaScript/TypeScript**: `npm install @tradesense/sdk`
- **Go**: `go get github.com/tradesense/sdk-go`
- **Ruby**: `gem install tradesense`

## Webhooks

Configure webhooks to receive real-time notifications:

1. Go to Settings → Webhooks
2. Add endpoint URL
3. Select events to receive
4. Verify webhook signature

### Webhook Payload

```json
{
  "id": "evt_123",
  "type": "trade.created",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "symbol": "AAPL",
    "profit_loss": 250.00
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Signature Verification

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Best Practices

1. **Use API Keys Securely**
   - Never expose keys in client-side code
   - Rotate keys regularly
   - Use environment variables

2. **Handle Rate Limits**
   - Implement exponential backoff
   - Cache responses when possible
   - Use webhooks for real-time updates

3. **Error Handling**
   - Always check response status
   - Implement retry logic
   - Log errors for debugging

4. **Optimize Requests**
   - Use bulk endpoints when available
   - Request only needed fields
   - Implement pagination properly

## Support

- **Documentation**: https://docs.tradesense.com
- **API Status**: https://status.tradesense.com
- **Support Email**: api-support@tradesense.com
- **Community Forum**: https://community.tradesense.com