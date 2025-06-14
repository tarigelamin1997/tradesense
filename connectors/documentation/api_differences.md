
# Multi-Connector API Differences and Edge Cases

This document outlines the key differences between broker and prop firm APIs, along with edge cases that must be handled for robust data integration.

## 1. Interactive Brokers (IB) API

### Authentication
- **Method**: Session-based authentication via IB Gateway/TWS
- **Edge Cases**:
  - Requires IB Gateway or TWS to be running locally
  - Sessions expire after 24 hours of inactivity
  - SSO re-authentication may be required for certain endpoints
  - Paper trading vs live accounts use different URLs

### Data Structure
- **Executions vs Trades**: IB returns individual executions, not complete trades
- **Partial Fills**: Multiple executions may comprise a single trade
- **Commission**: Reported separately from execution data
- **P&L Calculation**: Requires position data for accurate P&L

### Rate Limits
- **Limit**: 5 requests per second per endpoint
- **Mitigation**: Implement request queuing and retry logic

### Market Data
- **Real-time**: Requires separate market data subscriptions
- **Delayed**: 15-20 minute delay without subscription
- **Multi-Account**: Account ID specification required

## 2. TD Ameritrade API

### Authentication
- **Method**: OAuth 2.0 with refresh tokens
- **Edge Cases**:
  - Access tokens expire after 30 minutes
  - Refresh tokens expire after 90 days
  - Requires pre-registered client ID
  - Account linking required for live data

### Data Structure
- **Transactions**: Returns all transaction types, must filter for trades
- **Corporate Actions**: Appear as transactions, need filtering
- **Options**: Different transaction types (BUY_TO_OPEN, SELL_TO_CLOSE, etc.)
- **Fees**: Separate transaction types for dividends, fees, etc.

### Rate Limits
- **Limit**: 120 requests per minute per token
- **Date Range**: Limited to 1 year maximum

### Market Hours
- **Trading Hours**: Data availability affected by market hours
- **Extended Hours**: May require separate API calls

## 3. Apex Trader Funding (Prop Firm)

### Authentication
- **Method**: API key based authentication
- **Edge Cases**:
  - Different endpoints for challenge vs funded accounts
  - Account type affects available data and limits

### Prop Firm Specific Data
- **Risk Limits**: Daily loss limits, maximum loss limits
- **Profit Targets**: Required for account scaling/payouts
- **Account Types**: Challenge accounts vs funded accounts
- **Violations**: Risk rule violations tracked per trade

### Fee Structure
- **Commissions**: Typically no per-trade commissions
- **Profit Splits**: Revenue sharing instead of commission model
- **Scaling**: Account size changes based on performance

## 4. Common Edge Cases Across All Connectors

### Time Zones and Market Hours
- **UTC vs Local**: Different APIs use different time zone conventions
- **Market Sessions**: Regular hours vs extended hours trading
- **Holidays**: Market holiday handling varies by provider

### Data Quality Issues
- **Missing Data**: Gaps in historical data
- **Duplicate Records**: Same trade reported multiple times
- **Partial Data**: Incomplete trade information
- **Format Changes**: APIs may change data formats without notice

### Error Handling
- **Rate Limiting**: Different retry strategies needed
- **Authentication Failures**: Token refresh vs session management
- **Server Errors**: Temporary vs permanent failures
- **Data Validation**: Field validation varies by provider

## 5. Normalization Challenges

### Field Mapping
```python
# Example field mappings across providers
FIELD_MAPPINGS = {
    'interactive_brokers': {
        'symbol': 'symbol',
        'side': 'direction',
        'quantity': 'qty',
        'price': 'entry_price',
        'execution_time': 'entry_time'
    },
    'td_ameritrade': {
        'symbol': 'symbol',
        'instruction': 'direction',
        'amount': 'qty',
        'price': 'entry_price',
        'transactionDate': 'entry_time'
    },
    'apex_trader': {
        'symbol': 'symbol',
        'side': 'direction',
        'quantity': 'qty',
        'entry_price': 'entry_price',
        'entry_time': 'entry_time'
    }
}
```

### Data Type Conversions
- **Timestamps**: ISO 8601 vs Unix timestamps vs custom formats
- **Numbers**: String vs numeric representation
- **Directions**: 'BUY'/'SELL' vs 'long'/'short' vs 1/-1

### Currency Handling
- **Multi-Currency**: Different base currencies per account
- **Conversion**: Real-time vs historical exchange rates
- **Precision**: Decimal precision varies by currency

## 6. Testing and Validation

### Connection Testing
```python
def test_all_connectors():
    """Test all connectors for basic functionality."""
    connectors = ['interactive_brokers', 'td_ameritrade', 'apex_trader']
    results = {}
    
    for connector_name in connectors:
        try:
            connector = registry.create_instance(connector_name)
            connection_ok = connector.validate_connection()
            quality_report = connector.test_data_quality()
            
            results[connector_name] = {
                'connection': 'ok' if connection_ok else 'failed',
                'quality': quality_report
            }
        except Exception as e:
            results[connector_name] = {'error': str(e)}
    
    return results
```

### Data Quality Checks
- **Required Fields**: Ensure all required fields are present
- **Data Ranges**: Validate reasonable price/quantity ranges
- **Timestamp Validation**: Ensure timestamps are within expected ranges
- **Duplicate Detection**: Check for duplicate trade IDs

## 7. Performance Considerations

### Caching Strategies
- **Token Caching**: Cache authentication tokens appropriately
- **Data Caching**: Cache frequently accessed data
- **Rate Limit Tracking**: Track API usage to avoid limits

### Batch Processing
- **Bulk Requests**: Use batch endpoints where available
- **Pagination**: Handle large datasets with proper pagination
- **Parallel Processing**: Safely parallelize API calls

### Error Recovery
- **Retry Logic**: Exponential backoff for transient errors
- **Circuit Breakers**: Prevent cascading failures
- **Fallback Strategies**: Alternative data sources when primary fails

## 8. Security Considerations

### Credential Management
- **Token Storage**: Secure storage of API keys and tokens
- **Rotation**: Automatic token rotation where supported
- **Encryption**: Encrypt sensitive credentials at rest

### API Security
- **HTTPS**: Always use HTTPS for API communications
- **Certificate Validation**: Validate SSL certificates (except IB Gateway)
- **Request Signing**: Use proper request signing where required

This documentation should be updated as new connectors are added and as existing APIs evolve.
