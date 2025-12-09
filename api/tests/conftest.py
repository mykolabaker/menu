import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
import io
from PIL import Image


@pytest.fixture
def test_client():
    """Create a test client for the API."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Create a sample image for testing."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_image():
    """Create a sample PIL Image for testing."""
    return Image.new("RGB", (100, 100), color="white")


@pytest.fixture
def mock_mcp_response():
    """Mock successful MCP response."""
    return {
        "vegetarian_items": [
            {"name": "Greek Salad", "price": 9.99, "confidence": 0.95, "reasoning": "Contains vegetables and feta"},
            {"name": "Veggie Burger", "price": 12.50, "confidence": 0.88, "reasoning": "Plant-based patty"},
        ],
        "total_sum": 22.49,
        "classification_method": "llm+rag",
        "request_id": "test-request-id",
    }


@pytest.fixture
def mock_needs_review_response():
    """Mock needs_review MCP response."""
    return {
        "status": "needs_review",
        "request_id": "test-request-id",
        "confident_items": [
            {"name": "Greek Salad", "price": 9.99, "confidence": 0.95},
        ],
        "uncertain_items": [
            {"name": "Mushroom Risotto", "price": 14.00, "confidence": 0.55, "evidence": ["May contain chicken stock"]},
        ],
        "partial_sum": 9.99,
        "classification_method": "llm+rag",
    }


@pytest.fixture
def sample_ocr_text():
    """Sample OCR text output."""
    return """
    APPETIZERS
    Greek Salad $9.99
    Garden Salad $7.50

    MAIN COURSES
    Grilled Chicken $15.99
    Veggie Burger $12.50
    Mushroom Risotto $14.00
    """
