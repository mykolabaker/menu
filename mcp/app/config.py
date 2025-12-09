from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """MCP Server configuration loaded from environment variables."""

    # Server
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    # Ollama LLM
    ollama_base_url: str = "http://ollama:11434"
    llm_model: str = "llama3"

    # Classification
    confidence_threshold: float = 0.7

    # ChromaDB
    chroma_persist_directory: str = "/app/data/chromadb"
    chroma_collection_name: str = "vegetarian_dishes"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # RAG
    rag_top_k: int = 5

    # Observability
    langsmith_api_key: str | None = None
    langsmith_project: str = "vegetarian-menu-analyzer"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
