import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db.session import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///tradesense.db"

# Ensure the database directory exists
db_dir = os.path.dirname(os.path.abspath("tradesense.db"))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)