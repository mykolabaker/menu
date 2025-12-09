from pydantic import BaseModel, Field


class ClassifiedItemOutput(BaseModel):
    """A classified menu item in the output."""

    name: str
    price: float
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str | None = None
    is_vegetarian: bool


class VegetarianItemOutput(BaseModel):
    """Vegetarian item in final output."""

    name: str
    price: float
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str | None = None


class UncertainItemOutput(BaseModel):
    """Uncertain item that needs review."""

    name: str
    price: float
    confidence: float = Field(..., ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class ClassifyAndCalculateOutput(BaseModel):
    """Output schema for classify_and_calculate tool - final result."""

    vegetarian_items: list[VegetarianItemOutput] = Field(default_factory=list)
    total_sum: float = Field(..., ge=0)
    classification_method: str = Field(default="llm+rag+keywords")
    request_id: str


class NeedsReviewOutput(BaseModel):
    """Output when items need human review."""

    status: str = "needs_review"
    request_id: str
    confident_items: list[VegetarianItemOutput] = Field(default_factory=list)
    uncertain_items: list[UncertainItemOutput] = Field(default_factory=list)
    partial_sum: float = Field(..., ge=0)
    classification_method: str = Field(default="llm+rag+keywords")
