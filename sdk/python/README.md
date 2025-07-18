# TradeSense Python SDK

Official Python SDK for the TradeSense API.

## Installation

```bash
pip install tradesense
```

## Quick Start

```python
from tradesense import TradeSenseClient

# Initialize the client
client = TradeSenseClient(api_key="your-api-key")

# Create a trade
trade = client.trades.create({
    'symbol': 'AAPL',
    'entry_date': '2024-01-15',
    'entry_price': 150.50,
    'quantity': 100,
    'trade_type': 'long'
})

# Get analytics
overview = client.analytics.overview()
print(f"Win Rate: {overview['win_rate']:.1%}")
```

## Features

- Full API coverage
- Type hints for better IDE support
- Automatic retry with exponential backoff
- Comprehensive error handling
- Support for all TradeSense features:
  - Trade management
  - Analytics and reporting
  - Journal entries
  - A/B testing
  - Account management

## Authentication

You can provide your API key in several ways:

1. Pass directly to client:
```python
client = TradeSenseClient(api_key="your-api-key")
```

2. Use environment variable:
```bash
export TRADESENSE_API_KEY="your-api-key"
```
```python
client = TradeSenseClient()  # Will use env var
```

## Examples

### Trade Management

```python
# List trades with filters
trades = client.trades.list(
    start_date='2024-01-01',
    end_date='2024-01-31',
    symbol='AAPL'
)

# Update a trade
updated = client.trades.update(
    trade_id='123e4567-e89b-12d3-a456-426614174000',
    updates={'exit_price': 155.00}
)

# Bulk import
result = client.trades.bulk_create([
    {'symbol': 'AAPL', 'entry_date': '2024-01-15', ...},
    {'symbol': 'MSFT', 'entry_date': '2024-01-16', ...}
])
```

### Analytics

```python
# Get performance metrics
performance = client.analytics.performance(timeframe='month')

# Symbol analysis
by_symbol = client.analytics.by_symbol()
for symbol in by_symbol:
    print(f"{symbol['symbol']}: ${symbol['pnl']:.2f}")

# Risk metrics
risk = client.analytics.risk_metrics()
print(f"Sharpe Ratio: {risk['sharpe_ratio']:.2f}")
```

### Journal

```python
# Create entry
entry = client.journal.create(
    title="Market Analysis",
    content="Today's market showed...",
    mood="confident",
    tags=["analysis"]
)

# Search entries
results = client.journal.search("breakout strategy")
```

## Error Handling

```python
from tradesense import TradeSenseError, AuthenticationError, APIError

try:
    trade = client.trades.create(trade_data)
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
except TradeSenseError as e:
    print(f"SDK error: {e}")
```

## Requirements

- Python 3.7+
- requests

## Support

- Documentation: https://docs.tradesense.com
- API Reference: https://docs.tradesense.com/api
- Issues: https://github.com/tradesense/python-sdk/issues

## License

MIT License - see LICENSE file for details.