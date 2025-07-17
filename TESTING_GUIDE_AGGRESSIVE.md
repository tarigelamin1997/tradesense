# TradeSense Aggressive Testing Guide

## 🚀 Quick Start URLs

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Test Accounts

### Default Test User
- **Email**: test@example.com
- **Password**: TestPass123!

### Create New Test Account
1. Go to http://localhost:3001/register
2. Use any email (e.g., yourtest@example.com)
3. Password must have: uppercase, lowercase, number, special char, 8+ chars

## 🧪 Aggressive Testing Checklist

### 1. **Authentication Testing**
- [ ] Register new account
- [ ] Login with new account
- [ ] Login with wrong password
- [ ] Try SQL injection in login form
- [ ] Test "Forgot Password" flow
- [ ] Test session timeout
- [ ] Test multiple browser tabs

### 2. **Trade Import Testing**
- [ ] Upload CSV with valid trades
- [ ] Upload empty CSV
- [ ] Upload malformed CSV
- [ ] Upload huge CSV (1000+ trades)
- [ ] Test duplicate detection
- [ ] Import trades with various date formats
- [ ] Test concurrent uploads

### 3. **Analytics Testing**
- [ ] View dashboard with no trades
- [ ] View dashboard with 1 trade
- [ ] View dashboard with 1000+ trades
- [ ] Test all chart types
- [ ] Test date range filters
- [ ] Test symbol filters
- [ ] Export analytics data

### 4. **Performance Testing**
- [ ] Load dashboard with 10,000 trades
- [ ] Rapid page navigation
- [ ] Multiple filter changes quickly
- [ ] Open multiple browser tabs
- [ ] Test on slow network (Chrome DevTools)

### 5. **Edge Cases**
- [ ] Trades with $0 profit/loss
- [ ] Trades with same entry/exit time
- [ ] Future-dated trades
- [ ] Very old trades (year 2000)
- [ ] Unicode symbols (émojis in notes)
- [ ] Very long trade notes

### 6. **Billing/Subscription Testing**
- [ ] View pricing page
- [ ] Click upgrade (Stripe test mode)
- [ ] Test card: 4242 4242 4242 4242
- [ ] Cancel subscription
- [ ] Resubscribe

### 7. **Security Testing**
- [ ] XSS in trade notes: `<script>alert('XSS')</script>`
- [ ] SQL injection in search
- [ ] CSRF token validation
- [ ] API access without auth token
- [ ] Direct API calls with expired token

### 8. **Mobile Testing**
- [ ] Test on mobile viewport
- [ ] Test touch interactions
- [ ] Test mobile menu
- [ ] Test chart interactions on touch
- [ ] Test file upload on mobile

## 🛠️ Useful Testing Commands

### Check Service Status
```bash
docker compose -f docker-compose.fixed.yml ps
```

### View Backend Logs
```bash
docker compose -f docker-compose.fixed.yml logs -f backend
```

### View Frontend Logs
```bash
docker compose -f docker-compose.fixed.yml logs -f frontend
```

### Restart Services
```bash
docker compose -f docker-compose.fixed.yml restart
```

### Direct API Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

### Database Access
```bash
# Connect to PostgreSQL
docker compose -f docker-compose.fixed.yml exec postgres psql -U postgres -d tradesense

# Useful queries:
# SELECT * FROM users;
# SELECT COUNT(*) FROM trades;
# SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
```

## 🐛 Known Testing Scenarios

### 1. **Bulk Operations**
- Select all trades
- Bulk delete
- Bulk export
- Bulk tagging

### 2. **Real-time Features**
- WebSocket connection status
- Live price updates
- Real-time notifications

### 3. **Advanced Analytics**
- Win/loss streaks
- Strategy comparison
- Playbook performance
- Risk metrics

## 📊 Test Data

### Sample CSV Format
```csv
timestamp,symbol,side,quantity,price,commission,description
2024-01-15 09:30:00,AAPL,BUY,100,150.00,1.00,Opening position
2024-01-15 14:30:00,AAPL,SELL,100,155.00,1.00,Taking profit
```

### Generate Test Data
```python
# Use the backend's seed script
docker compose -f docker-compose.fixed.yml exec backend python seed_trades.py
```

## 🚨 What to Look For

1. **Error Messages**: Should be user-friendly
2. **Loading States**: All async operations should show loading
3. **Empty States**: Helpful messages when no data
4. **Validation**: Form validation should be immediate
5. **Responsiveness**: UI should adapt to all screen sizes
6. **Accessibility**: Keyboard navigation should work

## 💣 Stress Testing

1. **Rapid Clicking**: Click buttons rapidly
2. **Browser Back/Forward**: Navigate quickly
3. **Network Throttling**: Simulate slow connections
4. **Multiple Uploads**: Upload files simultaneously
5. **Session Juggling**: Login/logout repeatedly

Remember: The goal is to break things! Document any issues found.