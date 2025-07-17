# TradeSense Testing Guide

## Quick Start Options

### Option 1: Using the Start Script (Simplest)
```bash
# Fix any issues and start
./start.sh

# If it fails, check the logs
tail -f backend.log
```

### Option 2: Using Docker (Most Reliable)
```bash
# Build and run all services
docker-compose -f docker-compose.test.yml up --build

# Access the app at:
# - Frontend: http://localhost:5173
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Option 3: Manual Setup (Most Control)

#### Step 1: Start Database Services
```bash
# Start PostgreSQL
docker run -d --name tradesense-db \
  -e POSTGRES_PASSWORD=tradesense123 \
  -e POSTGRES_DB=tradesense \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d --name tradesense-redis \
  -e REDIS_PASSWORD=tradesense123 \
  -p 6379:6379 \
  redis:7-alpine redis-server --requirepass tradesense123
```

#### Step 2: Start Backend
```bash
cd src/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:tradesense123@localhost:5432/tradesense"
export REDIS_URL="redis://:tradesense123@localhost:6379/0"
export SECRET_KEY="test-secret-key"
export JWT_SECRET_KEY="test-jwt-secret"

# Run backend
python main.py
```

#### Step 3: Start Frontend
```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Test Accounts

Once the app is running, you can use these test accounts:

| Email | Password | Role | Features |
|-------|----------|------|----------|
| test@example.com | testpass123 | Free User | Basic features |
| pro@example.com | testpass123 | Pro User | Advanced analytics |
| admin@example.com | adminpass123 | Admin | All features |

## Testing Key Features

### 1. Authentication
- Sign up for a new account
- Login with test credentials
- Reset password flow
- Logout

### 2. Trade Management
- Upload trades via CSV
- Manual trade entry
- Edit existing trades
- Delete trades
- Filter and search trades

### 3. Analytics Dashboard
- View performance metrics
- Check win/loss ratios
- Analyze trade patterns
- Review P&L charts

### 4. Journal
- Create journal entries
- Link trades to entries
- Add tags and notes
- Search journal

### 5. Billing (Test Mode)
- View pricing page
- Test Stripe checkout
- Use test card: 4242 4242 4242 4242
- Any future date, any CVC

## API Testing

### Using cURL
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Get trades (need token from login)
curl http://localhost:8000/api/v1/trades \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using API Docs
1. Open http://localhost:8000/docs
2. Click "Authorize" button
3. Login with test credentials
4. Try out any endpoint

## Sample Test Data

### CSV Format for Trade Upload
```csv
symbol,side,quantity,entry_price,exit_price,entry_time,exit_time,commission,notes
AAPL,long,100,150.00,155.00,2024-01-15 09:30:00,2024-01-15 15:30:00,2.00,Test trade
GOOGL,short,50,2800.00,2750.00,2024-01-16 10:00:00,2024-01-16 14:00:00,2.00,Profitable short
```

## Troubleshooting

### Backend Won't Start
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Kill existing processes
pkill -f "python.*main.py"
docker stop tradesense-db tradesense-redis
docker rm tradesense-db tradesense-redis

# Check Python dependencies
pip list | grep -E "fastapi|uvicorn|sqlalchemy"
```

### Frontend Won't Start
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+ 
npm --version   # Should be 8+
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d tradesense -c "SELECT 1"

# Test Redis connection
redis-cli -a tradesense123 ping
```

### Import Errors
```bash
# Ensure you're in the right directory
cd src/backend

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Development Tips

### Watch Logs
```bash
# Backend logs
tail -f backend.log

# Frontend logs
# Check the terminal where npm run dev is running

# Docker logs
docker-compose -f docker-compose.test.yml logs -f
```

### Reset Everything
```bash
# Stop all services
./stop.sh
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Remove data
docker volume prune -f

# Start fresh
./start.sh
```

### Performance Testing
```bash
# Simple load test
for i in {1..100}; do
  curl -s http://localhost:8000/health &
done
wait
```

## Next Steps

1. **Explore the UI**: Click through all pages and features
2. **Upload test data**: Use the CSV format above
3. **Test integrations**: Try Stripe checkout, data export
4. **Check analytics**: Review all charts and metrics
5. **Test edge cases**: Empty states, errors, large datasets

## Getting Help

- Check logs in `backend.log` and browser console
- Review API docs at http://localhost:8000/docs
- Look at existing test files in `tests/` directory
- Check the deployment technical report for detailed configuration