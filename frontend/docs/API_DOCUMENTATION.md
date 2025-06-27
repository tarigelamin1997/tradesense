
# API Services Documentation

## Overview
This document outlines all available API services, their methods, inputs, outputs, and usage examples.

## Base Configuration

All API services use a shared axios instance configured in `services/api.ts`:

```typescript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## Authentication Service (`services/auth.ts`)

### Methods

#### `login(email: string, password: string)`
Authenticates a user and returns user data with JWT token.

**Input:**
```typescript
{
  email: string;
  password: string;
}
```

**Output:**
```typescript
{
  user: {
    id: string;
    email: string;
    name: string;
    createdAt: string;
  };
  token: string;
}
```

**Usage:**
```typescript
import { authService } from '@/services/auth';

try {
  const result = await authService.login('user@example.com', 'password123');
  console.log('User logged in:', result.user);
  localStorage.setItem('auth-token', result.token);
} catch (error) {
  console.error('Login failed:', error.message);
}
```

#### `register(email: string, password: string, name: string)`
Creates a new user account.

**Input:**
```typescript
{
  email: string;
  password: string;
  name: string;
}
```

**Output:**
```typescript
{
  user: {
    id: string;
    email: string;
    name: string;
    createdAt: string;
  };
  token: string;
}
```

**Usage:**
```typescript
const result = await authService.register(
  'newuser@example.com', 
  'securepassword', 
  'John Doe'
);
```

#### `logout()`
Invalidates the current session.

**Input:** None

**Output:**
```typescript
{
  message: string;
}
```

#### `refreshToken()`
Refreshes the current JWT token.

**Input:** None (uses stored token)

**Output:**
```typescript
{
  token: string;
}
```

#### `getCurrentUser()`
Fetches current user information.

**Input:** None (uses stored token)

**Output:**
```typescript
{
  id: string;
  email: string;
  name: string;
  createdAt: string;
  lastLogin: string;
}
```

## Trades Service (`services/trades.ts`)

### Methods

#### `getTrades(filters?: TradeFilters)`
Fetches user's trade data with optional filtering.

**Input:**
```typescript
interface TradeFilters {
  symbol?: string;
  dateFrom?: string;
  dateTo?: string;
  type?: 'buy' | 'sell';
  limit?: number;
  offset?: number;
}
```

**Output:**
```typescript
{
  trades: Trade[];
  total: number;
  page: number;
  totalPages: number;
}

interface Trade {
  id: string;
  symbol: string;
  quantity: number;
  price: number;
  date: string;
  type: 'buy' | 'sell';
  profit?: number;
  commission?: number;
}
```

**Usage:**
```typescript
import { tradesService } from '@/services/trades';

// Get all trades
const allTrades = await tradesService.getTrades();

// Get filtered trades
const filteredTrades = await tradesService.getTrades({
  symbol: 'AAPL',
  dateFrom: '2024-01-01',
  dateTo: '2024-12-31'
});
```

#### `uploadTrades(file: File)`
Uploads trade data from CSV file.

**Input:**
```typescript
file: File // CSV file object
```

**Output:**
```typescript
{
  message: string;
  imported: number;
  errors?: string[];
}
```

**Usage:**
```typescript
const fileInput = document.getElementById('csvFile') as HTMLInputElement;
const file = fileInput.files[0];

try {
  const result = await tradesService.uploadTrades(file);
  console.log(`Imported ${result.imported} trades`);
} catch (error) {
  console.error('Upload failed:', error);
}
```

#### `getAnalytics(dateRange?: string)`
Retrieves trading analytics and performance metrics.

**Input:**
```typescript
dateRange?: '7d' | '30d' | '90d' | '1y' | 'all'
```

**Output:**
```typescript
{
  totalProfit: number;
  totalTrades: number;
  winRate: number;
  avgProfit: number;
  maxDrawdown: number;
  sharpeRatio: number;
  profitFactor: number;
  equityCurve: Array<{
    date: string;
    value: number;
  }>;
  monthlyReturns: Array<{
    month: string;
    profit: number;
  }>;
}
```

#### `deleteTrade(id: string)`
Deletes a specific trade.

**Input:**
```typescript
id: string
```

**Output:**
```typescript
{
  message: string;
}
```

#### `updateTrade(id: string, data: Partial<Trade>)`
Updates a specific trade.

**Input:**
```typescript
id: string;
data: Partial<Trade>
```

**Output:**
```typescript
{
  trade: Trade;
  message: string;
}
```

## Error Handling

All services implement consistent error handling:

```typescript
try {
  const result = await someService.method();
} catch (error) {
  if (error.response) {
    // Server responded with error status
    console.error('Server Error:', error.response.data.message);
  } else if (error.request) {
    // Network error
    console.error('Network Error:', error.message);
  } else {
    // Other error
    console.error('Error:', error.message);
  }
}
```

## Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation failed)
- `500` - Internal Server Error

## Authentication Headers

Most endpoints require authentication. The token is automatically included in requests:

```typescript
Authorization: Bearer <jwt_token>
```

## Rate Limiting

API calls are rate-limited:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

When rate limited, you'll receive a `429` status code with retry information.
# TradeSense API Documentation

## Overview

TradeSense provides a comprehensive REST API for managing trading data, analytics, and user authentication. All API endpoints are prefixed with `/api/v1/`.

## Authentication

### Base URL
```
https://your-tradesense-domain.com/api/v1
```

### Authentication Methods
- **JWT Token**: Include `Authorization: Bearer <token>` header
- **API Key**: Include `X-API-Key: <key>` header (for integrations)

---

## Auth Service (`/auth`)

### `POST /auth/login`
Authenticate user and receive JWT token.

**Request:**
```typescript
{
  email: string;
  password: string;
}
```

**Response:**
```typescript
{
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
    created_at: string;
  };
  expires_in: number;
}
```

**Example:**
```javascript
import { authApi } from './services/auth';

const response = await authApi.login('trader@example.com', 'password123');
console.log(response.token); // JWT token for subsequent requests
```

### `POST /auth/register`
Create new user account.

**Request:**
```typescript
{
  name: string;
  email: string;
  password: string;
}
```

### `POST /auth/refresh`
Refresh expired JWT token.

**Headers:** `Authorization: Bearer <expired_token>`

---

## Trades Service (`/trades`)

### `GET /trades`
Fetch paginated trades with optional filtering.

**Query Parameters:**
```typescript
{
  page?: number;          // Default: 1
  limit?: number;         // Default: 50, Max: 200
  symbol?: string;        // Filter by symbol
  strategy?: string;      // Filter by strategy
  start_date?: string;    // ISO date string
  end_date?: string;      // ISO date string
  min_pnl?: number;       // Minimum P&L
  max_pnl?: number;       // Maximum P&L
  confidence_min?: number; // Min confidence score (1-10)
  confidence_max?: number; // Max confidence score (1-10)
}
```

**Response:**
```typescript
{
  trades: Trade[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  summary: {
    total_pnl: number;
    win_rate: number;
    total_trades: number;
  };
}
```

**Example:**
```javascript
import { tradesApi } from './services/trades';

// Fetch recent AAPL trades
const response = await tradesApi.getTrades({
  symbol: 'AAPL',
  limit: 20,
  start_date: '2024-01-01'
});

console.log(`Found ${response.trades.length} AAPL trades`);
```

### `POST /trades`
Create new trade entry.

**Request:**
```typescript
{
  symbol: string;
  entry_time: string;     // ISO datetime
  exit_time?: string;     // ISO datetime
  quantity: number;
  entry_price: number;
  exit_price?: number;
  strategy?: string;
  confidence_score?: number; // 1-10
  tags?: string[];
  notes?: string;
}
```

### `PUT /trades/{id}`
Update existing trade.

### `DELETE /trades/{id}`
Delete trade by ID.

---

## Analytics Service (`/analytics`)

### `GET /analytics/performance`
Get comprehensive performance metrics.

**Query Parameters:**
```typescript
{
  start_date?: string;
  end_date?: string;
  strategy?: string;
  symbol?: string;
  groupBy?: 'day' | 'week' | 'month';
}
```

**Response:**
```typescript
{
  metrics: {
    total_pnl: number;
    win_rate: number;
    profit_factor: number;
    sharpe_ratio: number;
    max_drawdown: number;
    avg_win: number;
    avg_loss: number;
    largest_win: number;
    largest_loss: number;
  };
  equity_curve: Array<{
    date: string;
    cumulative_pnl: number;
    daily_pnl: number;
  }>;
  strategy_breakdown: Array<{
    strategy: string;
    trades: number;
    pnl: number;
    win_rate: number;
  }>;
}
```

### `GET /analytics/streaks`
Analyze winning and losing streaks.

**Response:**
```typescript
{
  current_streak: {
    type: 'winning' | 'losing';
    count: number;
    pnl: number;
  };
  longest_winning_streak: number;
  longest_losing_streak: number;
  streak_history: Array<{
    start_date: string;
    end_date: string;
    type: 'winning' | 'losing';
    count: number;
    pnl: number;
  }>;
}
```

### `GET /analytics/heatmap`
Get trading performance heatmap data.

**Response:**
```typescript
{
  daily_pnl: Array<{
    date: string;
    pnl: number;
    trades: number;
  }>;
  hourly_performance: Array<{
    hour: number;
    avg_pnl: number;
    trades: number;
    win_rate: number;
  }>;
  symbol_performance: Array<{
    symbol: string;
    pnl: number;
    trades: number;
    win_rate: number;
  }>;
}
```

---

## Playbooks Service (`/playbooks`)

### `GET /playbooks`
Get all trading playbooks/strategies.

### `POST /playbooks`
Create new playbook.

**Request:**
```typescript
{
  name: string;
  description: string;
  rules: string[];
  tags: string[];
  risk_parameters: {
    max_position_size: number;
    stop_loss_pct: number;
    take_profit_pct: number;
  };
}
```

---

## Portfolio Service (`/portfolio`)

### `GET /portfolio/simulation`
Get portfolio simulation data.

**Response:**
```typescript
{
  starting_balance: number;
  current_balance: number;
  total_return: number;
  total_return_pct: number;
  max_drawdown: number;
  equity_curve: Array<{
    date: string;
    balance: number;
    daily_return: number;
  }>;
  monthly_returns: Array<{
    month: string;
    return: number;
    return_pct: number;
  }>;
}
```

---

## File Upload Service (`/uploads`)

### `POST /uploads/trades`
Upload CSV/Excel file with trade data.

**Request:** `multipart/form-data`
- `file`: CSV or Excel file
- `format`: 'csv' | 'excel'
- `has_headers`: boolean

**Response:**
```typescript
{
  upload_id: string;
  status: 'processing' | 'completed' | 'failed';
  total_rows: number;
  processed_rows: number;
  errors: Array<{
    row: number;
    message: string;
  }>;
}
```

### `GET /uploads/{upload_id}/status`
Check upload processing status.

---

## Error Handling

All API endpoints follow consistent error response format:

```typescript
{
  error: {
    code: string;           // Error code (e.g., 'INVALID_CREDENTIALS')
    message: string;        // Human-readable message
    details?: object;       // Additional error context
  };
  status: number;          // HTTP status code
  timestamp: string;       // ISO datetime
}
```

### Common Error Codes
- `UNAUTHORIZED` (401): Invalid or missing authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `VALIDATION_ERROR` (400): Invalid request data
- `RATE_LIMITED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error

---

## Rate Limiting

- **Authenticated requests**: 100 requests per minute
- **File uploads**: 5 uploads per minute
- **Analytics queries**: 30 requests per minute

Rate limit headers included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## WebSocket API (Real-time)

### Connection
```javascript
const ws = new WebSocket('wss://your-domain.com/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

### Subscriptions
```javascript
// Subscribe to trade updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'trades',
  user_id: 'your-user-id'
}));

// Subscribe to portfolio updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'portfolio',
  user_id: 'your-user-id'
}));
```

---

## SDK Examples

### JavaScript/TypeScript
```javascript
import { TradeSenseAPI } from '@tradesense/sdk';

const api = new TradeSenseAPI({
  baseUrl: 'https://api.tradesense.com',
  apiKey: 'your-api-key'
});

// Fetch recent trades
const trades = await api.trades.list({ limit: 10 });

// Add new trade
const newTrade = await api.trades.create({
  symbol: 'TSLA',
  entry_time: new Date(),
  quantity: 100,
  entry_price: 250.00,
  strategy: 'breakout'
});
```

### Python
```python
from tradesense import TradeSenseClient

client = TradeSenseClient(
    base_url='https://api.tradesense.com',
    api_key='your-api-key'
)

# Fetch analytics
analytics = client.analytics.performance(
    start_date='2024-01-01',
    strategy='momentum'
)

print(f"Win Rate: {analytics['metrics']['win_rate']:.2%}")
```

---

## Changelog

### v1.2.0 (Latest)
- Added confidence calibration endpoints
- Enhanced portfolio simulation
- New market context analysis
- Improved error handling

### v1.1.0
- Added playbook management
- WebSocket support for real-time updates
- Enhanced filtering options

### v1.0.0
- Initial API release
- Core trading data management
- Basic analytics endpoints
