# 🚀 How to Run TradeSense - Simple Guide

## 📍 Quick Start (Copy & Paste Commands)

### Option 1: Use the Automated Script
```bash
cd /home/tarigelamin/Desktop/tradesense
./startup-fixed.sh
```

### Option 2: Manual Start (If Script Fails)

#### 1. Start Backend
```bash
cd /home/tarigelamin/Desktop/tradesense/src/backend
source ../../test_venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 2. Start Frontend (New Terminal)
```bash
cd /home/tarigelamin/Desktop/tradesense/frontend
npm run dev
```

## 🌐 Access Your App

Once both servers are running, open your browser and go to:

### Main Application
**http://localhost:3001**

### Important Pages
- **Home**: http://localhost:3001
- **Pricing**: http://localhost:3001/pricing
- **Login**: http://localhost:3001/login
- **Billing**: http://localhost:3001/billing (after login)

### Backend API
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## 👤 Test User Credentials

### Existing User
- **Email**: `demouser@test.com`
- **Password**: `Demo@123456`

### Or Create New User
1. Click "Sign Up" on the website
2. Use any email (e.g., yourname@test.com)
3. Password must have: uppercase, lowercase, number, and special character
   - Example: `MyPass@123`

## 🧪 What to Test

### 1. Basic Flow
1. Go to http://localhost:3001
2. Click "Sign Up" or "Login"
3. After login, click "Pricing" in the navbar
4. Explore the pricing plans
5. Click "Get Started" on any plan

### 2. Test Features
- **Pricing Page**: See all plans and features
- **Monthly/Yearly Toggle**: Switch pricing views
- **Billing Portal**: Manage subscription (after signup)
- **Feature Gates**: Some features require paid plans

## 🛠️ Troubleshooting

### If Backend Won't Start
```bash
# Kill existing process
pkill -f uvicorn

# Try again
cd /home/tarigelamin/Desktop/tradesense/src/backend
source ../../test_venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### If Frontend Won't Start
```bash
# Kill existing process
pkill -f "npm run dev"

# Try again
cd /home/tarigelamin/Desktop/tradesense/frontend
npm run dev
```

### If Port is Busy
Frontend might use port 3001 or 3002. Check the terminal output for the actual port.

## 📊 Check If Everything is Working

### Backend Health Check
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy",...}`

### Frontend Check
Open http://localhost:3001 in your browser. You should see the TradeSense homepage.

## 🛑 How to Stop Everything

### Option 1: Use Shutdown Script
```bash
cd /home/tarigelamin/Desktop/tradesense
./shutdown.sh
```

### Option 2: Manual Stop
Press `Ctrl+C` in each terminal window where servers are running.

### Option 3: Force Stop
```bash
pkill -f uvicorn
pkill -f "npm run dev"
```

## 💡 Tips for Testing

1. **Use Chrome/Firefox Developer Tools**
   - Press F12 to see network requests
   - Check Console for any errors

2. **Test Different Scenarios**
   - Sign up as new user
   - Try to access premium features
   - Test the pricing page interactions

3. **Note About Stripe**
   - Checkout will only work with real Stripe API keys
   - You'll see the UI but need Stripe account for actual payments

## 📝 Quick Commands Reference

```bash
# Navigate to project
cd /home/tarigelamin/Desktop/tradesense

# Start everything
./startup-fixed.sh

# Check backend logs
tail -f backend_working.log

# Check if services are running
ps aux | grep -E "uvicorn|npm"

# Stop everything
./shutdown.sh
```

## 🎯 Ready to Test!

1. Run the startup script
2. Wait for both servers to start (about 10 seconds)
3. Open http://localhost:3001
4. Login with test credentials
5. Explore your new billing system!

---
**Need Help?** Check the logs or try the manual start commands above.