# TradeSense Mobile API Documentation

Comprehensive guide for integrating TradeSense mobile APIs into iOS and Android applications.

## Overview

The TradeSense Mobile API is designed specifically for mobile applications, providing:
- Optimized payload sizes
- Offline support considerations  
- Push notification integration
- Biometric authentication
- Real-time market data streaming
- Mobile-specific response formatting

## Base URL

```
Production: https://api.tradesense.app/mobile/v1
Staging: https://staging-api.tradesense.app/mobile/v1
```

## Authentication

### Headers Required

All authenticated requests require:
```
Authorization: Bearer {access_token}
X-Device-ID: {unique_device_id}
X-Device-Type: ios|android|tablet_ios|tablet_android
X-OS-Version: {os_version}
X-App-Version: {app_version}
```

Optional headers:
```
X-Push-Token: {fcm_or_apns_token}
X-Timezone: {user_timezone}
X-Language: {language_code}
```

### Login Flow

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123",
  "device_info": {
    "device_id": "unique-device-id",
    "device_type": "ios",
    "os_version": "15.0",
    "app_version": "1.0.0"
  }
}

Response:
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "refresh_token_here",
    "expires_in": 3600,
    "user": {
      "id": "user_id",
      "username": "johndoe",
      "email": "user@example.com",
      "subscription_tier": "premium"
    },
    "biometric_token": "biometric_token_for_future_logins"
  }
}
```

### Biometric Authentication

After initial login, use biometric token for subsequent logins:

```http
POST /auth/login
{
  "username": "user@example.com",
  "biometric_token": "stored_biometric_token",
  "device_info": {...}
}
```

### Token Refresh

```http
POST /auth/refresh
{
  "refresh_token": "current_refresh_token",
  "device_id": "unique-device-id"
}
```

## Core Endpoints

### Portfolio Management

#### Get Portfolio Summary
```http
GET /portfolio/summary

Response:
{
  "data": {
    "total_value": {"amount": 125000.50, "formatted": "$125,000.50"},
    "cash_balance": {"amount": 25000.00, "formatted": "$25,000.00"},
    "day_pnl": {"amount": 1250.00, "formatted": "$1,250.00"},
    "day_pnl_percent": {"value": 1.02, "formatted": "1.02%"},
    "positions_count": 15
  }
}
```

#### Get Positions
```http
GET /portfolio/positions?sort_by=value

Response:
{
  "data": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "avg_cost": 150.00,
      "current_price": 175.00,
      "unrealized_pnl": {"amount": 2500.00, "formatted": "$2,500.00"},
      "unrealized_pnl_percent": {"value": 16.67, "formatted": "16.67%"}
    }
  ]
}
```

### Trading

#### Quick Trade Entry
```http
POST /trades/quick-add
{
  "symbol": "AAPL",
  "type": "long",
  "shares": 100,
  "entry_price": 175.50,
  "notes": "Breakout trade"
}
```

#### Get Trade List
```http
GET /trades/list?status=open&page=1&limit=20

Response includes pagination:
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Analytics

#### Get Analytics Dashboard
```http
GET /analytics/dashboard?timeframe=30d

Response:
{
  "data": {
    "performance": {
      "total_pnl": {"amount": 5250.00, "formatted": "$5,250.00"},
      "win_rate": {"value": 65.5, "formatted": "65.5%"},
      "profit_factor": 2.1,
      "sharpe_ratio": 1.8
    },
    "charts": {
      "equity": {
        "type": "line",
        "data_points": [
          {"timestamp": "2024-01-01", "value": 100000},
          {"timestamp": "2024-01-02", "value": 101250}
        ]
      }
    }
  }
}
```

### Market Data

#### Real-time Quote
```http
GET /market/quote/AAPL

Response:
{
  "data": {
    "symbol": "AAPL",
    "price": 175.50,
    "change": 2.50,
    "change_percent": 1.44,
    "volume": 52341234,
    "high": 176.80,
    "low": 173.20
  }
}
```

#### WebSocket Streaming
```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.tradesense.app/mobile/v1/market/stream');

// Subscribe to symbols
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['AAPL', 'GOOGL', 'TSLA']
}));

// Receive real-time updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'quotes') {
    // Handle quote updates
  }
};
```

### Notifications

#### Register Push Token
```http
POST /notifications/register-token
{
  "token": "fcm_or_apns_token",
  "platform": "ios",
  "device_info": {...}
}
```

#### Get Notifications
```http
GET /notifications/list?unread_only=true

Response:
{
  "data": [
    {
      "id": "notif_123",
      "type": "trade",
      "title": "Trade Closed: AAPL",
      "body": "P&L: +$250.00",
      "timestamp": "2024-01-15T10:30:00Z",
      "read": false
    }
  ]
}
```

## Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Invalid credentials",
  "error_code": "AUTH_001",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

## Offline Support

### Caching Strategy

1. **ETags**: Use ETags for efficient caching
   ```http
   GET /trades/list
   If-None-Match: "etag_value"
   
   Response: 304 Not Modified (if data hasn't changed)
   ```

2. **Sync Tokens**: Track last sync for incremental updates
   ```http
   GET /trades/sync?since=2024-01-15T00:00:00Z
   ```

3. **Offline Queue**: Queue actions when offline
   ```javascript
   // Example offline queue implementation
   const offlineQueue = [];
   
   function addTrade(tradeData) {
     if (isOnline()) {
       return api.post('/trades/quick-add', tradeData);
     } else {
       offlineQueue.push({
         action: 'addTrade',
         data: tradeData,
         timestamp: new Date()
       });
       return Promise.resolve({offline: true});
     }
   }
   ```

## Best Practices

### 1. Device Management
- Generate unique device IDs that persist across app reinstalls
- Update device info on app launch
- Handle device token rotation gracefully

### 2. Security
- Store tokens securely in device keychain/keystore
- Implement certificate pinning for API calls
- Use biometric authentication where available
- Clear sensitive data on logout

### 3. Performance
- Implement aggressive caching for market data
- Use pagination for large data sets
- Batch API requests where possible
- Compress request/response payloads

### 4. Error Handling
```javascript
class APIClient {
  async request(endpoint, options) {
    try {
      const response = await fetch(endpoint, options);
      
      if (!response.ok) {
        switch (response.status) {
          case 401:
            // Token expired, try refresh
            await this.refreshToken();
            return this.request(endpoint, options);
          case 429:
            // Rate limited, implement backoff
            await this.backoff();
            return this.request(endpoint, options);
          default:
            throw new APIError(response);
        }
      }
      
      return response.json();
    } catch (error) {
      if (error.name === 'NetworkError') {
        // Queue for offline sync
        return this.queueOffline(endpoint, options);
      }
      throw error;
    }
  }
}
```

### 5. Push Notifications

#### Notification Payload Structure
```json
{
  "notification": {
    "title": "Trade Alert",
    "body": "AAPL hit your target price",
    "badge": 1,
    "sound": "default"
  },
  "data": {
    "type": "price_alert",
    "symbol": "AAPL",
    "alert_id": "alert_123",
    "deep_link": "tradesense://alerts/123"
  }
}
```

## Rate Limits

- **Authentication**: 5 requests per minute
- **Trading endpoints**: 60 requests per minute
- **Market data**: 300 requests per minute
- **WebSocket connections**: 5 concurrent per user

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642267200
```

## SDK Examples

### iOS (Swift)
```swift
class TradeSenseAPI {
    static let shared = TradeSenseAPI()
    private let baseURL = "https://api.tradesense.app/mobile/v1"
    
    func login(username: String, password: String) async throws -> LoginResponse {
        let deviceInfo = DeviceInfo(
            deviceId: UIDevice.current.identifierForVendor?.uuidString ?? "",
            deviceType: UIDevice.current.userInterfaceIdiom == .pad ? "tablet_ios" : "ios",
            osVersion: UIDevice.current.systemVersion,
            appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        )
        
        let request = LoginRequest(
            username: username,
            password: password,
            deviceInfo: deviceInfo
        )
        
        return try await post("/auth/login", body: request)
    }
}
```

### Android (Kotlin)
```kotlin
class TradeSenseAPI(private val context: Context) {
    private val baseURL = "https://api.tradesense.app/mobile/v1"
    
    suspend fun login(username: String, password: String): LoginResponse {
        val deviceInfo = DeviceInfo(
            deviceId = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ANDROID_ID
            ),
            deviceType = if (isTablet()) "tablet_android" else "android",
            osVersion = Build.VERSION.RELEASE,
            appVersion = BuildConfig.VERSION_NAME
        )
        
        val request = LoginRequest(
            username = username,
            password = password,
            deviceInfo = deviceInfo
        )
        
        return post("/auth/login", request)
    }
}
```

## Testing

### Test Credentials
```
Environment: Staging
Username: mobile_test@tradesense.app
Password: TestUser123!
```

### Postman Collection
Download our complete Postman collection:
https://api.tradesense.app/docs/mobile-api-postman.json

## Support

- **Documentation**: https://docs.tradesense.app/mobile
- **API Status**: https://status.tradesense.app
- **Support Email**: mobile-support@tradesense.app
- **Developer Forum**: https://forum.tradesense.app/mobile

## Changelog

### Version 1.0 (Current)
- Initial mobile API release
- Biometric authentication support
- Push notifications
- Real-time market data streaming
- Offline support with sync
- Comprehensive analytics endpoints
