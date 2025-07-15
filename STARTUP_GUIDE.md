# 🚀 TradeSense Startup Guide

## Quick Start

There is now **ONE** unified way to start TradeSense:

```bash
./start.sh
```

To stop everything:

```bash
./stop.sh
```

That's it! The script handles everything automatically.

## Features of the Unified Script

### ✅ Automatic Setup
- Creates virtual environment if missing
- Installs dependencies if needed
- Creates necessary directories
- Cleans up old processes

### ✅ Smart Port Management
- Kills processes on required ports
- Detects actual frontend port (3000, 3001, etc.)
- Tracks PIDs for clean shutdown

### ✅ Professional Output
- Color-coded status messages
- Progress indicators
- Clear error messages
- Success summary with all URLs

### ✅ Comprehensive Information
- Shows all access URLs
- Displays test credentials
- Lists test credit card numbers
- Provides useful commands

### ✅ Error Recovery
- Validates directory structure
- Checks service health
- Shows logs on failure
- Handles corrupted environments

### ✅ Browser Integration
- Automatically opens frontend in browser
- Works on Linux and macOS

## What You'll See

When you run `./start.sh`, you'll see:

```
🚀 TradeSense Startup Script v2.0
=================================

📧 Cleaning up previous sessions...
✓ Stopped previous backend (PID: 12345)
ℹ Cleared port 8000

🐍 Setting up Python environment...
✓ Activated virtual environment

🔧 Starting Backend Server...
✓ Backend is running! (PID: 12456)

🎨 Starting Frontend Server...
✓ Frontend is running! (PID: 12567)

✨ TradeSense is running!
========================

📍 Access URLs:
  Frontend: http://localhost:3001
  Backend API: http://localhost:8000
  API Documentation: http://localhost:8000/api/docs

👤 Test Credentials:
  Email: demouser@test.com
  Password: Demo@123456

🔗 Quick Links:
  Home: http://localhost:3001
  Pricing: http://localhost:3001/pricing
  Login: http://localhost:3001/login
  Billing: http://localhost:3001/billing (after login)

💳 Test Credit Cards:
  Success: 4242 4242 4242 4242
  3D Secure: 4000 0025 0000 3155
  Declined: 4000 0000 0000 9995

📝 Useful Commands:
  View logs: tail -f logs/backend.log
  Stop all: ./stop.sh
  Check health: curl http://localhost:8000/health

🎉 Enjoy using TradeSense!
```

## Troubleshooting

### If the script fails:

1. **Check logs:**
   - Backend: `tail -50 logs/backend.log`
   - Frontend: `tail -50 logs/frontend.log`

2. **Manual cleanup:**
   ```bash
   pkill -f uvicorn
   pkill -f "npm run dev"
   ```

3. **Port conflicts:**
   ```bash
   lsof -i:8000  # Check what's using backend port
   lsof -i:5173  # Check what's using frontend port
   ```

4. **Virtual environment issues:**
   ```bash
   rm -rf test_venv
   ./start.sh  # Will recreate it
   ```

## Advanced Usage

### Stripe Webhook Testing
If you have Stripe CLI installed:
```bash
# In another terminal after starting TradeSense
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

### Direct Log Monitoring
```bash
# Watch backend logs
tail -f logs/backend.log

# Watch frontend logs
tail -f logs/frontend.log
```

### Health Checks
```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/api/docs
```

## Notes

- The script uses `test_venv` as the virtual environment
- Logs are stored in the `logs/` directory
- PIDs are tracked in `.pids/` directory
- The `stop.sh` script is auto-generated each time

## Migration from Old Scripts

All previous startup scripts have been removed:
- ~~startup-fixed.sh~~
- ~~start-tradesense.sh~~
- ~~start_servers.sh~~
- ~~start_dev.sh~~
- ~~quick-start.sh~~

Use only `./start.sh` going forward!