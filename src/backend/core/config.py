"""
Core configuration for TradeSense backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/tradesense")
    test_database_url: Optional[str] = None
    sqlite_database_url: Optional[str] = "sqlite:///./tradesense.db"  # Keep SQLite as fallback
    
    # Security
    secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", "")  # Legacy field
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30  # Legacy field
    jwt_access_token_expire_minutes: int = 30
    jwt_expiration_hours: int = 24

    # Environment
    environment: str = "development"
    
    # API
    api_title: str = "TradeSense API"
    api_version: str = "1.0.0"
    api_v1_str: str = "/api/v1"
    project_name: str = "TradeSense API"
    debug: bool = True
    
    # CORS - We'll handle parsing in main.py to avoid pydantic parsing issues
    cors_origins_str: str = "http://localhost:8000,http://localhost:3001,http://localhost:5173"
    
    # Frontend
    vite_api_base_url: Optional[str] = None

    # Market Data APIs
    alpha_vantage_api_key: str = "demo"  # Replace with real API key
    market_data_timeout: int = 10
    market_data_cache_minutes: int = 15

    # File Upload Settings
    allowed_file_extensions: list = [".csv", ".xlsx", ".xls"]
    max_file_size: int = 10 * 1024 * 1024  # 10MB in bytes
    
    # Email
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Redis
    redis_url: Optional[str] = None
    
    # Stripe
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "extra": "allow"  # Allow extra fields for flexibility
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable must be set!")

settings = Settings()