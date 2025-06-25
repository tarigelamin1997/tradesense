"""
Application configuration settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    # App settings
    app_name: str = "TradeSense API"
    version: str = "1.0.0"
    debug: bool = False

    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Database
    database_url: str = "sqlite:///./tradesense.db"

    # API
    api_prefix: str = "/api"
    allowed_origins: list = ["http://localhost:3000", "http://0.0.0.0:3000", "http://127.0.0.1:3000"]

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/tradesense.log"

    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".csv", ".xlsx", ".xls"]

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()