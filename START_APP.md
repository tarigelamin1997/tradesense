# 🚀 How to Start TradeSense - Simple Method

## Quick Start (Recommended)

### Option 1: Use the run-with-docker script
```bash
./run-with-docker.sh
```

This script:
- Creates a simple docker-compose.yml
- Starts all services
- Backend on http://localhost:8000
- Frontend on http://localhost:5173

### Option 2: Manual Docker Compose
```bash
# Use the bulletproof configuration (most reliable)
docker compose -f docker-compose.bulletproof.yml up -d

# Wait 2-3 minutes for first build
# Then access http://localhost:5173
```

### Option 3: Fix Backend Dependencies
If backend fails with "sklearn" error:

1. Create a file `src/backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install scikit-learn pydantic-settings
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Rebuild and start:
```bash
docker compose -f docker-compose.bulletproof.yml up -d --build
```

## Current Issue

The backend is missing dependencies:
- scikit-learn (for pattern detection)
- pydantic-settings (for configuration)

These aren't in the main requirements.txt file, causing the backend to crash.

## Working Solution

1. **Stop everything**:
```bash
docker compose down
```

2. **Add missing deps to src/backend/requirements.txt**:
```bash
echo "pydantic-settings" >> src/backend/requirements.txt
```

3. **Use bulletproof config** (builds custom images):
```bash
docker compose -f docker-compose.bulletproof.yml up -d
```

4. **Wait for build** (2-3 minutes first time)

5. **Access the app**:
- Frontend: http://localhost:5173
- Create account and test!

## Test Credentials
- Create any account you want
- Password must have: Uppercase, lowercase, number, special char
- Example: TestUser123!

## If All Else Fails

Use the development databases with local backend:
```bash
# Start only databases
docker compose -f docker-compose.simple-alt.yml up -d postgres redis

# Install backend locally
cd src/backend
pip install -r requirements.txt
pip install uvicorn pydantic-settings scikit-learn

# Run backend
DATABASE_URL=postgresql://tradesense:tradesense@localhost:5433/tradesense \
REDIS_URL=redis://localhost:6380 \
SECRET_KEY=test \
uvicorn main:app --reload

# In another terminal, run frontend
cd frontend
npm install
npm run dev
```

Then access http://localhost:5173