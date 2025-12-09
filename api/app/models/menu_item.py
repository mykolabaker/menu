from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    """Represents a single menu item extracted from OCR."""

    name: str = Field(..., description="Name of the dish")
    price: float = Field(..., ge=0, description="Price of the dish")
    description: str | None = Field(None, description="Optional description")
    category: str | None = Field(None, description="Menu section/category")

    def normalized_name(self) -> str:
        """Return normalized name for deduplication."""
        return self.name.lower().strip()


class ClassifiedMenuItem(BaseModel):
    """Menu item with vegetarian classification."""

    name: str
    price: float
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str | None = None
    is_vegetarian: bool


class VegetarianItem(BaseModel):
    """Vegetarian item for API response."""

    name: str
    price: float
