"""Environment driven settings for the mcp service."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    log_level: str = Field("INFO", alias="MCP_LOG_LEVEL")
    backend_base_url: str = Field("http://localhost:8000", alias="BACKEND_BASE_URL")
    ml_base_url: str = Field("http://localhost:8001", alias="ML_BASE_URL")
    http_timeout_seconds: float = Field(10.0, alias="HTTP_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
