from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    port: int = Field(default=8501, alias="PORT")
    db_service_port: int = Field(default=8000, alias="DB_SERVICE_PORT")
    openai_service_port: int = Field(default=8502, alias="OPENAI_SERVICE_PORT")
    db_service_domain: str = Field(default="db-service", alias="DB_SERVICE_DOMAIN")
    openai_service_domain: str = Field(
        default="openai-service", alias="OPENAI_SERVICE_DOMAIN"
    )
    db_service_protocol: str = Field(default="http", alias="DB_SERVICE_PROTOCOL")
    openai_service_protocol: str = Field(
        default="http", alias="OPENAI_SERVICE_PROTOCOL"
    )
    whatsapp_verify_token: str = Field(default="", alias="WHATSAPP_VERIFY_TOKEN")
    whatsapp_access_token: str = Field(default="", alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_api_version: str = Field(default="v17.0", alias="WHATSAPP_API_VERSION")
    whatsapp_number_id: str = Field(default="", alias="WHATSAPP_NUMBER_ID")
    environment: Literal["development", "production", "test"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    host: str = Field(default="0.0.0.0", alias="HOST")
    mongodb_user: str = Field(default="", alias="MONGODB_USER")
    mongodb_password: str = Field(default="", alias="MONGODB_PASSWORD")
    mongodb_host: str = Field(default="", alias="MONGODB_HOST")

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False
        extra = "allow"

    def get_whatsapp_api_url(self) -> str:
        return f"https://graph.facebook.com/{self.whatsapp_api_version}/{self.whatsapp_number_id}/messages"

    def build_service_url(self, service: str, path: str = "") -> str:
        if service == "db":
            protocol = self.db_service_protocol
            domain = self.db_service_domain
            port = self.db_service_port
        elif service == "openai":
            protocol = self.openai_service_protocol
            domain = self.openai_service_domain
            port = self.openai_service_port
        else:
            raise ValueError(f"Unknown service: {service}")

        # In production (Railway), we don't include the port in the URL
        if self.environment == "production":
            # For HTTPS, we don't need to specify port 443 as it's the default
            return f"{protocol}://{domain}{path}"

        # In development, we use the specified ports
        if protocol == "https" and port == 443:
            return f"{protocol}://{domain}{path}"
        return f"{protocol}://{domain}:{port}{path}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
