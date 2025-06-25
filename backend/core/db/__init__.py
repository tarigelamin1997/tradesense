# Database module

# Database initialization
from backend.core.db.session import engine, Base

# Import models to register them
from backend.models.trade import Trade
from backend.models.user import User

# Create tables
Base.metadata.create_all(bind=engine)