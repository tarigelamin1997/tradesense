# TradeSense Project Bible
*Last Updated: January 11, 2025*

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Component Catalog](#component-catalog)
5. [Database Schema](#database-schema)
6. [API Documentation](#api-documentation)
7. [Frontend Architecture](#frontend-architecture)
8. [Development Playbook](#development-playbook)
9. [Technical Debt Register](#technical-debt-register)
10. [Immediate Action Plan](#immediate-action-plan)

---

## Executive Summary

### 30-Second Elevator Pitch
TradeSense is a trading analytics platform migrating from Streamlit to FastAPI/React. It helps traders track performance, analyze patterns, and improve through journaling and AI-powered insights. Currently 75% migrated with working auth and basic trade management, but critical features need completion for the 4-week launch goal.

### Current Status Snapshot
- **Migration Progress**: 75% complete (Streamlit → FastAPI/React)
- **Database**: PostgreSQL (migrated from SQLite)
- **Authentication**: ✅ Working (JWT-based)
- **Trade Management**: 🟡 Partial (basic CRUD only)
- **Analytics**: 🟡 Backend ready, frontend disconnected
- **Payment System**: ❌ Not implemented
- **Production Readiness**: ~40%

### Critical Issues
1. **Security**: Hardcoded JWT secrets, wildcard CORS
2. **Configuration**: Frontend expects wrong API port (8080 vs 8000)
3. **Performance**: No caching, no connection pooling
4. **Testing**: <40% coverage, broken test imports

### What's Working vs What's Not

#### ✅ Fully Functional
- JWT authentication system (login/register/logout)
- PostgreSQL database with 19 models
- FastAPI framework with 25+ routers
- Basic React frontend structure
- Trade CRUD operations (backend)

#### 🟡 Partially Working
- Analytics engine (backend only)
- Dashboard UI (not connected to backend)
- File upload system (no UI)
- Trade filtering/search (basic only)
- Email service (not configured)

#### ❌ Broken or Missing
- Frontend-Backend connection (port mismatch)
- Payment integration (Stripe)
- Real-time features (WebSockets)
- Market data integration
- Production deployment setup

---

## Project Overview

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.95.0
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **Task Queue**: Celery (configured but not used)
- **Caching**: Redis (planned, not configured)
- **Testing**: pytest

#### Frontend
- **Framework**: React 18.2.0 with TypeScript
- **Build Tool**: Vite 4.4.5
- **State Management**: Zustand 4.3.6
- **API Client**: Axios + React Query
- **UI Framework**: Tailwind CSS + Radix UI
- **Charts**: Recharts
- **Testing**: Jest + React Testing Library

### Project Structure
```
tradesense/
├── src/
│   └── backend/              # FastAPI backend
│       ├── api/              # API endpoints
│       │   └── v1/           # Version 1 API
│       ├── core/             # Core utilities
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic
│       └── main.py           # Application entry
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   ├── stores/           # Zustand stores
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Utilities
│   └── package.json
├── docs/                     # Documentation
├── infra/                    # Infrastructure configs
├── backups/                  # Migration backups
└── tests/                    # Test suites
```

### Migration History
- **Phase 1**: Database migration (SQLite → PostgreSQL) ✅
- **Phase 2**: Backend migration (Streamlit → FastAPI) 🟡
- **Phase 3**: Frontend creation (New React app) 🟡
- **Phase 4**: Feature parity with Streamlit ❌
- **Phase 5**: New features and scaling ❌

---

## System Architecture

### High-Level Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React SPA     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│  (Port 5173)    │     │  (Port 8000)    │     │  (Port 5432)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                        │
        │                        │                        │
    Zustand                 JWT Auth                SQLAlchemy
    Storage                Middleware                   ORM
```

### Authentication Flow
```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Database
    
    User->>Frontend: Enter credentials
    Frontend->>API: POST /api/v1/auth/login
    API->>Database: Verify user
    Database-->>API: User data
    API->>API: Generate JWT
    API-->>Frontend: JWT token
    Frontend->>Frontend: Store in localStorage
    Frontend->>API: Subsequent requests with Bearer token
```

### Data Flow Architecture
```
User Actions → React Components → API Services → Axios Client
                    ↓                               ↓
                UI Updates ← Zustand Store ← API Response
                    ↓
              Recharts Viz

Backend Flow:
HTTP Request → FastAPI Router → Dependency Injection → Service Layer
                    ↓                                      ↓
            Response Model ← Pydantic Schema ← Database Query
```

### API Structure
```
/api/v1/
├── auth/                    # Authentication endpoints
│   ├── POST   /login       # User login
│   ├── POST   /register    # User registration
│   ├── GET    /profile     # Get current user
│   └── POST   /logout      # Logout user
├── trades/                  # Trade management
│   ├── GET    /           # List trades
│   ├── POST   /           # Create trade
│   ├── GET    /{id}       # Get trade
│   ├── PUT    /{id}       # Update trade
│   ├── DELETE /{id}       # Delete trade
│   └── POST   /bulk       # Bulk operations
├── analytics/               # Analytics engine
│   ├── GET    /summary    # Performance summary
│   ├── GET    /streaks    # Win/loss streaks
│   ├── GET    /emotions   # Emotional analysis
│   └── GET    /patterns   # Pattern detection
├── uploads/                 # File handling
│   ├── POST   /csv        # Upload CSV
│   ├── POST   /parse      # Parse file
│   └── GET    /status     # Upload status
└── portfolio/              # Portfolio management
    ├── GET    /           # List portfolios
    └── POST   /optimize   # Optimization
```

---

## Component Catalog

### Backend Components

#### Core Services (`src/backend/core/`)

##### Authentication & Security
```python
# core/security.py
**Purpose**: JWT token generation and validation
**Status**: 🟢 Working
**Key Functions**:
- create_access_token(data: dict) -> str
- verify_token(token: str) -> dict
**Issues**: 
- Hardcoded secret key
- No refresh token support
```

##### Database Configuration
```python
# core/db/session.py
**Purpose**: Database connection management
**Status**: 🟡 Partial
**Configuration**:
- URL: postgresql://postgres:postgres@localhost/tradesense
- No connection pooling
- Synchronous queries in async context
**TODO**: Add connection pooling, async support
```

#### API Endpoints (`src/backend/api/v1/`)

##### Authentication Module
```
📁 auth/
├── router.py          🟢 Working - Login, register, profile endpoints
├── service.py         🟢 Working - User authentication logic
├── schemas.py         🟢 Working - Request/response models
└── dependencies.py    🟢 Working - JWT verification
```

##### Trade Management Module
```
📁 trades/
├── router.py          🟡 Partial - CRUD works, search incomplete
├── service.py         🟡 Partial - Basic operations only
├── schemas.py         🟢 Working - Trade data models
└── filters.py         🔴 Broken - Advanced filtering not implemented
```

##### Analytics Module
```
📁 analytics/
├── router.py          🟡 Partial - Endpoints defined, not all tested
├── service.py         🟢 Working - Calculation logic complete
├── schemas.py         🟢 Working - Analytics response models
├── performance.py     🟢 Working - Performance metrics
├── streaks.py         🟢 Working - Win/loss streak analysis
└── emotions.py        ⚫ Unknown - Emotional impact analysis
```

### Frontend Components

#### Core Components (`frontend/src/components/`)

##### Layout Components
```typescript
// Layout/AppLayout.tsx
**Purpose**: Main application layout wrapper
**Status**: 🟢 Working
**Features**: Sidebar, header, responsive design
**Dependencies**: React Router, auth store
```

##### Dashboard
```typescript
// Dashboard.tsx
**Purpose**: Main analytics dashboard
**Status**: 🟡 Partial
**Issues**: 
- Hardcoded to wrong API endpoint
- Not receiving real data
- Missing error handling
**TODO**: 
- Fix API connection
- Add loading states
- Implement real-time updates
```

##### Trade Management
```typescript
// TradeLog.tsx
**Purpose**: Display and manage trades
**Status**: 🔴 Broken
**Issues**: Not connected to backend
**Dependencies**: Trade service, data table component
```

#### Service Layer (`frontend/src/services/`)

##### API Client
```typescript
// api.ts
**Configuration**:
- Base URL: http://localhost:8000 (hardcoded as 8080)
- Timeout: 30 seconds
- Auth: Bearer token from localStorage
**Interceptors**: 
- Request: Adds auth token
- Response: Handles 401 errors
```

##### Feature Services
```typescript
// analytics.ts    🟡 Partial - Methods defined, not tested
// auth.ts         🟢 Working - Login/register/logout
// trades.ts       🟡 Partial - CRUD methods incomplete
// upload.ts       ⚫ Unknown - Not implemented
```

---

## Database Schema

### Entity Relationship Diagram
```
User (1) ──────< (∞) Trade
  │                    │
  │                    ├────< TradeNote
  │                    ├────< TradeReview
  │                    └────< TradeTag
  │
  ├──────< Portfolio
  ├──────< TradingAccount
  ├──────< Playbook
  └──────< DailyReflection
```

### Core Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### trades
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    symbol VARCHAR NOT NULL,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    entry_price DECIMAL,
    exit_price DECIMAL,
    quantity INTEGER,
    trade_type VARCHAR, -- 'long' or 'short'
    pnl DECIMAL,
    pnl_percentage DECIMAL,
    strategy_id UUID,
    emotions_before VARCHAR[],
    emotions_after VARCHAR[],
    confidence_level INTEGER,
    created_at TIMESTAMP
);
```

#### portfolios
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR NOT NULL,
    initial_balance DECIMAL,
    current_balance DECIMAL,
    currency VARCHAR DEFAULT 'USD',
    created_at TIMESTAMP
);
```

### Indexes and Constraints
```sql
-- Performance indexes
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_symbol ON trades(symbol);

-- Composite indexes for common queries
CREATE INDEX idx_trades_user_date ON trades(user_id, entry_time);
CREATE INDEX idx_trades_user_strategy ON trades(user_id, strategy_id);
```

---

## API Documentation

### Authentication Endpoints

#### POST /api/v1/auth/register
```json
// Request
{
  "email": "trader@example.com",
  "password": "SecurePass123!",
  "full_name": "John Trader"
}

// Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "trader@example.com",
    "full_name": "John Trader"
  }
}
```

#### POST /api/v1/auth/login
```json
// Request
{
  "email": "trader@example.com",
  "password": "SecurePass123!"
}

// Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Trade Management Endpoints

#### GET /api/v1/trades
```json
// Query Parameters
?limit=20&offset=0&symbol=AAPL&start_date=2024-01-01

// Response
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "symbol": "AAPL",
      "entry_time": "2024-01-15T09:30:00Z",
      "exit_time": "2024-01-15T10:45:00Z",
      "entry_price": 150.25,
      "exit_price": 152.50,
      "quantity": 100,
      "trade_type": "long",
      "pnl": 225.00,
      "pnl_percentage": 1.5
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### POST /api/v1/trades
```json
// Request
{
  "symbol": "AAPL",
  "entry_time": "2024-01-15T09:30:00Z",
  "exit_time": "2024-01-15T10:45:00Z",
  "entry_price": 150.25,
  "exit_price": 152.50,
  "quantity": 100,
  "trade_type": "long",
  "strategy_id": "550e8400-e29b-41d4-a716-446655440000",
  "emotions_before": ["confident", "focused"],
  "emotions_after": ["satisfied", "calm"],
  "confidence_level": 8
}

// Response
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "pnl": 225.00,
  "pnl_percentage": 1.5,
  ...
}
```

### Analytics Endpoints

#### GET /api/v1/analytics/summary
```json
// Query Parameters
?start_date=2024-01-01&end_date=2024-12-31

// Response
{
  "total_trades": 150,
  "total_pnl": 15750.50,
  "win_rate": 65.5,
  "profit_factor": 2.3,
  "average_win": 450.25,
  "average_loss": -195.50,
  "best_trade": {
    "symbol": "NVDA",
    "pnl": 2500.00,
    "date": "2024-03-15"
  },
  "worst_trade": {
    "symbol": "META",
    "pnl": -850.00,
    "date": "2024-02-20"
  }
}
```

---

## Frontend Architecture

### Component Hierarchy
```
App.tsx
├── AuthProvider
│   └── Router
│       ├── PublicRoute
│       │   ├── Login
│       │   ├── Register
│       │   └── Landing
│       └── PrivateRoute
│           └── AppLayout
│               ├── Sidebar
│               ├── Header
│               └── MainContent
│                   ├── Dashboard
│                   ├── TradeLog
│                   ├── Analytics
│                   ├── Journal
│                   └── Settings
```

### State Management

#### Zustand Stores
```typescript
// stores/authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

// stores/tradeStore.ts
interface TradeState {
  trades: Trade[];
  loading: boolean;
  error: string | null;
  fetchTrades: (filters?: TradeFilters) => Promise<void>;
  createTrade: (trade: CreateTradeDto) => Promise<void>;
  updateTrade: (id: string, trade: UpdateTradeDto) => Promise<void>;
  deleteTrade: (id: string) => Promise<void>;
}
```

### Component Patterns

#### Data Fetching Pattern
```typescript
// Using React Query
const useTrades = (filters?: TradeFilters) => {
  return useQuery({
    queryKey: ['trades', filters],
    queryFn: () => tradeService.getTrades(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Component usage
function TradeList() {
  const { data: trades, isLoading, error } = useTrades();
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return <TradeTable trades={trades} />;
}
```

#### Form Handling Pattern
```typescript
// Using React Hook Form + Zod
const tradeSchema = z.object({
  symbol: z.string().min(1, 'Symbol is required'),
  entry_price: z.number().positive('Price must be positive'),
  quantity: z.number().int().positive('Quantity must be positive'),
});

function CreateTradeForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(tradeSchema),
  });
  
  const onSubmit = async (data: TradeFormData) => {
    await tradeService.createTrade(data);
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
}
```

---

## Development Playbook

### Getting Started

#### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis (optional, for caching)

#### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd tradesense

# Backend setup
cd src/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost/tradesense
JWT_SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost:5173
EOF

# Run migrations
alembic upgrade head

# Start backend
python main.py

# Frontend setup (new terminal)
cd frontend
npm install

# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:8000
EOF

# Start frontend
npm run dev
```

### Common Development Tasks

#### Creating a New Feature

1. **Backend API Endpoint**
```python
# src/backend/api/v1/feature/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.deps import get_current_user, get_db

router = APIRouter()

@router.get("/")
async def get_features(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Implementation
    pass
```

2. **Frontend Service**
```typescript
// frontend/src/services/feature.ts
import { api } from './api';

export const featureService = {
  getFeatures: async () => {
    const response = await api.get('/api/v1/feature');
    return response.data;
  },
};
```

3. **React Component**
```typescript
// frontend/src/components/Feature.tsx
import { useQuery } from '@tanstack/react-query';
import { featureService } from '../services/feature';

export function Feature() {
  const { data, isLoading } = useQuery({
    queryKey: ['features'],
    queryFn: featureService.getFeatures,
  });
  
  // Component implementation
}
```

#### Running Tests
```bash
# Backend tests
cd src/backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

#### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Database shell
psql -U postgres -d tradesense
```

### Debugging Tips

#### Backend Debugging
```python
# Add to any endpoint for debugging
import logging
logger = logging.getLogger(__name__)

@router.get("/debug")
async def debug_endpoint():
    logger.info("Debug info here")
    import pdb; pdb.set_trace()  # Breakpoint
    return {"status": "debugging"}
```

#### Frontend Debugging
```typescript
// Browser DevTools
console.log('Component state:', { trades, loading, error });

// React DevTools
// Install browser extension for component inspection

// Network debugging
window.__API_REQUESTS__ = [];
axios.interceptors.request.use(config => {
  window.__API_REQUESTS__.push(config);
  return config;
});
```

---

## Technical Debt Register

### 🔴 Critical Issues (Fix Immediately)

#### 1. Security Vulnerabilities
```python
# Location: src/backend/core/config.py
# Current:
JWT_SECRET_KEY = "your-secret-key-here"  # HARDCODED!

# Fix:
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable not set")
```
**Impact**: Complete authentication bypass possible
**Effort**: 30 minutes
**Priority**: P0

#### 2. CORS Configuration
```python
# Location: src/backend/main.py
# Current:
origins = ["*"]  # ALLOWS ANY ORIGIN!

# Fix:
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://yourdomain.com"
]
```
**Impact**: Cross-site scripting vulnerabilities
**Effort**: 15 minutes
**Priority**: P0

#### 3. API URL Mismatch
```typescript
// Location: frontend/src/services/api.ts
// Current:
const API_BASE_URL = 'http://localhost:8080';  // WRONG PORT!

// Fix:
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```
**Impact**: Frontend cannot connect to backend
**Effort**: 15 minutes
**Priority**: P0

### 🟡 Performance Issues

#### 1. Database Connection Pooling
```python
# Location: src/backend/core/db/session.py
# Add:
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)
```
**Impact**: Database connection exhaustion under load
**Effort**: 1 hour
**Priority**: P1

#### 2. Missing Indexes
```sql
-- Add these indexes for common queries
CREATE INDEX idx_trades_user_symbol ON trades(user_id, symbol);
CREATE INDEX idx_trades_date_range ON trades(user_id, entry_time, exit_time);
CREATE INDEX idx_analytics_user_date ON analytics_cache(user_id, date);
```
**Impact**: Slow queries on large datasets
**Effort**: 2 hours
**Priority**: P1

### ⚫ Code Quality Issues

#### 1. Mixed Sync/Async Patterns
```python
# Many services use sync database calls in async endpoints
# Example: src/backend/api/v1/trades/service.py
# Need to convert all database operations to async
```
**Impact**: Thread blocking, poor performance
**Effort**: 8 hours
**Priority**: P2

#### 2. No Error Boundaries
```typescript
// Add to frontend/src/components/ErrorBoundary.tsx
export class ErrorBoundary extends Component {
  // Implementation needed
}
```
**Impact**: White screen on component errors
**Effort**: 4 hours
**Priority**: P2

### Technical Debt Summary

| Priority | Count | Total Effort | Business Impact |
|----------|-------|--------------|-----------------|
| P0 (Critical) | 3 | 1 hour | Blocks all development |
| P1 (High) | 5 | 12 hours | Performance/Scale issues |
| P2 (Medium) | 8 | 24 hours | Code maintainability |
| P3 (Low) | 15 | 40 hours | Nice to have |

---

## Immediate Action Plan

### Day 1: Critical Fixes (3 hours)
1. **Fix API URL Configuration** (30 min)
   - Update frontend API client
   - Add environment variable support
   - Test connection

2. **Secure JWT Implementation** (30 min)
   - Move secret to environment
   - Generate secure key
   - Update deployment docs

3. **Fix CORS Configuration** (30 min)
   - Restrict to specific origins
   - Add environment-based config
   - Test cross-origin requests

4. **Verify Core Functionality** (90 min)
   - Test registration flow
   - Test login and token storage
   - Create sample trade
   - Verify dashboard loads

### Week 1: Foundation (40 hours)
- **Monday**: Fix critical security and config issues
- **Tuesday**: Complete trade search/filtering
- **Wednesday**: Connect analytics dashboard
- **Thursday**: Implement CSV upload UI
- **Friday**: Add error handling and loading states

### Week 2: Core Features (40 hours)
- Complete trade management UI
- Implement journal functionality
- Add portfolio tracking
- Basic reporting features
- Performance optimizations

### Week 3: Advanced Features (40 hours)
- AI-powered insights
- Advanced analytics
- Strategy backtesting
- Real-time market data
- Notification system

### Week 4: Launch Preparation (40 hours)
- Payment integration (Stripe)
- User onboarding flow
- Performance testing
- Security audit
- Deployment setup

### Success Metrics
- [ ] All P0 issues resolved
- [ ] Core features functional
- [ ] <3s page load time
- [ ] 0 critical security issues
- [ ] 80%+ test coverage
- [ ] Deployment automated

---

## Appendices

### A. Quick Reference Commands

```bash
# Development
cd ~/Desktop/tradesense
./start_dev.sh  # Starts both frontend and backend

# Backend only
cd src/backend && python main.py

# Frontend only
cd frontend && npm run dev

# Database
psql -U postgres -d tradesense
alembic upgrade head
alembic revision --autogenerate -m "Description"

# Testing
pytest src/backend/tests/ -v
npm test --prefix frontend

# Code quality
black src/backend
isort src/backend
npm run lint --prefix frontend
```

### B. Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://postgres:postgres@localhost/tradesense
JWT_SECRET_KEY=your-generated-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALPHA_VANTAGE_API_KEY=your-api-key
STRIPE_API_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=false
VITE_SENTRY_DSN=your-sentry-dsn
```

### C. Useful SQL Queries

```sql
-- Check user activity
SELECT u.email, COUNT(t.id) as trade_count, 
       SUM(t.pnl) as total_pnl,
       MAX(t.created_at) as last_trade
FROM users u
LEFT JOIN trades t ON u.id = t.user_id
GROUP BY u.id, u.email
ORDER BY total_pnl DESC;

-- Daily P&L summary
SELECT DATE(entry_time) as trade_date,
       COUNT(*) as trade_count,
       SUM(pnl) as daily_pnl,
       AVG(pnl) as avg_pnl
FROM trades
WHERE user_id = 'user-uuid-here'
GROUP BY DATE(entry_time)
ORDER BY trade_date DESC;

-- Strategy performance
SELECT s.name as strategy,
       COUNT(t.id) as trades,
       SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END)::float / COUNT(*) as win_rate,
       SUM(t.pnl) as total_pnl
FROM strategies s
JOIN trades t ON s.id = t.strategy_id
GROUP BY s.id, s.name
ORDER BY total_pnl DESC;
```

### D. Architecture Diagrams

#### Component Communication Flow
```
Frontend                 Backend                  Database
   │                        │                        │
   ├─ Login Request ───────▶│                        │
   │                        ├─ Validate User ───────▶│
   │                        │◀─ User Data ────────────┤
   │                        ├─ Generate JWT          │
   │◀─ JWT Token ───────────┤                        │
   │                        │                        │
   ├─ Get Trades ──────────▶│                        │
   │  (with JWT)            ├─ Verify Token          │
   │                        ├─ Query Trades ────────▶│
   │                        │◀─ Trade Data ───────────┤
   │◀─ Trade List ──────────┤                        │
   │                        │                        │
   └─ Display Dashboard     │                        │
```

#### Deployment Architecture (Future)
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CloudFlare    │────▶│   Load Balancer │────▶│   Nginx Proxy   │
│      (CDN)      │     │    (AWS ALB)    │     │   (Port 80/443) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                              ┌───────────────────────────┴───────────────────────────┐
                              │                                                       │
                    ┌─────────▼─────────┐                                   ┌─────────▼─────────┐
                    │   React App       │                                   │   FastAPI App     │
                    │   (S3 + CloudFront)│                                   │   (ECS Fargate)   │
                    └───────────────────┘                                   └─────────┬─────────┘
                                                                                      │
                                                        ┌─────────────────────────────┼─────────────────────────────┐
                                                        │                             │                             │
                                              ┌─────────▼─────────┐         ┌─────────▼─────────┐       ┌─────────▼─────────┐
                                              │   PostgreSQL      │         │      Redis        │       │    Celery         │
                                              │   (RDS)           │         │   (ElastiCache)   │       │   (ECS)           │
                                              └───────────────────┘         └───────────────────┘       └───────────────────┘
```

---

*This document is a living reference. Update it as the project evolves.*