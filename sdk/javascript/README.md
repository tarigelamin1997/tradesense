# TradeSense JavaScript/TypeScript SDK

Official JavaScript/TypeScript SDK for the TradeSense API.

## Installation

```bash
npm install @tradesense/sdk
# or
yarn add @tradesense/sdk
# or
pnpm add @tradesense/sdk
```

## Quick Start

```typescript
import { TradeSenseClient } from '@tradesense/sdk';

// Initialize the client
const client = new TradeSenseClient({
  apiKey: 'your-api-key'
});

// Create a trade
const trade = await client.trades.create({
  symbol: 'AAPL',
  entry_date: '2024-01-15',
  entry_price: 150.50,
  quantity: 100,
  trade_type: 'long'
});

// Get analytics
const overview = await client.analytics.overview();
console.log(`Win Rate: ${(overview.win_rate * 100).toFixed(1)}%`);
```

## Features

- Full TypeScript support with complete type definitions
- Works in both Node.js and browsers
- Automatic retry with exponential backoff
- Comprehensive error handling
- Zero dependencies
- Support for all TradeSense features:
  - Trade management
  - Analytics and reporting
  - Journal entries
  - A/B testing
  - Account management

## Authentication

You can provide your API key in several ways:

1. Pass directly to client:
```typescript
const client = new TradeSenseClient({
  apiKey: 'your-api-key'
});
```

2. Use environment variable (Node.js):
```bash
export TRADESENSE_API_KEY="your-api-key"
```
```typescript
const client = new TradeSenseClient({});  // Will use env var
```

## Examples

### Trade Management

```typescript
// List trades with filters
const trades = await client.trades.list({
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  symbol: 'AAPL'
});

// Update a trade
const updated = await client.trades.update(
  '123e4567-e89b-12d3-a456-426614174000',
  { exit_price: 155.00 }
);

// Bulk import
const result = await client.trades.bulkCreate([
  { symbol: 'AAPL', entry_date: '2024-01-15', ... },
  { symbol: 'MSFT', entry_date: '2024-01-16', ... }
]);
```

### Analytics

```typescript
// Get performance metrics
const performance = await client.analytics.performance('month');

// Symbol analysis
const bySymbol = await client.analytics.bySymbol();
bySymbol.forEach(symbol => {
  console.log(`${symbol.symbol}: $${symbol.pnl}`);
});

// Risk metrics
const risk = await client.analytics.riskMetrics();
console.log(`Sharpe Ratio: ${risk.sharpe_ratio.toFixed(2)}`);
```

### Journal

```typescript
// Create entry
const entry = await client.journal.create({
  title: 'Market Analysis',
  content: 'Today\'s market showed...',
  mood: 'confident',
  tags: ['analysis']
});

// Search entries
const results = await client.journal.search('breakout strategy');
```

### File Upload (Browser)

```typescript
// Import trades from CSV
const fileInput = document.getElementById('csv-file') as HTMLInputElement;
const file = fileInput.files[0];

const result = await client.trades.importCSV(file, 'td_ameritrade');
console.log(`Imported ${result.imported} trades`);
```

## Error Handling

```typescript
import { TradeSenseError, AuthenticationError } from '@tradesense/sdk';

try {
  const trade = await client.trades.create(tradeData);
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof TradeSenseError) {
    console.error(`API error: ${error.message} (status: ${error.statusCode})`);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## TypeScript Support

The SDK is written in TypeScript and provides complete type definitions:

```typescript
import type { Trade, AnalyticsOverview, JournalEntry } from '@tradesense/sdk';

// All methods are fully typed
const trade: Trade = await client.trades.get('trade-id');
const analytics: AnalyticsOverview = await client.analytics.overview();
```

## Configuration

```typescript
const client = new TradeSenseClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.tradesense.com',  // Optional
  timeout: 30000,  // Request timeout in ms (default: 30s)
  retries: 3       // Number of retries (default: 3)
});
```

## Browser Usage

The SDK works in modern browsers that support fetch API:

```html
<script type="module">
  import { TradeSenseClient } from 'https://unpkg.com/@tradesense/sdk';
  
  const client = new TradeSenseClient({
    apiKey: 'your-api-key'
  });
  
  // Use the client
  const trades = await client.trades.list();
</script>
```

## Requirements

- Node.js 14+ or modern browser
- No external dependencies

## Support

- Documentation: https://docs.tradesense.com
- API Reference: https://docs.tradesense.com/api
- Issues: https://github.com/tradesense/js-sdk/issues

## License

MIT License - see LICENSE file for details.