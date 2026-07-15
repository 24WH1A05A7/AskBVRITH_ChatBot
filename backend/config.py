"""Backend configuration module."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    # Security
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Database
    DATABASE_URL: str = "sqlite:///./data/observability.db"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Caching
    CACHE_TTL_SECONDS: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
