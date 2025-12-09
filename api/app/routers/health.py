from fastapi import APIRouter
import structlog

from ..models.responses import HealthResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic health status of the API service.
    """
    return HealthResponse(status="healthy", service="api")
