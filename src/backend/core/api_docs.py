"""
API Documentation Generator

Provides comprehensive API documentation with OpenAPI specifications, examples, and testing utilities.
"""
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def generate_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """Generate enhanced OpenAPI schema with comprehensive documentation"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="TradeSense API",
        version="2.6.1",
        description="""
        # TradeSense Trading Analytics API
        
        A comprehensive API for trading analytics, portfolio management, and behavioral analysis.
        
        ## Features
        
        - **Trade Management**: Upload, analyze, and manage trading data
        - **Analytics**: Advanced performance metrics and behavioral analysis
        - **Portfolio Simulation**: Backtest strategies and simulate portfolios
        - **Real-time Data**: Live market data and real-time analytics
        - **User Management**: Secure authentication and user profiles
        
        ## Authentication
        
        All protected endpoints require JWT authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your_jwt_token>
        ```
        
        ## Rate Limiting
        
        API endpoints are rate-limited to ensure fair usage:
        - Authentication endpoints: 5 requests per minute
        - General endpoints: 100 requests per minute
        - Analytics endpoints: 20 requests per minute
        
        ## Error Handling
        
        The API uses standard HTTP status codes and returns detailed error messages:
        - `400`: Bad Request - Invalid input data
        - `401`: Unauthorized - Authentication required
        - `403`: Forbidden - Insufficient permissions
        - `404`: Not Found - Resource not found
        - `422`: Validation Error - Invalid data format
        - `429`: Too Many Requests - Rate limit exceeded
        - `500`: Internal Server Error - Server error
        
        ## Response Format
        
        All responses follow a consistent format:
        ```json
        {
            "success": true,
            "message": "Operation completed successfully",
            "data": { ... },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        ```
        """,
        routes=app.routes,
    )
    
    # Add custom components
    openapi_schema["components"]["schemas"].update({
        "Trade": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "symbol": {"type": "string", "example": "AAPL"},
                "direction": {"type": "string", "enum": ["long", "short", "buy", "sell"]},
                "quantity": {"type": "number", "minimum": 0},
                "entry_price": {"type": "number", "minimum": 0},
                "exit_price": {"type": "number", "minimum": 0},
                "entry_time": {"type": "string", "format": "date-time"},
                "exit_time": {"type": "string", "format": "date-time"},
                "pnl": {"type": "number"},
                "commission": {"type": "number", "default": 0},
                "strategy_tag": {"type": "string"},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 100},
                "notes": {"type": "string"}
            },
            "required": ["symbol", "direction", "quantity", "entry_price", "entry_time"]
        },
        "Analytics": {
            "type": "object",
            "properties": {
                "total_trades": {"type": "integer"},
                "winning_trades": {"type": "integer"},
                "losing_trades": {"type": "integer"},
                "win_rate": {"type": "number"},
                "total_pnl": {"type": "number"},
                "profit_factor": {"type": "number"},
                "max_drawdown": {"type": "number"},
                "sharpe_ratio": {"type": "number"},
                "equity_curve": {"type": "array", "items": {"type": "number"}},
                "symbol_breakdown": {"type": "array", "items": {"type": "object"}},
                "strategy_breakdown": {"type": "array", "items": {"type": "object"}},
                "behavioral_metrics": {"type": "object"}
            }
        },
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "email": {"type": "string", "format": "email"},
                "username": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "role": {"type": "string", "enum": ["user", "admin"]},
                "is_active": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": False},
                "message": {"type": "string"},
                "error": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"}
            }
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "message": {"type": "string"},
                "data": {"type": "object"},
                "timestamp": {"type": "string", "format": "date-time"}
            }
        }
    })
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for API authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add tags with descriptions
    openapi_schema["tags"] = [
        {
            "name": "authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "trades",
            "description": "Trade management and analysis endpoints"
        },
        {
            "name": "analytics",
            "description": "Advanced analytics and performance metrics"
        },
        {
            "name": "portfolio",
            "description": "Portfolio management and simulation"
        },
        {
            "name": "market-data",
            "description": "Real-time market data and feeds"
        },
        {
            "name": "performance",
            "description": "System performance monitoring and optimization"
        },
        {
            "name": "health",
            "description": "System health and status endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def get_api_examples() -> Dict[str, Any]:
    """Get comprehensive API examples for documentation"""
    return {
        "trade_creation": {
            "summary": "Create a new trade",
            "value": {
                "symbol": "AAPL",
                "direction": "long",
                "quantity": 100,
                "entry_price": 150.25,
                "exit_price": 155.75,
                "entry_time": "2024-01-15T09:30:00Z",
                "exit_time": "2024-01-15T15:45:00Z",
                "strategy_tag": "momentum",
                "confidence_score": 85,
                "notes": "Strong momentum breakout with high volume"
            }
        },
        "analytics_request": {
            "summary": "Request analytics for a date range",
            "value": {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
                "include_behavioral": True,
                "include_equity_curve": True
            }
        },
        "portfolio_simulation": {
            "summary": "Simulate portfolio with specific parameters",
            "value": {
                "initial_capital": 100000,
                "risk_per_trade": 0.02,
                "max_positions": 10,
                "strategy": "momentum",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            }
        },
        "user_registration": {
            "summary": "Register a new user",
            "value": {
                "email": "trader@example.com",
                "username": "pro_trader",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    }

def generate_test_cases() -> List[Dict[str, Any]]:
    """Generate comprehensive test cases for API endpoints"""
    return [
        {
            "name": "User Registration",
            "endpoint": "POST /api/v1/auth/register",
            "test_cases": [
                {
                    "name": "Valid registration",
                    "data": {
                        "email": "test@example.com",
                        "username": "testuser",
                        "password": "TestPass123!"
                    },
                    "expected_status": 201
                },
                {
                    "name": "Invalid email",
                    "data": {
                        "email": "invalid-email",
                        "username": "testuser",
                        "password": "TestPass123!"
                    },
                    "expected_status": 422
                },
                {
                    "name": "Weak password",
                    "data": {
                        "email": "test@example.com",
                        "username": "testuser",
                        "password": "123"
                    },
                    "expected_status": 422
                }
            ]
        },
        {
            "name": "Trade Creation",
            "endpoint": "POST /api/v1/trades",
            "test_cases": [
                {
                    "name": "Valid trade",
                    "data": {
                        "symbol": "AAPL",
                        "direction": "long",
                        "quantity": 100,
                        "entry_price": 150.25,
                        "entry_time": "2024-01-15T09:30:00Z"
                    },
                    "expected_status": 201
                },
                {
                    "name": "Invalid symbol",
                    "data": {
                        "symbol": "INVALID_SYMBOL_123",
                        "direction": "long",
                        "quantity": 100,
                        "entry_price": 150.25,
                        "entry_time": "2024-01-15T09:30:00Z"
                    },
                    "expected_status": 422
                },
                {
                    "name": "Negative quantity",
                    "data": {
                        "symbol": "AAPL",
                        "direction": "long",
                        "quantity": -100,
                        "entry_price": 150.25,
                        "entry_time": "2024-01-15T09:30:00Z"
                    },
                    "expected_status": 422
                }
            ]
        },
        {
            "name": "Analytics Retrieval",
            "endpoint": "GET /api/v1/analytics",
            "test_cases": [
                {
                    "name": "Valid date range",
                    "params": {
                        "start_date": "2024-01-01T00:00:00Z",
                        "end_date": "2024-01-31T23:59:59Z"
                    },
                    "expected_status": 200
                },
                {
                    "name": "Invalid date range",
                    "params": {
                        "start_date": "2024-01-31T23:59:59Z",
                        "end_date": "2024-01-01T00:00:00Z"
                    },
                    "expected_status": 400
                }
            ]
        }
    ]

def create_api_documentation_markdown() -> str:
    """Generate markdown documentation for the API"""
    return """
# TradeSense API Documentation

## Overview

The TradeSense API provides comprehensive trading analytics, portfolio management, and behavioral analysis capabilities.

## Base URL

```
https://api.tradesense.com/v1
```

## Authentication

All API requests require authentication using JWT tokens.

### Getting a Token

```bash
curl -X POST "https://api.tradesense.com/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Using the Token

```bash
curl -X GET "https://api.tradesense.com/v1/trades" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "trader123",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### POST /auth/login
Authenticate and get JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Trades

#### GET /trades
Get user's trades with optional filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `symbol` (string): Filter by symbol
- `start_date` (datetime): Filter trades from this date
- `end_date` (datetime): Filter trades until this date
- `strategy` (string): Filter by strategy tag

#### POST /trades
Create a new trade.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "direction": "long",
  "quantity": 100,
  "entry_price": 150.25,
  "exit_price": 155.75,
  "entry_time": "2024-01-15T09:30:00Z",
  "exit_time": "2024-01-15T15:45:00Z",
  "strategy_tag": "momentum",
  "confidence_score": 85,
  "notes": "Strong momentum breakout"
}
```

### Analytics

#### GET /analytics
Get comprehensive trading analytics.

**Query Parameters:**
- `start_date` (datetime): Start date for analysis
- `end_date` (datetime): End date for analysis
- `include_behavioral` (bool): Include behavioral metrics
- `include_equity_curve` (bool): Include equity curve data

**Response:**
```json
{
  "success": true,
  "data": {
    "total_trades": 150,
    "winning_trades": 95,
    "losing_trades": 55,
    "win_rate": 63.33,
    "total_pnl": 12500.50,
    "profit_factor": 1.85,
    "max_drawdown": -2500.00,
    "sharpe_ratio": 1.25,
    "equity_curve": [...],
    "symbol_breakdown": [...],
    "strategy_breakdown": [...],
    "behavioral_metrics": {...}
  }
}
```

### Portfolio

#### POST /portfolio/simulate
Simulate portfolio performance.

**Request Body:**
```json
{
  "initial_capital": 100000,
  "risk_per_trade": 0.02,
  "max_positions": 10,
  "strategy": "momentum",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z"
}
```

### Market Data

#### GET /market-data/live
Get real-time market data.

**Query Parameters:**
- `symbols` (string): Comma-separated list of symbols

### Performance Monitoring

#### GET /performance/metrics
Get system performance metrics.

#### GET /performance/slow-queries
Get list of slowest queries.

#### POST /performance/cache/clear
Clear query cache.

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
  "success": false,
  "message": "Validation error",
  "error": "Invalid symbol format",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

- Authentication endpoints: 5 requests per minute
- General endpoints: 100 requests per minute
- Analytics endpoints: 20 requests per minute

## SDK Examples

### Python

```python
import requests

# Authenticate
response = requests.post("https://api.tradesense.com/v1/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = response.json()["data"]["access_token"]

# Get trades
headers = {"Authorization": f"Bearer {token}"}
trades = requests.get("https://api.tradesense.com/v1/trades", headers=headers)

# Create trade
new_trade = requests.post("https://api.tradesense.com/v1/trades", 
                         headers=headers, json=trade_data)
```

### JavaScript

```javascript
// Authenticate
const authResponse = await fetch("https://api.tradesense.com/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123"
  })
});
const { access_token } = await authResponse.json();

// Get trades
const tradesResponse = await fetch("https://api.tradesense.com/v1/trades", {
  headers: { "Authorization": `Bearer ${access_token}` }
});
const trades = await tradesResponse.json();
```

## Testing

Use the provided test cases to validate your API integration:

```bash
# Run API tests
python -m pytest tests/api/ -v

# Run specific test
python -m pytest tests/api/test_trades.py::test_create_trade -v
```

## Support

For API support and questions:
- Email: api-support@tradesense.com
- Documentation: https://docs.tradesense.com
- Status: https://status.tradesense.com
""" 