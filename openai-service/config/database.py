from typing import Optional
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseSettings(BaseSettings):
    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # DB Service settings
    DB_SERVICE_URL: str = "http://db-service:8000/api/v1"

    class Config:
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development').lower()}"
        case_sensitive = True


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
