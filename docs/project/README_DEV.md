
# TradeSense Backend - Developer Guide

## 🏗️ Architecture Overview

TradeSense has been refactored from a Streamlit prototype into a production-ready FastAPI backend with clear separation of concerns:

```
app/
├── main.py              # FastAPI app entry point
├── routers/             # API endpoints organized by feature
│   ├── auth.py         # Authentication (login, register, JWT)
│   ├── analytics.py    # Trade analytics and performance
│   ├── scheduler.py    # Email scheduling and notifications
│   ├── journaling.py   # Trade journaling and reflections
│   ├── admin.py        # Admin dashboard and user management
│   └── exports.py      # PDF/CSV exports
├── services/            # Business logic layer
│   ├── auth_service.py     # JWT tokens, password hashing
│   ├── analytics_service.py # Performance calculations
│   ├── database_service.py # Database operations
│   └── email_service.py    # Email sending and scheduling
├── models/              # Pydantic data models
│   ├── user.py         # User authentication models
│   ├── analytics.py    # Analytics response models
│   └── journal.py      # Journaling data models
└── config/
    └── settings.py     # Environment configuration
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Backend dependencies are auto-installed in Replit
# For local development:
pip install fastapi uvicorn pandas numpy bcrypt pyjwt
```

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
JWT_SECRET_KEY=your-super-secret-jwt-key
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DATABASE_URL=sqlite:///./tradesense.db
```

### 3. Run the Backend
```bash
# Method 1: Direct execution
python app/main.py

# Method 2: Via uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Method 3: Use Replit Run button (configured for Full Stack Development)
```

### 4. Test API Endpoints
Open your browser to:
- **API Documentation:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/api/health
- **Root Endpoint:** http://localhost:8000/

## 📡 API Endpoints

### Authentication
```bash
# Register new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "trader1", "email": "trader@example.com", "password": "securepass", "confirm_password": "securepass"}'

# Login and get JWT token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "trader1", "password": "securepass"}'

# Get current user profile (requires token)
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Analytics
```bash
# Get dashboard metrics
curl -X GET "http://localhost:8000/api/analytics/dashboard" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Upload trade data
curl -X POST "http://localhost:8000/api/analytics/upload-trades" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@your_trades.csv"

# Get performance metrics
curl -X GET "http://localhost:8000/api/analytics/performance" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Email Scheduler
```bash
# Schedule daily report
curl -X POST "http://localhost:8000/api/scheduler/schedule" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email_type": "daily_report", "schedule_time": "09:00:00", "enabled": true}'
```

## 🔗 Frontend Integration

### React/JavaScript Example
```javascript
// Authentication
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
};

// Get analytics data
const getDashboard = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:8000/api/analytics/dashboard', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Upload trades
const uploadTrades = async (file) => {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/analytics/upload-trades', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  return response.json();
};
```

## 🛠️ Adding New Features

### 1. Create a New Router
```python
# app/routers/my_feature.py
from fastapi import APIRouter, Depends
from app.services.auth_service import get_current_user

router = APIRouter()

@router.get("/endpoint")
async def my_endpoint(user=Depends(get_current_user)):
    return {"message": "Hello from new feature"}
```

### 2. Register Router in Main App
```python
# app/main.py
from app.routers import my_feature

app.include_router(my_feature.router, prefix="/api/my-feature", tags=["My Feature"])
```

### 3. Create Service Layer
```python
# app/services/my_feature_service.py
class MyFeatureService:
    def __init__(self):
        self.db = DatabaseService()
    
    async def do_something(self, user_id: int):
        # Business logic here
        pass
```

### 4. Add Data Models
```python
# app/models/my_feature.py
from pydantic import BaseModel

class MyFeatureRequest(BaseModel):
    name: str
    value: int

class MyFeatureResponse(BaseModel):
    id: int
    name: str
    value: int
```

## 🗄️ Database Operations

### Adding New Tables
```python
# In app/services/database_service.py, add to init_database():
conn.execute("""
    CREATE TABLE IF NOT EXISTS my_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
""")
```

### Adding New Database Methods
```python
async def create_my_record(self, data: Dict) -> Dict:
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO my_table (user_id, name) VALUES (?, ?)
            """, (data["user_id"], data["name"]))
            
            record_id = cursor.lastrowid
            data["id"] = record_id
            return data
    except Exception as e:
        logger.error(f"Create record failed: {e}")
        raise
```

## 🔐 Security Features

- **JWT Authentication:** Stateless token-based auth
- **Password Hashing:** bcrypt with salt
- **CORS Protection:** Configured for frontend origins
- **Input Validation:** Pydantic models validate all inputs
- **SQL Injection Protection:** Parameterized queries

## 📊 Monitoring & Logging

- **Health Checks:** `/api/health` endpoint
- **Request Logging:** All requests logged with timestamps
- **Error Handling:** Global exception handler
- **Database Monitoring:** Connection status in health checks

## 🚀 Deployment Checklist

1. **Environment Variables:** Set production values in `.env`
2. **Database:** Initialize with `python -c "from app.services.database_service import DatabaseService; DatabaseService()"`
3. **JWT Secret:** Generate secure random key
4. **SMTP Settings:** Configure email service
5. **Frontend CORS:** Update allowed origins

## 🧪 Testing

```bash
# Run basic health check
curl http://localhost:8000/api/health

# Test authentication flow
curl -X POST http://localhost:8000/api/auth/register -d '{"username":"test","email":"test@example.com","password":"test","confirm_password":"test"}' -H "Content-Type: application/json"

# Test with sample data
curl -X GET http://localhost:8000/api/analytics/dashboard -H "Authorization: Bearer TOKEN"
```

## 🎯 Production Readiness

✅ **Complete:** Modular FastAPI structure
✅ **Complete:** JWT authentication system  
✅ **Complete:** Database layer with SQLite
✅ **Complete:** API documentation with Swagger
✅ **Complete:** Error handling and logging
✅ **Complete:** CORS configuration for frontend
✅ **Complete:** File upload processing
✅ **Complete:** Environment configuration

🔄 **Next Steps for Full Production:**
- Add Redis for session management
- Implement rate limiting
- Add comprehensive test suite
- Set up CI/CD pipeline
- Add database migrations
- Implement email templates
- Add monitoring dashboard

## 📞 Support

For questions or issues:
1. Check API docs at `/api/docs`
2. Review logs in `logs/tradesense.log`
3. Test endpoints with curl or Postman
4. Verify environment variables in `.env`

The backend is now production-ready and can be deployed independently of any frontend framework.
