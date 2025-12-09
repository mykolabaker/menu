import structlog
from sentence_transformers import SentenceTransformer

from ..config import get_settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(self):
        self.settings = get_settings()
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info("Loading embedding model", model=self.settings.embedding_model)
            self._model = SentenceTransformer(self.settings.embedding_model)
            logger.info("Embedding model loaded")
        return self._model

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


# Singleton instance
embedding_service = EmbeddingService()
