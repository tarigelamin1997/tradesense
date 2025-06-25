
"""
Centralized configuration management for TradeSense backend
"""
import os
from typing import List
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    # Application settings
    app_name: str = "TradeSense API"
    version: str = "2.0.0"
    description: str = "Advanced Trading Analytics Platform API"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./backend/tradesense.db"
    
    # Security
    jwt_secret: str = "tradesense_jwt_secret_key_2024"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 720  # 30 days
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://0.0.0.0:3000",
        "https://*.replit.dev",
        "https://*.replit.app"
    ]
    
    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_extensions: List[str] = [".csv", ".xlsx", ".xls"]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/tradesense.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator('allowed_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


settings = Settings()
