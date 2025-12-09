import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


@pytest.fixture
def test_client():
    """Create a test client for the MCP server."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_menu_items():
    """Sample menu items for testing."""
    return [
        {"name": "Greek Salad", "price": 9.99, "description": "Fresh vegetables with feta"},
        {"name": "Grilled Chicken", "price": 15.99, "description": "Herb-marinated chicken"},
        {"name": "Veggie Burger", "price": 12.50, "description": "Plant-based patty"},
        {"name": "Mushroom Risotto", "price": 14.00, "description": None},
    ]


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama chat response."""
    return {
        "message": {
            "content": '{"is_vegetarian": true, "confidence": 0.95, "reasoning": "Contains only vegetables and cheese"}'
        }
    }


@pytest.fixture
def mock_rag_evidence():
    """Mock RAG evidence."""
    from app.models.classification import RAGEvidence
    return [
        RAGEvidence(
            dish_name="Greek Salad",
            is_vegetarian=True,
            similarity_score=0.92,
            description="Fresh vegetables with feta",
        ),
        RAGEvidence(
            dish_name="Caesar Salad",
            is_vegetarian=False,
            similarity_score=0.85,
            description="Contains anchovies",
        ),
    ]
