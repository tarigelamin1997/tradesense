# TradeSense Mobile App Quick Start Guide

Get your mobile app integrated with TradeSense in minutes.

## Prerequisites

- API Key from TradeSense dashboard
- Mobile development environment (Xcode/Android Studio)
- Basic knowledge of REST APIs

## iOS Integration (Swift)

### 1. Install SDK

```swift
// Swift Package Manager
dependencies: [
    .package(url: "https://github.com/tradesense/ios-sdk.git", from: "1.0.0")
]
```

### 2. Initialize SDK

```swift
import TradeSenseSDK

// In AppDelegate or App struct
TradeSense.configure(
    apiKey: "your-api-key",
    environment: .production
)
```

### 3. Authentication

```swift
// Login
TradeSense.auth.login(username: email, password: password) { result in
    switch result {
    case .success(let user):
        // Store tokens securely
        KeychainHelper.save("access_token", user.accessToken)
        KeychainHelper.save("refresh_token", user.refreshToken)
        
        // Enable biometric for future logins
        if let biometricToken = user.biometricToken {
            TradeSense.auth.enableBiometric(token: biometricToken)
        }
        
    case .failure(let error):
        // Handle error
        print("Login failed: \(error)")
    }
}

// Biometric Login
TradeSense.auth.loginWithBiometric { result in
    // Handle result
}
```

### 4. Basic Operations

```swift
// Get Portfolio
TradeSense.portfolio.getSummary { result in
    switch result {
    case .success(let portfolio):
        updateUI(with: portfolio)
    case .failure(let error):
        showError(error)
    }
}

// Add Trade
let trade = QuickTrade(
    symbol: "AAPL",
    type: .long,
    shares: 100,
    entryPrice: 175.50
)

TradeSense.trades.quickAdd(trade) { result in
    // Handle result
}

// Real-time Market Data
TradeSense.market.subscribe(symbols: ["AAPL", "GOOGL"]) { quote in
    updateQuote(quote)
}
```

### 5. Push Notifications

```swift
// Register for push notifications
func application(_ application: UIApplication, 
                didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
    TradeSense.notifications.registerDevice(token: token)
}

// Handle notification
func userNotificationCenter(_ center: UNUserNotificationCenter,
                          didReceive response: UNNotificationResponse) {
    if let data = response.notification.request.content.userInfo["data"] as? [String: Any] {
        TradeSense.notifications.handleNotification(data)
    }
}
```

## Android Integration (Kotlin)

### 1. Add Dependencies

```gradle
// build.gradle
dependencies {
    implementation 'com.tradesense:android-sdk:1.0.0'
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.6.4'
}
```

### 2. Initialize SDK

```kotlin
// In Application class
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        
        TradeSense.init(
            context = this,
            apiKey = "your-api-key",
            environment = Environment.PRODUCTION
        )
    }
}
```

### 3. Authentication

```kotlin
// Login
lifecycleScope.launch {
    try {
        val user = TradeSense.auth.login(email, password)
        
        // Store tokens securely
        SecurePreferences.putString("access_token", user.accessToken)
        SecurePreferences.putString("refresh_token", user.refreshToken)
        
        // Enable biometric
        user.biometricToken?.let { token ->
            TradeSense.auth.enableBiometric(token)
        }
        
        navigateToHome()
    } catch (e: Exception) {
        showError(e.message)
    }
}

// Biometric Login
val biometricPrompt = BiometricPrompt(this, executor,
    object : BiometricPrompt.AuthenticationCallback() {
        override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
            lifecycleScope.launch {
                val user = TradeSense.auth.loginWithBiometric()
                navigateToHome()
            }
        }
    })

biometricPrompt.authenticate(promptInfo)
```

### 4. Basic Operations

```kotlin
// Get Portfolio
lifecycleScope.launch {
    val portfolio = TradeSense.portfolio.getSummary()
    updateUI(portfolio)
}

// Add Trade
val trade = QuickTrade(
    symbol = "AAPL",
    type = TradeType.LONG,
    shares = 100f,
    entryPrice = 175.50f
)

lifecycleScope.launch {
    try {
        val result = TradeSense.trades.quickAdd(trade)
        showSuccess("Trade added: ${result.tradeId}")
    } catch (e: Exception) {
        showError(e.message)
    }
}

// Real-time Market Data
TradeSense.market.subscribe(listOf("AAPL", "GOOGL")).collect { quote ->
    updateQuote(quote)
}
```

### 5. Push Notifications

```kotlin
// FCM Service
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        TradeSense.notifications.registerDevice(token)
    }
    
    override fun onMessageReceived(message: RemoteMessage) {
        message.data["type"]?.let { type ->
            TradeSense.notifications.handleNotification(message.data)
        }
    }
}
```

## React Native Integration

### 1. Install Package

```bash
npm install @tradesense/react-native-sdk
# or
yarn add @tradesense/react-native-sdk
```

### 2. Setup

```javascript
import TradeSense from '@tradesense/react-native-sdk';

// Initialize
TradeSense.configure({
  apiKey: 'your-api-key',
  environment: 'production'
});

// Login
const login = async (email, password) => {
  try {
    const user = await TradeSense.auth.login(email, password);
    
    // Store tokens
    await SecureStore.setItemAsync('access_token', user.accessToken);
    await SecureStore.setItemAsync('refresh_token', user.refreshToken);
    
    // Enable biometric
    if (user.biometricToken) {
      await TradeSense.auth.enableBiometric(user.biometricToken);
    }
    
    navigation.navigate('Home');
  } catch (error) {
    Alert.alert('Login Failed', error.message);
  }
};
```

### 3. Components

```jsx
import { PortfolioSummary, TradeList, MarketQuote } from '@tradesense/react-native-sdk';

// Portfolio Component
function Portfolio() {
  return (
    <PortfolioSummary
      onRefresh={() => console.log('Refreshing...')}
      onTradePress={(trade) => navigation.navigate('TradeDetail', { trade })}
    />
  );
}

// Market Data
function MarketWatch() {
  const [symbols] = useState(['AAPL', 'GOOGL', 'TSLA']);
  
  return (
    <FlatList
      data={symbols}
      renderItem={({ item }) => (
        <MarketQuote 
          symbol={item}
          realtime={true}
          onPress={() => navigation.navigate('SymbolDetail', { symbol: item })}
        />
      )}
    />
  );
}
```

## Best Practices

### 1. Secure Token Storage

**iOS**: Use Keychain Services
```swift
Keychain.set(token, forKey: "access_token")
```

**Android**: Use EncryptedSharedPreferences
```kotlin
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val prefs = EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
```

### 2. Offline Support

```swift
// iOS - Cache with expiration
let cache = URLCache(
    memoryCapacity: 10 * 1024 * 1024,
    diskCapacity: 50 * 1024 * 1024
)

// Android - Room database
@Entity
data class CachedTrade(
    @PrimaryKey val id: String,
    val data: String,
    val timestamp: Long
)
```

### 3. Error Handling

```kotlin
// Centralized error handling
sealed class TradeSenseError : Exception() {
    object NetworkError : TradeSenseError()
    object AuthenticationError : TradeSenseError()
    data class ServerError(val code: Int, override val message: String) : TradeSenseError()
    data class ValidationError(val fields: Map<String, String>) : TradeSenseError()
}

// Usage
try {
    val trades = TradeSense.trades.getList()
} catch (e: TradeSenseError) {
    when (e) {
        is TradeSenseError.NetworkError -> showOfflineMessage()
        is TradeSenseError.AuthenticationError -> navigateToLogin()
        is TradeSenseError.ServerError -> showError(e.message)
        is TradeSenseError.ValidationError -> highlightErrors(e.fields)
    }
}
```

### 4. Performance Optimization

- **Pagination**: Always use pagination for lists
- **Image Loading**: Use lazy loading for charts and images
- **Data Sync**: Implement incremental sync for offline support
- **Caching**: Cache frequently accessed data (quotes, portfolio)

## Testing

### Test Credentials
```
Environment: Staging
API Key: test_key_mobile_dev
Test User: mobile@test.tradesense.app
Password: TestUser123!
```

### Unit Tests

```swift
// iOS
func testLogin() async throws {
    let expectation = XCTestExpectation(description: "Login")
    
    TradeSense.auth.login(username: "test@example.com", password: "password") { result in
        XCTAssertTrue(result.isSuccess)
        expectation.fulfill()
    }
    
    wait(for: [expectation], timeout: 5.0)
}
```

```kotlin
// Android
@Test
fun testLogin() = runTest {
    val user = TradeSense.auth.login("test@example.com", "password")
    assertNotNull(user.accessToken)
    assertTrue(user.accessToken.isNotEmpty())
}
```

## Support Resources

- **Documentation**: https://docs.tradesense.app/mobile
- **API Reference**: https://api.tradesense.app/mobile/v1/docs
- **Sample Apps**: https://github.com/tradesense/mobile-samples
- **Support**: mobile-support@tradesense.app
- **Stack Overflow**: Tag your questions with `tradesense-mobile`

## Common Issues

### SSL Certificate Pinning (iOS)
```swift
let pinnedCertificates = [
    "api.tradesense.app": "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
]
```

### ProGuard Rules (Android)
```proguard
-keep class com.tradesense.** { *; }
-keepattributes Signature
-keepattributes *Annotation*
```

### Network Security Config (Android)
```xml
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">tradesense.app</domain>
        <pin-set expiration="2025-01-01">
            <pin digest="SHA-256">base64hash=</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```
