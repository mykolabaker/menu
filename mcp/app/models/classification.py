from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Result of classifying a single dish."""

    is_vegetarian: bool
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    method: str  # "llm", "keyword", "rag", "combined"


class RAGEvidence(BaseModel):
    """Evidence retrieved from RAG system."""

    dish_name: str
    is_vegetarian: bool
    similarity_score: float
    description: str | None = None


class LLMClassificationResponse(BaseModel):
    """Expected response format from LLM."""

    is_vegetarian: bool
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str


class KeywordClassificationResult(BaseModel):
    """Result from keyword-based classification."""

    is_vegetarian: bool | None  # None if uncertain
    confidence: float
    matched_keywords: list[str] = Field(default_factory=list)
