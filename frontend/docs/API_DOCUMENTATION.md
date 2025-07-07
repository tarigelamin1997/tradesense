# TradeSense API Documentation

## Overview

TradeSense API provides endpoints for trading analytics, user management, and data processing. All authenticated endpoints require a Bearer token.

## Base URL
```
Production: https://your-repl-name.replit.app/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### Login
```typescript
// POST /auth/login
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  user: {
    id: number;
    email: string;
    created_at: string;
  };
}

// Usage
import { authService } from '../services/auth';

const loginResult = await authService.login('user@example.com', 'password');
```

### Get Current User
```typescript
// GET /auth/me
// Headers: Authorization: Bearer <token>

interface UserResponse {
  id: number;
  email: string;
  created_at: string;
  preferences?: Record<string, any>;
}

// Usage
const user = await authService.getCurrentUser();
```

## Trades API

### Get Trades
```typescript
// GET /trades
// Headers: Authorization: Bearer <token>
// Query params: symbol?, start_date?, end_date?, playbook_id?

interface Trade {
  id: number;
  symbol: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  entry_time: string;
  exit_time: string;
  playbook_id?: number;
  confidence_level?: number;
}

// Usage
import { tradesService } from '../services/trades';

const trades = await tradesService.getTrades({
  symbol: 'AAPL',
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});
```

### Create Trade
```typescript
// POST /trades
interface CreateTradeRequest {
  symbol: string;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  entry_time: string;
  exit_time?: string;
  playbook_id?: number;
  confidence_level?: number;
  notes?: string;
}

// Usage
const newTrade = await tradesService.createTrade({
  symbol: 'AAPL',
  entry_price: 150.00,
  exit_price: 155.00,
  quantity: 100,
  entry_time: '2025-01-01T10:00:00Z',
  exit_time: '2025-01-01T15:00:00Z'
});
```

## Analytics API

### Performance Metrics
```typescript
// GET /analytics/performance
// Headers: Authorization: Bearer <token>
// Query params: start_date?, end_date?, playbook_id?

interface PerformanceMetrics {
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  avg_trade_duration: number;
}

// Usage
import { analyticsService } from '../services/analytics';

const performance = await analyticsService.getPerformance({
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});
```

### Streak Analysis
```typescript
// GET /analytics/streaks
interface StreakAnalysis {
  current_streak: {
    type: 'winning' | 'losing';
    count: number;
    pnl: number;
  };
  max_winning_streak: number;
  max_losing_streak: number;
  avg_winning_streak: number;
  avg_losing_streak: number;
}

// Usage
const streaks = await analyticsService.getStreaks();
```

## File Upload API

### Upload Trade Data
```typescript
// POST /uploads/trades
// Content-Type: multipart/form-data
// Headers: Authorization: Bearer <token>

interface UploadResponse {
  success: boolean;
  trades_imported: number;
  errors?: string[];
  preview?: Trade[];
}

// Usage
import { uploadsService } from '../services/uploads';

const formData = new FormData();
formData.append('file', file);
formData.append('column_mapping', JSON.stringify({
  symbol: 'Symbol',
  entry_price: 'Entry Price',
  exit_price: 'Exit Price'
}));

const result = await uploadsService.uploadTrades(formData);
```

## Playbooks API

### Get Playbooks
```typescript
// GET /playbooks
interface Playbook {
  id: number;
  name: string;
  description: string;
  color: string;
  created_at: string;
  trade_count: number;
  win_rate: number;
  avg_pnl: number;
}

// Usage
import { playbooksService } from '../services/playbooks';

const playbooks = await playbooksService.getPlaybooks();
```

### Create Playbook
```typescript
// POST /playbooks
interface CreatePlaybookRequest {
  name: string;
  description?: string;
  color?: string;
}

// Usage
const newPlaybook = await playbooksService.createPlaybook({
  name: 'Momentum Breakouts',
  description: 'High volume breakout strategy',
  color: '#3B82F6'
});
```

## Error Handling

All API responses follow this error format:

```typescript
interface APIError {
  detail: string;
  status_code: number;
  error_code?: string;
}

// HTTP Status Codes:
// 400 - Bad Request (validation errors)
// 401 - Unauthorized (missing/invalid token)
// 403 - Forbidden (insufficient permissions)
// 404 - Not Found
// 422 - Validation Error
// 500 - Internal Server Error
```

## Rate Limiting

- 100 requests per minute per user for most endpoints
- 10 requests per minute for file upload endpoints
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Pagination

List endpoints support pagination:

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Query params: page=1&size=50 (default: page=1, size=50, max=100)
```

## WebSocket Events (Future)

```typescript
// Connect to /ws/trades
interface TradeEvent {
  type: 'trade_created' | 'trade_updated' | 'trade_deleted';
  data: Trade;
}

interface AnalyticsEvent {
  type: 'metrics_updated';
  data: PerformanceMetrics;
}