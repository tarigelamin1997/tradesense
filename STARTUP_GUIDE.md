# TradeSense Startup Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js 16+** and npm installed
3. **PostgreSQL** or SQLite (default) for database
4. **Virtual environment** activated (optional but recommended)

## Frontend Technology

TradeSense now uses **SvelteKit** for the frontend, providing:
- ⚡ 50-70% less code than React
- 🚀 Blazing fast performance with no virtual DOM
- 📊 Clean, minimal UI with custom CSS
- 🔄 Simple state management with Svelte stores

## Quick Start

### Option 1: Using the startup script (Recommended)

```bash
# Make sure the script is executable
chmod +x start.sh

# Run the startup script
./start.sh
```

### Option 2: Manual startup

#### 1. Start Backend

```bash
# Navigate to backend directory
cd src/backend

# Install Python dependencies (if not already done)
pip install -r ../../requirements.txt

# Run the backend
python main.py

# Or with uvicorn for better performance
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will start on http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- Alternative API Docs: http://localhost:8000/api/redoc

#### 2. Start Frontend

In a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

The frontend will start on http://localhost:3001

## Default Test Credentials

After starting the app, you can use these test credentials:

**Regular User:**
- Email: john.trader@example.com
- Password: SecurePass123!

**Admin User:**
- Email: admin@tradesense.com
- Password: AdminPass123!

## Troubleshooting

### Backend Issues

1. **Import Error for WebSocket**
   - Already fixed! The `get_current_user_ws` function has been added.

2. **Database Connection Error**
   - Check if PostgreSQL is running (if using PostgreSQL)
   - For SQLite, ensure write permissions in the project directory
   - Check `.env` file for correct DATABASE_URL

3. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Kill process on port 3001
   lsof -ti:3001 | xargs kill -9
   ```

### Frontend Issues

1. **npm install fails**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Delete node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Vite errors**
   - Make sure you're using Node.js 16+
   - Check that all environment variables are set

## Environment Configuration

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./tradesense.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/tradesense

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256

# CORS Origins
CORS_ORIGINS=http://localhost:3001,http://localhost:5173

# Environment
ENVIRONMENT=development
```

## Testing the Application

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Login Test**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "john.trader@example.com", "password": "SecurePass123!"}'
   ```

3. **Frontend Access**
   - Open http://localhost:3001 in your browser
   - Try logging in with the test credentials

## Security Notes

- All critical security vulnerabilities have been fixed
- Rate limiting is active (5 login attempts per 5 minutes)
- Input validation prevents SQL injection
- Timeout protection prevents DoS attacks
- CORS is properly configured for localhost only

## Production Deployment

Before deploying to production:

1. Set `ENVIRONMENT=production` in `.env`
2. Use a strong `JWT_SECRET_KEY`
3. Configure proper CORS origins
4. Use PostgreSQL instead of SQLite
5. Build frontend for production: `npm run build`
6. Use a process manager like PM2 or systemd
7. Set up HTTPS with SSL certificates
8. Configure a reverse proxy (nginx/Apache)

## Need Help?

1. Check the logs:
   - Backend: `logs/backend.log`
   - Frontend: Browser console

2. Verify all dependencies are installed:
   ```bash
   pip list | grep -E "fastapi|sqlalchemy|pydantic"
   npm list | grep -E "react|vite|axios"
   ```

3. Make sure all services are running:
   - Backend on http://localhost:8000
   - Frontend on http://localhost:3001
   - Database connection is active