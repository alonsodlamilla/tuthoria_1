from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Environment settings
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    PORT: int = 8502
    DEBUG: bool = False

    # OpenAI settings
    OPENAI_API_KEY: str

    # Database settings
    DB_SERVICE_URL: str = "http://db-service:8000/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
