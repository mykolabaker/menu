from pydantic import BaseModel, Field


class MenuItemInput(BaseModel):
    """Input menu item for classification."""

    name: str = Field(..., description="Name of the dish")
    price: float = Field(..., ge=0, description="Price of the dish")
    description: str | None = Field(None, description="Optional description")


class ClassifyAndCalculateInput(BaseModel):
    """Input schema for classify_and_calculate tool."""

    menu_items: list[MenuItemInput] = Field(
        ..., min_length=1, description="List of menu items to classify"
    )
    request_id: str = Field(..., description="Request ID for tracing")
