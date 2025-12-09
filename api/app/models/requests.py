from pydantic import BaseModel, Field


class ProcessMenuBase64Request(BaseModel):
    """Request body for base64-encoded images."""

    images: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of base64-encoded images (1-5)",
    )


class ReviewCorrectionItem(BaseModel):
    """Single correction item for HITL review."""

    name: str = Field(..., description="Name of the dish to correct")
    is_vegetarian: bool = Field(..., description="Corrected vegetarian classification")


class ReviewRequest(BaseModel):
    """Request body for HITL review corrections."""

    request_id: str = Field(..., description="Original request ID")
    corrections: list[ReviewCorrectionItem] = Field(
        ..., min_length=1, description="List of corrections"
    )
