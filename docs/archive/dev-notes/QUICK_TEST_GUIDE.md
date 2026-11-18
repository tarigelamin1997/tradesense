# 🚀 TradeSense Quick Testing Guide

## ✅ Your App is Running!

### 🌐 Access URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 📧 How to Start Testing

1. **Open the Frontend**
   - Go to: http://localhost:5173
   - You should see the TradeSense landing page

2. **Create a Test Account**
   - Click "Get Started" or "Sign Up"
   - Enter any email (e.g., yourname@test.com)
   - Password requirements:
     - At least 8 characters
     - One uppercase letter
     - One lowercase letter
     - One number
     - One special character
   - Example: TestUser123!

3. **Start Testing Features**
   - Dashboard (empty initially)
   - Upload trades (CSV)
   - View analytics
   - Test filters
   - Try the journal
   - Check settings

### 🛠️ Service Status Commands

```bash
# Check all services
docker compose -f docker-compose.simple-alt.yml ps

# View backend logs (if issues)
docker compose -f docker-compose.simple-alt.yml logs -f backend

# View frontend logs
docker compose -f docker-compose.simple-alt.yml logs -f frontend

# Restart everything
docker compose -f docker-compose.simple-alt.yml restart

# Stop everything
docker compose -f docker-compose.simple-alt.yml down
```

### 📊 Sample Trade Data (CSV)

Create a file `sample_trades.csv`:

```csv
timestamp,symbol,side,quantity,price,commission,description
2024-01-15 09:30:00,AAPL,BUY,100,150.00,1.00,Opening position
2024-01-15 14:30:00,AAPL,SELL,100,155.00,1.00,Taking profit
2024-01-16 10:00:00,TSLA,BUY,50,200.00,1.00,Long entry
2024-01-16 15:30:00,TSLA,SELL,50,210.00,1.00,Exit with profit
2024-01-17 09:45:00,MSFT,BUY,75,300.00,1.00,Swing trade entry
2024-01-17 15:45:00,MSFT,SELL,75,295.00,1.00,Stop loss hit
```

### 🔍 What to Test

1. **Basic Functionality**
   - Register → Login → Upload trades → View analytics

2. **Edge Cases**
   - Upload empty CSV
   - Upload malformed data
   - Very large numbers
   - Special characters in notes

3. **Performance**
   - Upload 1000+ trades
   - Filter large datasets
   - Multiple browser tabs

4. **Security**
   - Try XSS in trade notes
   - Test unauthorized API access
   - Session management

### ⚡ Quick Troubleshooting

**Backend not responding?**
```bash
docker compose -f docker-compose.simple-alt.yml logs backend | tail -50
```

**Frontend errors?**
- Open browser console (F12)
- Check network tab for failed requests

**Database issues?**
```bash
# Connect to database
docker compose -f docker-compose.simple-alt.yml exec postgres psql -U tradesense -d tradesense

# Useful queries
\dt                    -- List tables
SELECT * FROM users;   -- View users
SELECT COUNT(*) FROM trades; -- Count trades
\q                     -- Exit
```

### 🎯 Ready to Test!

1. Open http://localhost:5173
2. Create an account
3. Start breaking things!
4. Document any issues you find

Remember: The goal is to find bugs before your users do!