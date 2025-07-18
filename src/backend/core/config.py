"""
Core configuration for TradeSense backend
"""
import os
import secrets
from pydantic_settings import BaseSettings
from typing import Optional, List

# Helper function to construct database URL
def get_database_url():
    """
    Get database URL with proper handling for Railway's postgres:// format
    """
    # First check for explicit DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url
    
    # Check for Railway's DATABASE_PRIVATE_URL
    private_url = os.getenv("DATABASE_PRIVATE_URL")
    if private_url:
        if private_url.startswith("postgres://"):
            private_url = private_url.replace("postgres://", "postgresql://", 1)
        return private_url
    
    # Check for Railway's POSTGRES_* variables (new format)
    if os.getenv("POSTGRES_HOST"):
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DATABASE", "railway")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    # Construct from individual PG variables (Railway style)
    if os.getenv("PGHOST"):
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "postgres")
        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        database = os.getenv("PGDATABASE", "railway")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    # In production, we should not have a default
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("DATABASE_URL must be set in production!")
    
    # Default local database for development only
    return "postgresql://postgres:postgres@localhost/tradesense"

class Settings(BaseSettings):
    # Database
    database_url: str = get_database_url()
    test_database_url: Optional[str] = None
    sqlite_database_url: Optional[str] = "sqlite:///./tradesense.db"  # Keep SQLite as fallback
    
    # Security - Generate defaults if not provided
    secret_key: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))  # Legacy field
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30  # Legacy field
    jwt_access_token_expire_minutes: int = 30
    jwt_expiration_hours: int = 24

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # API
    api_title: str = "TradeSense API"
    api_version: str = "2.0.0"
    api_v1_str: str = "/api/v1"
    project_name: str = "TradeSense API"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS - We'll handle parsing in main.py to avoid pydantic parsing issues
    cors_origins_str: str = os.getenv("CORS_ORIGINS_STR", "http://localhost:8000,http://localhost:3001,http://localhost:5173")
    
    # Frontend
    vite_api_base_url: Optional[str] = None

    # Market Data APIs
    alpha_vantage_api_key: str = "demo"  # Replace with real API key
    market_data_timeout: int = 10
    market_data_cache_minutes: int = 15

    # File Upload Settings
    allowed_file_extensions: list = [".csv", ".xlsx", ".xls"]
    max_file_size: int = 10 * 1024 * 1024  # 10MB in bytes
    
    # Reports Directory
    reports_directory: str = "reports"
    
    # Email
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Redis
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    
    # Stripe
    stripe_api_key: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    model_config = {
        "env_file": ".env",
        "extra": "allow"  # Allow extra fields for flexibility
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Don't require JWT_SECRET_KEY in production - we generate one if needed
        if self.environment == "production" and not self.database_url:
            raise ValueError("DATABASE_URL must be set in production!")

settings = Settings()