"""
Application Configuration
Loads settings from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Blend Optimizer API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://optimizer:password@localhost:5432/blend_optimizer"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-here-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".csv"]

    # Optimizer Settings
    MAX_COMBINATIONS: int = 25000
    MAX_LOTS_PER_BLEND: int = 10
    DC_TOLERANCE: float = 3.0
    FP_TOLERANCE: float = 5.0
    DUCK_TOLERANCE: float = 5.0
    INITIAL_DC_RANGE: float = 15.0  # Range iniziale per ricerca candidati (±15%)

    # Paths
    EXCEL_OUTPUT_PATH: str = "/app/exports"
    OPTIMIZER_CORE_PATH: str = "/app/optimizer_core"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
