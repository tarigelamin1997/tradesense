
"""
Database session management
"""
from typing import Generator
from sqlalchemy.orm import Session
from backend.db.connection import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    FastAPI will use this as a dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
