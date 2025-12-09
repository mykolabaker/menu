from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration."""

    # MCP Server
    mcp_server_url: str = "http://mcp:8001"
    mcp_timeout_seconds: float = 300.0

    # Image Processing
    max_images: int = 5
    min_images: int = 1

    # Observability
    langsmith_api_key: str | None = None
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
