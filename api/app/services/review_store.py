import structlog
from typing import Any
from threading import Lock

logger = structlog.get_logger()


class ReviewStore:
    """
    In-memory store for HITL review requests.

    Stores MCP results keyed by request_id for later correction.
    """

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def store(self, request_id: str, mcp_result: dict[str, Any]) -> None:
        """Store MCP result for later review."""
        with self._lock:
            self._store[request_id] = mcp_result
            logger.debug("review_stored", request_id=request_id)

    def get(self, request_id: str) -> dict[str, Any] | None:
        """Get stored MCP result by request_id."""
        with self._lock:
            return self._store.get(request_id)

    def delete(self, request_id: str) -> bool:
        """Delete stored result after review."""
        with self._lock:
            if request_id in self._store:
                del self._store[request_id]
                logger.debug("review_deleted", request_id=request_id)
                return True
            return False

    def exists(self, request_id: str) -> bool:
        """Check if request_id exists in store."""
        with self._lock:
            return request_id in self._store


# Singleton instance
review_store = ReviewStore()
