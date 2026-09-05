"""Environment driven settings for the agentic service."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    log_level: str = Field("INFO", alias="AGENTIC_LOG_LEVEL")
    # every data access goes through mcp, never straight to backend or ml
    mcp_base_url: str = Field("http://localhost:8002", alias="MCP_BASE_URL")
    http_timeout_seconds: float = Field(15.0, alias="HTTP_TIMEOUT_SECONDS")
    max_tool_calls: int = Field(5, alias="MAX_TOOL_CALLS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
