# TradeSense Quick Start Guide
**Get the development environment running in 5 minutes**

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- PostgreSQL 12+ installed
- Git installed

## Quick Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd tradesense
```

### 2. Backend Setup (2 minutes)
```bash
# Navigate to backend
cd src/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env file with your database credentials
# Minimum required:
# DATABASE_URL=postgresql://user:password@localhost:5432/tradesense
# SECRET_KEY=your-secret-key-here

# Create database
createdb tradesense

# Run migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --port 8000
```

Backend should now be running at: http://localhost:8000
API docs available at: http://localhost:8000/docs

### 3. Frontend Setup (2 minutes)
```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

Frontend should now be running at: http://localhost:5173

## Quick Test

### 1. Create a Test User
1. Navigate to http://localhost:5173/register
2. Enter test credentials:
   - Username: testuser
   - Email: test@example.com
   - Password: Test123!@#

### 2. Verify Basic Functionality
1. Check dashboard loads
2. Try creating a manual trade
3. Access the journal
4. Test CSV upload

## Common Issues & Quick Fixes

### Backend won't start
```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -U postgres -c "\l" | grep tradesense

# Check port 8000 is free
lsof -i :8000
```

### Frontend won't start
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check port 5173 is free
lsof -i :5173
```

### Database connection errors
```bash
# Test database connection
psql postgresql://user:password@localhost:5432/tradesense

# Common fix - update .env file:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tradesense
```

## Essential Commands

### Backend
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest

# Format code
black .
```

### Frontend
```bash
# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Quick Development Tips

### 1. Enable Debug Mode
```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

### 2. Access Sample Data
Most components have fallback sample data when API fails. Just run frontend without backend to see UI with sample data.

### 3. Quick API Testing
```bash
# Test API is running
curl http://localhost:8000/health

# Get API docs
open http://localhost:8000/docs
```

### 4. Reset Database
```bash
# Drop and recreate
dropdb tradesense
createdb tradesense
alembic upgrade head
```

## Project Structure Overview
```
tradesense/
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── routes/        # Pages
│   │   ├── lib/           # Components & utilities
│   │   └── app.html       # Root HTML
│   └── package.json
├── src/backend/           # FastAPI backend
│   ├── api/               # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── main.py           # App entry point
├── docs/                  # Documentation
└── scripts/              # Utility scripts
```

## Next Steps
1. Read `DEVELOPMENT_NOTES.md` for coding patterns
2. Check `API_ENDPOINTS_DOCUMENTATION.md` for API reference
3. Review `UX_ERRORS_REPORT.md` for completed improvements
4. See `DEPLOYMENT_READINESS_CHECKLIST.md` before deploying

## Getting Help
- Check existing documentation in the repo
- Review error logs in browser console or terminal
- Most common issues are in the "Common Issues" section above

---

**Quick Links:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: postgresql://localhost:5432/tradesense