# TradeSense SDK Guide

This guide covers the official TradeSense SDKs for Python and JavaScript/TypeScript.

## Installation

### Python

```bash
pip install tradesense
```

### JavaScript/TypeScript

```bash
npm install @tradesense/sdk
# or
yarn add @tradesense/sdk
```

## Quick Start

### Python

```python
from tradesense import TradeSenseClient

# Initialize client
client = TradeSenseClient(api_key="your-api-key-here")

# Create a trade
trade = client.trades.create({
    'symbol': 'AAPL',
    'entry_date': '2024-01-15',
    'entry_price': 150.50,
    'quantity': 100,
    'trade_type': 'long'
})

print(f"Created trade {trade['id']} with P&L: ${trade.get('profit_loss', 0):.2f}")

# Get analytics
overview = client.analytics.overview()
print(f"Total P&L: ${overview['total_pnl']:.2f}")
print(f"Win Rate: {overview['win_rate']:.1%}")
```

### JavaScript/TypeScript

```typescript
import { TradeSenseClient } from '@tradesense/sdk';

// Initialize client
const client = new TradeSenseClient({
  apiKey: 'your-api-key-here'
});

// Create a trade
const trade = await client.trades.create({
  symbol: 'AAPL',
  entry_date: '2024-01-15',
  entry_price: 150.50,
  quantity: 100,
  trade_type: 'long'
});

console.log(`Created trade ${trade.id} with P&L: $${trade.profit_loss || 0}`);

// Get analytics
const overview = await client.analytics.overview();
console.log(`Total P&L: $${overview.total_pnl}`);
console.log(`Win Rate: ${(overview.win_rate * 100).toFixed(1)}%`);
```

## Configuration

### Environment Variables

Both SDKs support environment variables:

```bash
export TRADESENSE_API_KEY="your-api-key-here"
export TRADESENSE_BASE_URL="https://api.tradesense.com"  # Optional
```

### Python Configuration

```python
from tradesense import TradeSenseClient

client = TradeSenseClient(
    api_key="your-api-key",  # Or use TRADESENSE_API_KEY env var
    base_url="https://api.tradesense.com",  # Optional
    timeout=30,  # Request timeout in seconds
    retry_count=3  # Number of retries on failure
)
```

### JavaScript Configuration

```typescript
import { TradeSenseClient } from '@tradesense/sdk';

const client = new TradeSenseClient({
  apiKey: 'your-api-key',  // Or use TRADESENSE_API_KEY env var
  baseUrl: 'https://api.tradesense.com',  // Optional
  timeout: 30000,  // Request timeout in milliseconds
  retries: 3  // Number of retries on failure
});
```

## Trade Management

### List Trades

**Python:**
```python
# List all trades
trades = client.trades.list()

# Filter trades
trades = client.trades.list(
    start_date='2024-01-01',
    end_date='2024-01-31',
    symbol='AAPL',
    limit=50
)

for trade in trades:
    print(f"{trade['symbol']}: ${trade['profit_loss']:.2f}")
```

**JavaScript:**
```typescript
// List all trades
const trades = await client.trades.list();

// Filter trades
const filteredTrades = await client.trades.list({
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  symbol: 'AAPL',
  limit: 50
});

filteredTrades.items.forEach(trade => {
  console.log(`${trade.symbol}: $${trade.profit_loss}`);
});
```

### Create Trade

**Python:**
```python
trade = client.trades.create({
    'symbol': 'MSFT',
    'entry_date': '2024-01-15',
    'entry_price': 380.50,
    'quantity': 50,
    'trade_type': 'long',
    'exit_date': '2024-01-20',
    'exit_price': 385.75,
    'commission': 2.00,
    'notes': 'Earnings play',
    'tags': ['earnings', 'tech'],
    'strategy': 'momentum'
})
```

**JavaScript:**
```typescript
const trade = await client.trades.create({
  symbol: 'MSFT',
  entry_date: '2024-01-15',
  entry_price: 380.50,
  quantity: 50,
  trade_type: 'long',
  exit_date: '2024-01-20',
  exit_price: 385.75,
  commission: 2.00,
  notes: 'Earnings play',
  tags: ['earnings', 'tech'],
  strategy: 'momentum'
});
```

### Update Trade

**Python:**
```python
updated_trade = client.trades.update(
    trade_id='123e4567-e89b-12d3-a456-426614174000',
    updates={
        'exit_date': '2024-01-22',
        'exit_price': 388.00,
        'notes': 'Extended hold for better exit'
    }
)
```

**JavaScript:**
```typescript
const updatedTrade = await client.trades.update(
  '123e4567-e89b-12d3-a456-426614174000',
  {
    exit_date: '2024-01-22',
    exit_price: 388.00,
    notes: 'Extended hold for better exit'
  }
);
```

### Bulk Operations

**Python:**
```python
# Bulk create trades
trades_data = [
    {
        'symbol': 'AAPL',
        'entry_date': '2024-01-15',
        'entry_price': 150.50,
        'quantity': 100,
        'trade_type': 'long'
    },
    {
        'symbol': 'GOOGL',
        'entry_date': '2024-01-16',
        'entry_price': 140.25,
        'quantity': 50,
        'trade_type': 'long'
    }
]

result = client.trades.bulk_create(trades_data)
print(f"Created {result['created']} trades")
if result['errors']:
    print(f"Errors: {result['errors']}")
```

**JavaScript:**
```typescript
// Bulk create trades
const tradesData = [
  {
    symbol: 'AAPL',
    entry_date: '2024-01-15',
    entry_price: 150.50,
    quantity: 100,
    trade_type: 'long' as const
  },
  {
    symbol: 'GOOGL',
    entry_date: '2024-01-16',
    entry_price: 140.25,
    quantity: 50,
    trade_type: 'long' as const
  }
];

const result = await client.trades.bulkCreate(tradesData);
console.log(`Created ${result.created} trades`);
if (result.errors.length > 0) {
  console.log('Errors:', result.errors);
}
```

### Import from CSV

**Python:**
```python
# Import trades from CSV file
result = client.trades.import_csv(
    file_path='trades.csv',
    broker='td_ameritrade'
)

print(f"Imported {result['imported']} trades")
if result['errors']:
    for error in result['errors']:
        print(f"Row {error['row']}: {error['error']}")
```

**JavaScript:**
```typescript
// Import trades from CSV file (browser)
const fileInput = document.getElementById('file-input') as HTMLInputElement;
const file = fileInput.files[0];

const result = await client.trades.importCSV(file, 'td_ameritrade');
console.log(`Imported ${result.imported} trades`);

// Node.js
import { readFileSync } from 'fs';

const file = new Blob([readFileSync('trades.csv')]);
const result = await client.trades.importCSV(file, 'td_ameritrade');
```

## Analytics

### Overview Metrics

**Python:**
```python
# Get overall analytics
overview = client.analytics.overview()

print(f"Total Trades: {overview['total_trades']}")
print(f"Total P&L: ${overview['total_pnl']:,.2f}")
print(f"Win Rate: {overview['win_rate']:.1%}")
print(f"Profit Factor: {overview['profit_factor']:.2f}")
print(f"Average Win: ${overview['average_win']:.2f}")
print(f"Average Loss: ${overview['average_loss']:.2f}")
print(f"Sharpe Ratio: {overview['sharpe_ratio']:.2f}")

# Get analytics for date range
overview = client.analytics.overview(
    start_date='2024-01-01',
    end_date='2024-01-31'
)
```

**JavaScript:**
```typescript
// Get overall analytics
const overview = await client.analytics.overview();

console.log(`Total Trades: ${overview.total_trades}`);
console.log(`Total P&L: $${overview.total_pnl.toLocaleString()}`);
console.log(`Win Rate: ${(overview.win_rate * 100).toFixed(1)}%`);
console.log(`Profit Factor: ${overview.profit_factor.toFixed(2)}`);
console.log(`Average Win: $${overview.average_win.toFixed(2)}`);
console.log(`Average Loss: $${overview.average_loss.toFixed(2)}`);
console.log(`Sharpe Ratio: ${overview.sharpe_ratio.toFixed(2)}`);

// Get analytics for date range
const rangeOverview = await client.analytics.overview({
  start_date: '2024-01-01',
  end_date: '2024-01-31'
});
```

### Performance Analysis

**Python:**
```python
# Get monthly performance
performance = client.analytics.performance(timeframe='month')

for period in performance['periods']:
    print(f"{period['period']}: ${period['pnl']:.2f} ({period['return_percentage']:.1f}%)")

# Get win/loss analysis
win_loss = client.analytics.win_loss()
print(f"Profit Factor: {win_loss['profit_factor']:.2f}")
print(f"Expectancy: ${win_loss['expectancy']:.2f}")

# Get performance by symbol
by_symbol = client.analytics.by_symbol()
for symbol_data in by_symbol:
    print(f"{symbol_data['symbol']}: ${symbol_data['pnl']:.2f} ({symbol_data['win_rate']:.1%})")
```

**JavaScript:**
```typescript
// Get monthly performance
const performance = await client.analytics.performance('month');

performance.periods.forEach(period => {
  console.log(`${period.period}: $${period.pnl} (${period.return_percentage.toFixed(1)}%)`);
});

// Get win/loss analysis
const winLoss = await client.analytics.winLoss();
console.log(`Profit Factor: ${winLoss.profit_factor.toFixed(2)}`);
console.log(`Expectancy: $${winLoss.expectancy.toFixed(2)}`);

// Get performance by symbol
const bySymbol = await client.analytics.bySymbol();
bySymbol.forEach(symbolData => {
  console.log(`${symbolData.symbol}: $${symbolData.pnl} (${(symbolData.win_rate * 100).toFixed(1)}%)`);
});
```

## Journal Management

### Create Entry

**Python:**
```python
entry = client.journal.create(
    title="Weekly Market Review",
    content="This week showed strong bullish momentum in tech stocks...",
    mood="confident",
    tags=["weekly-review", "tech", "bullish"]
)

print(f"Created journal entry: {entry['id']}")
```

**JavaScript:**
```typescript
const entry = await client.journal.create({
  title: "Weekly Market Review",
  content: "This week showed strong bullish momentum in tech stocks...",
  mood: "confident",
  tags: ["weekly-review", "tech", "bullish"]
});

console.log(`Created journal entry: ${entry.id}`);
```

### Search Entries

**Python:**
```python
# Search journal entries
results = client.journal.search("momentum strategy")

for entry in results:
    print(f"{entry['title']} - {entry['created_at']}")
    print(f"Preview: {entry['content'][:100]}...")
    print("---")
```

**JavaScript:**
```typescript
// Search journal entries
const results = await client.journal.search("momentum strategy");

results.forEach(entry => {
  console.log(`${entry.title} - ${entry.created_at}`);
  console.log(`Preview: ${entry.content.substring(0, 100)}...`);
  console.log('---');
});
```

## A/B Testing Integration

### Get Experiment Assignments

**Python:**
```python
# Get all active experiment assignments
assignments = client.experiments.get_assignments()

for assignment in assignments:
    print(f"Experiment: {assignment['experiment_id']}")
    print(f"Variant: {assignment['variant_name']}")
    print(f"Config: {assignment['config']}")

# Check specific experiment
variant = client.experiments.get_variant('pricing_page_v2')
if variant:
    if variant['config'].get('show_value_bullets'):
        # Show enhanced pricing page
        pass
```

**JavaScript:**
```typescript
// Get all active experiment assignments
const assignments = await client.experiments.getAssignments();

assignments.forEach(assignment => {
  console.log(`Experiment: ${assignment.experiment_id}`);
  console.log(`Variant: ${assignment.variant_name}`);
  console.log('Config:', assignment.config);
});

// Check specific experiment
const variant = await client.experiments.getVariant('pricing_page_v2');
if (variant?.config.show_value_bullets) {
  // Show enhanced pricing page
}
```

### Track Conversions

**Python:**
```python
# Track conversion event
client.experiments.track_conversion(
    experiment_id='pricing_page_v2',
    metric_id='pro_conversion',
    value=29.99,
    metadata={
        'plan': 'pro',
        'billing_cycle': 'monthly'
    }
)
```

**JavaScript:**
```typescript
// Track conversion event
await client.experiments.trackConversion(
  'pricing_page_v2',
  'pro_conversion',
  29.99,
  {
    plan: 'pro',
    billing_cycle: 'monthly'
  }
);
```

## Error Handling

### Python

```python
from tradesense import TradeSenseError, AuthenticationError, APIError

try:
    trade = client.trades.create({
        'symbol': 'AAPL',
        'entry_date': '2024-01-15',
        'entry_price': 150.50,
        'quantity': 100,
        'trade_type': 'long'
    })
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    if e.response:
        print(f"Details: {e.response}")
except TradeSenseError as e:
    print(f"SDK Error: {e}")
```

### JavaScript/TypeScript

```typescript
import { TradeSenseError, AuthenticationError } from '@tradesense/sdk';

try {
  const trade = await client.trades.create({
    symbol: 'AAPL',
    entry_date: '2024-01-15',
    entry_price: 150.50,
    quantity: 100,
    trade_type: 'long'
  });
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof TradeSenseError) {
    console.error(`API Error: ${error.message}`);
    console.error(`Status Code: ${error.statusCode}`);
    if (error.response) {
      console.error('Details:', error.response);
    }
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Advanced Usage

### Pagination

**Python:**
```python
# Paginate through all trades
offset = 0
limit = 100
all_trades = []

while True:
    page = client.trades.list(limit=limit, offset=offset)
    all_trades.extend(page)
    
    if len(page) < limit:
        break
    
    offset += limit

print(f"Total trades: {len(all_trades)}")
```

**JavaScript:**
```typescript
// Paginate through all trades
let offset = 0;
const limit = 100;
const allTrades: Trade[] = [];

while (true) {
  const page = await client.trades.list({ limit, offset });
  allTrades.push(...page.items);
  
  if (page.items.length < limit) {
    break;
  }
  
  offset += limit;
}

console.log(`Total trades: ${allTrades.length}`);
```

### Rate Limit Handling

**Python:**
```python
import time
from tradesense import APIError

def with_rate_limit_retry(func, *args, **kwargs):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if e.status_code == 429:  # Rate limited
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
            raise
    
# Usage
trade = with_rate_limit_retry(client.trades.create, trade_data)
```

**JavaScript:**
```typescript
async function withRateLimitRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (error instanceof TradeSenseError && error.statusCode === 429) {
        if (attempt < maxRetries - 1) {
          await new Promise(resolve => 
            setTimeout(resolve, 1000 * Math.pow(2, attempt))
          );
          continue;
        }
      }
      throw error;
    }
  }
  
  throw lastError!;
}

// Usage
const trade = await withRateLimitRetry(() => 
  client.trades.create(tradeData)
);
```

## Best Practices

1. **API Key Security**
   ```python
   # Use environment variables
   import os
   client = TradeSenseClient(api_key=os.environ['TRADESENSE_API_KEY'])
   ```

2. **Efficient Data Fetching**
   ```python
   # Request only what you need
   trades = client.trades.list(
       start_date='2024-01-01',
       limit=50,
       symbol='AAPL'
   )
   ```

3. **Error Recovery**
   ```python
   # Implement retry logic for transient failures
   for attempt in range(3):
       try:
           result = client.analytics.overview()
           break
       except Exception as e:
           if attempt == 2:
               raise
           time.sleep(1)
   ```

4. **Bulk Operations**
   ```python
   # Use bulk endpoints for better performance
   trades_to_create = []
   
   # Batch trades
   for trade_data in large_dataset:
       trades_to_create.append(trade_data)
       
       if len(trades_to_create) >= 100:
           client.trades.bulk_create(trades_to_create)
           trades_to_create = []
   
   # Don't forget remaining trades
   if trades_to_create:
       client.trades.bulk_create(trades_to_create)
   ```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API key is correct
   - Check key hasn't expired
   - Ensure proper environment variable is set

2. **Rate Limiting**
   - Implement exponential backoff
   - Cache responses when possible
   - Consider upgrading subscription tier

3. **Timeout Errors**
   - Increase timeout setting
   - Reduce batch sizes
   - Check network connectivity

4. **Data Validation**
   - Ensure dates are in YYYY-MM-DD format
   - Verify required fields are provided
   - Check numeric values are valid

### Debug Mode

**Python:**
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# SDK will now log all requests/responses
client = TradeSenseClient(api_key="your-key")
```

**JavaScript:**
```typescript
// Enable debug mode via environment
process.env.DEBUG = 'tradesense:*';

// Or configure in client
const client = new TradeSenseClient({
  apiKey: 'your-key',
  debug: true  // If supported
});
```