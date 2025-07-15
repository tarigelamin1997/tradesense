# 🔐 Fix Login Issues - Quick Guide

## Current Situation
- Login failing with 401 Unauthorized
- test@example.com exists but password unknown
- Need to reset password or create new user

## Option 1: Reset Test User (Recommended)
```bash
cd src/backend
python reset_test_user.py
```
This will:
- Delete existing test@example.com
- Create fresh user with password: **Password123!**

## Option 2: Create New Demo User
```bash
cd src/backend
python create_new_user.py
```
This creates:
- Email: **demo@tradesense.com**
- Password: **DemoPass123!**

## Option 3: Register via UI
1. Go to http://localhost:5173/register
2. Create new account:
   - Email: your-email@example.com
   - Password: YourPass123!
   - Fill other fields

## Option 4: Check Database Directly
```bash
# If PostgreSQL is accessible:
psql -U postgres -d tradesense -f check_users.sql
```

## After Reset/Creation
1. Start backend: `cd src/backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Login with your credentials
4. Dashboard should load with trade data

## Known Working Credentials (after reset):
- **test@example.com** / **Password123!**
- **demo@tradesense.com** / **DemoPass123!**

## Troubleshooting
- If scripts fail: Make sure backend is running first
- If login still fails: Check browser console for errors
- If no trades show: Run `seed_trades.py` again

## Quick Test
```bash
# Test login via API directly:
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!"}'
```

Success response should include access_token.