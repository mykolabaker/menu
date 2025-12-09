import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import get_settings
from .models.tool_input import ClassifyAndCalculateInput
from .models.tool_output import ClassifyAndCalculateOutput, NeedsReviewOutput
from .tools.classify_and_calculate import classify_and_calculate_tool
from .services.rag_service import rag_service


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
    logger.info("Starting MCP server")
    # Initialize RAG knowledge base
    try:
        rag_service.initialize()
    except Exception as e:
        logger.warning("RAG initialization failed, will retry on first use", error=str(e))
    yield
    logger.info("Shutting down MCP server")


# Create FastAPI app
app = FastAPI(
    title="Vegetarian Menu Analyzer MCP Server",
    description="MCP Server for vegetarian dish classification",
    version="1.0.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "mcp"


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.post(
    "/tools/classify_and_calculate",
    response_model=ClassifyAndCalculateOutput | NeedsReviewOutput,
)
async def classify_and_calculate(
    request: Request,
    body: ClassifyAndCalculateInput,
):
    """
    Classify menu items and calculate vegetarian totals.

    This is the main MCP tool endpoint.
    """
    # Get request ID from header or use the one in body
    request_id = request.headers.get("X-Request-ID", body.request_id)

    # Bind request ID to logging context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        result = await classify_and_calculate_tool.execute(body)
        return result
    except Exception as e:
        logger.exception("Classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Tool schema endpoint for MCP protocol compatibility
@app.get("/tools")
async def list_tools():
    """List available tools (MCP protocol)."""
    return {
        "tools": [
            {
                "name": "classify_and_calculate",
                "description": "Classify menu items as vegetarian/non-vegetarian and calculate total sum",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "menu_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "number"},
                                    "description": {"type": "string"},
                                },
                                "required": ["name", "price"],
                            },
                        },
                        "request_id": {"type": "string"},
                    },
                    "required": ["menu_items", "request_id"],
                },
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.mcp_host,
        port=settings.mcp_port,
        reload=True,
    )
