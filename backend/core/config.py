"""
Core configuration for TradeSense backend
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./tradesense.db"

    # Security
    secret_key: str = "your-secret-key-here"
    jwt_secret: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    jwt_expiration_hours: int = 24
    jwt_algorithm: str = "HS256"

    # API
    api_title: str = "TradeSense API"
    api_version: str = "1.0.0"
    debug: bool = True

    # Market Data APIs
    alpha_vantage_api_key: str = "demo"  # Replace with real API key
    market_data_timeout: int = 10
    market_data_cache_minutes: int = 15

    class Config:
        env_file = ".env"

settings = Settings()