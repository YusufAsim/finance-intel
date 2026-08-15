"""Environment driven settings for the ml service."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    log_level: str = Field("INFO", alias="ML_LOG_LEVEL")
    # upstream backend used to pull training data, never a database
    backend_base_url: str = Field("http://localhost:8000", alias="BACKEND_BASE_URL")
    backend_timeout_seconds: float = Field(10.0, alias="BACKEND_TIMEOUT_SECONDS")
    artifacts_dir: Path = Field(Path("artifacts"), alias="ARTIFACTS_DIR")


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached for the process lifetime."""
    return Settings()
