
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
