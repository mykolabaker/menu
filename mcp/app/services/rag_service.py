import json
import time
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
import structlog

from ..config import get_settings
from ..models.classification import RAGEvidence
from .embeddings import embedding_service

logger = structlog.get_logger()


class RAGService:
    """RAG service using ChromaDB for semantic search."""

    def __init__(self):
        self.settings = get_settings()
        self._client: chromadb.Client | None = None
        self._collection = None
        self._initialized = False

    @property
    def client(self) -> chromadb.Client:
        """Lazy load ChromaDB client."""
        if self._client is None:
            logger.info(
                "Initializing ChromaDB",
                persist_directory=self.settings.chroma_persist_directory,
            )
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.settings.chroma_collection_name,
                metadata={"description": "Vegetarian dish classification knowledge base"},
            )
        return self._collection

    def initialize(self) -> None:
        """Initialize the knowledge base with seed data if empty."""
        if self._initialized:
            return

        # Check if collection has data
        count = self.collection.count()
        if count > 0:
            logger.info("Knowledge base already populated", count=count)
            self._initialized = True
            return

        # Load and seed data
        self._seed_knowledge_base()
        self._initialized = True

    def _seed_knowledge_base(self) -> None:
        """Seed the knowledge base from JSON file."""
        logger.info("Seeding knowledge base")

        # Find the JSON file
        current_dir = Path(__file__).parent.parent
        json_path = current_dir / "knowledge_base" / "vegetarian_dishes.json"

        if not json_path.exists():
            logger.warning("Knowledge base JSON not found", path=str(json_path))
            return

        with open(json_path) as f:
            data = json.load(f)

        dishes = data.get("dishes", [])
        if not dishes:
            logger.warning("No dishes found in knowledge base JSON")
            return

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for i, dish in enumerate(dishes):
            dish_id = f"dish_{i}"
            # Combine name and description for better semantic search
            doc_text = dish["name"]
            if dish.get("description"):
                doc_text += f" - {dish['description']}"

            ids.append(dish_id)
            documents.append(doc_text)
            metadatas.append({
                "name": dish["name"],
                "is_vegetarian": dish["is_vegetarian"],
                "description": dish.get("description", ""),
            })

        # Generate embeddings
        embeddings = embedding_service.embed_batch(documents)

        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Knowledge base seeded", count=len(dishes))

    def search(
        self,
        query: str,
        top_k: int | None = None,
        request_id: str = "",
    ) -> list[RAGEvidence]:
        """
        Search for similar dishes in the knowledge base.

        Args:
            query: Dish name or description to search for
            top_k: Number of results to return
            request_id: Request ID for logging

        Returns:
            List of RAGEvidence objects
        """
        log = logger.bind(request_id=request_id, query=query)

        # Ensure initialized
        self.initialize()

        if top_k is None:
            top_k = self.settings.rag_top_k

        start_time = time.time()

        # Generate embedding for query
        query_embedding = embedding_service.embed(query)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Convert to RAGEvidence objects
        evidence_list = []
        if results["metadatas"] and results["distances"]:
            for metadata, distance in zip(
                results["metadatas"][0], results["distances"][0]
            ):
                # ChromaDB returns L2 distance, convert to similarity score
                # Lower distance = higher similarity
                similarity = 1 / (1 + distance)

                evidence_list.append(
                    RAGEvidence(
                        dish_name=metadata["name"],
                        is_vegetarian=metadata["is_vegetarian"],
                        similarity_score=round(similarity, 3),
                        description=metadata.get("description"),
                    )
                )

        log.info(
            "rag_retrieval",
            hits_count=len(evidence_list),
            duration_ms=duration_ms,
        )

        return evidence_list


# Singleton instance
rag_service = RAGService()
