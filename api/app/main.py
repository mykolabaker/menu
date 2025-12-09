import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .middleware.request_id import RequestIDMiddleware
from .routers import menu, review
from .services.mcp_client import mcp_client
from .utils.exceptions import MenuAnalyzerError


# Configure structured logging
def configure_logging():
    settings = get_settings()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting API service")
    yield
    logger.info("Shutting down API service")
    await mcp_client.close()


# Create FastAPI app
app = FastAPI(
    title="Vegetarian Menu Analyzer API",
    description="API for processing restaurant menu photos and identifying vegetarian dishes",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestIDMiddleware)


# Exception handlers
@app.exception_handler(MenuAnalyzerError)
async def menu_analyzer_error_handler(request: Request, exc: MenuAnalyzerError):
    """Handle custom application errors."""
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.exception("Unexpected error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# Include routers
app.include_router(menu.router, tags=["Menu"])
app.include_router(review.router, tags=["Review"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and orchestration."""
    return {
        "status": "healthy",
        "service": "api",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
