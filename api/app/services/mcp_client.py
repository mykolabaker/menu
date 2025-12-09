import time
import httpx
import structlog

from ..config import get_settings
from ..models.menu_item import MenuItem
from ..utils.exceptions import MCPError, MCPUnavailableError

logger = structlog.get_logger()


class MCPClient:
    """HTTP client for communicating with the MCP server."""

    def __init__(self):
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.mcp_server_url,
                timeout=httpx.Timeout(self.settings.mcp_timeout_seconds),
            )
        return self._client

    async def classify_and_calculate(
        self,
        menu_items: list[MenuItem],
        request_id: str,
    ) -> dict:
        """
        Call the MCP server's classify_and_calculate tool.

        Args:
            menu_items: List of menu items to classify
            request_id: Request ID for tracing

        Returns:
            Classification results from MCP server

        Raises:
            MCPUnavailableError: If MCP server is unreachable
            MCPError: If MCP server returns an error
        """
        log = logger.bind(request_id=request_id)
        log.info("mcp_call_started", tool_name="classify_and_calculate")

        start_time = time.time()

        # Prepare request payload
        payload = {
            "menu_items": [
                {
                    "name": item.name,
                    "price": item.price,
                    "description": item.description,
                }
                for item in menu_items
            ],
            "request_id": request_id,
        }

        try:
            response = await self.client.post(
                "/tools/classify_and_calculate",
                json=payload,
                headers={"X-Request-ID": request_id},
            )

            duration_ms = int((time.time() - start_time) * 1000)
            log.info("mcp_call_completed", duration_ms=duration_ms)

            if response.status_code != 200:
                log.error(
                    "mcp_call_error",
                    status_code=response.status_code,
                    response=response.text[:500],
                )
                raise MCPError(
                    message="MCP server error",
                    detail=f"Status {response.status_code}: {response.text[:200]}",
                )

            return response.json()

        except httpx.ConnectError as e:
            log.error("mcp_unavailable", error=str(e))
            raise MCPUnavailableError(
                message="MCP server unavailable",
                detail="Unable to connect to the classification service",
            )
        except httpx.TimeoutException as e:
            log.error("mcp_timeout", error=str(e))
            raise MCPError(
                message="MCP server timeout",
                detail="Classification service took too long to respond",
            )

    async def health_check(self) -> bool:
        """Check if MCP server is healthy."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
mcp_client = MCPClient()
