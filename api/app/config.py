from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # MCP Server
    mcp_server_url: str = "http://mcp:8001"

    # Image Processing
    max_images: int = 5
    min_images: int = 1
    max_image_size_mb: int = 10
    allowed_image_formats: list[str] = ["jpeg", "jpg", "png", "webp", "tiff", "tif"]

    # Observability
    langsmith_api_key: str | None = None
    langsmith_project: str = "vegetarian-menu-analyzer"
    log_level: str = "INFO"

    # Timeouts
    mcp_timeout_seconds: int = 30
    ocr_timeout_seconds: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
