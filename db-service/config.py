from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
from pydantic import Field


class Settings(BaseSettings):
    mongodb_user: str = Field(alias="MONGODB_USER")
    mongodb_password: str = Field(alias="MONGODB_PASSWORD")
    mongodb_host: str = Field(alias="MONGODB_HOST")
    environment: Literal["development", "production", "test"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

    @property
    def mongodb_url(self) -> str:
        if self.environment == "test":
            return f"mongodb://{self.mongodb_user}:{self.mongodb_password}@{self.mongodb_host}/{self.database_name}"
        return f"mongodb+srv://{self.mongodb_user}:{self.mongodb_password}@{self.mongodb_host}/{self.database_name}"

    @property
    def database_name(self) -> str:
        if self.environment == "test":
            return "test_chat_db"
        return "chat_db"

    def get_mongodb_url(self) -> str:
        return f"{self.mongodb_url}?retryWrites=true&w=majority&appName=Tuthoria"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
