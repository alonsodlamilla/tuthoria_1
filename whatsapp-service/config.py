from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    port: int = Field(alias="PORT")
    db_service_port: int = Field(alias="DB_SERVICE_PORT")
    openai_service_port: int = Field(alias="OPENAI_SERVICE_PORT")
    db_service_domain: str = Field(alias="DB_SERVICE_DOMAIN")
    openai_service_domain: str = Field(alias="OPENAI_SERVICE_DOMAIN")
    db_service_protocol: str = Field(alias="DB_SERVICE_PROTOCOL")
    openai_service_protocol: str = Field(alias="OPENAI_SERVICE_PROTOCOL")
    whatsapp_verify_token: str = Field(alias="WHATSAPP_VERIFY_TOKEN")
    whatsapp_access_token: str = Field(alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_api_version: str = Field(alias="WHATSAPP_API_VERSION")
    whatsapp_number_id: str = Field(alias="WHATSAPP_NUMBER_ID")
    environment: Literal["development", "production", "test"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    host: str = Field(default="0.0.0.0", alias="HOST")

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

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

        return f"{protocol}://{domain}:{port}{path}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
