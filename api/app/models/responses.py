from pydantic import BaseModel, Field
from .menu_item import VegetarianItem


class ProcessMenuResponse(BaseModel):
    """Successful response for menu processing."""

    vegetarian_items: list[VegetarianItem] = Field(
        default_factory=list, description="List of identified vegetarian dishes"
    )
    total_sum: float = Field(..., ge=0, description="Sum of all vegetarian dish prices")


class UncertainItem(BaseModel):
    """Item that needs human review."""

    name: str
    price: float
    confidence: float = Field(..., ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class ConfidentItem(BaseModel):
    """Item with high confidence classification."""

    name: str
    price: float
    confidence: float = Field(..., ge=0, le=1)


class NeedsReviewResponse(BaseModel):
    """Response when items need human review (HITL)."""

    status: str = "needs_review"
    request_id: str
    confident_items: list[ConfidentItem] = Field(default_factory=list)
    uncertain_items: list[UncertainItem] = Field(default_factory=list)
    partial_sum: float = Field(..., ge=0)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "api"


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: str
    detail: str | None = None
    request_id: str | None = None
