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

    # MongoDB settings
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_HOST: str
    MONGO_PORT: Optional[int] = None
    MONGO_DB_NAME: str = "openai_service"
    MONGO_ATLAS_CLUSTER: Optional[str] = None

    @property
    def mongodb_uri(self) -> str:
        """Get MongoDB URI based on environment"""
        if self.ENVIRONMENT == Environment.DEVELOPMENT:
            return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}"
        else:
            # Atlas connection string
            return f"mongodb+srv://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_ATLAS_CLUSTER}"

    class Config:
        env_file = ".env"


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
