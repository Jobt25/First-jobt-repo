# ============================================
# app/config.py - Configuration Settings
# ============================================
"""
Application Configuration
Loads environment variables and provides settings for the entire application.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Jobt AI Career Coach"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8000

    # Security
    SECRET_KEY: str  # Generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour

    # Database
    DATABASE_URL: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    OPENAI_BASE_URL: str
    OPENAI_MAX_TOKENS: int = 1000
    MAX_SESSION_DURATION: int = 1800
    MAX_TOKENS_PER_SESSION: int = 4000

    # Email (for password reset)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None

    # Rate Limiting
    FREE_TIER_MONTHLY_LIMIT: int = 5
    DAILY_SESSION_LIMIT: int = 10
    MAX_SESSION_DURATION: int = 1800  # 30 minutes in seconds

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
