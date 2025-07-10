# TradeSense Architecture

## Quick Navigation
- Frontend UI: `/frontend`
- Backend API: `/src/backend`
- Documentation: `/docs`
- Tests: `/tests`

## Development Workflow
1. API changes go in `/src/backend/api/v1/[feature]`
2. Business logic in `/src/backend/services`
3. Frontend consumes via `/frontend/src/services`

## Key Decisions
- FastAPI for backend (migrated from Streamlit)
- React/Next.js for frontend
- SQLite for development, PostgreSQL for production
