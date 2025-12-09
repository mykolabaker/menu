import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


class TestClassifyAndCalculateTool:
    @patch("app.tools.classify_and_calculate.llm_classifier")
    @patch("app.tools.classify_and_calculate.rag_service")
    def test_classify_vegetarian_items(self, mock_rag, mock_llm, client):
        """Test classification of vegetarian items."""
        # Mock RAG service
        mock_rag.search.return_value = []

        # Mock LLM classifier
        from app.models.classification import LLMClassificationResponse
        mock_llm.classify.return_value = LLMClassificationResponse(
            is_vegetarian=True,
            confidence=0.95,
            reasoning="Contains only vegetables",
        )

        response = client.post(
            "/tools/classify_and_calculate",
            json={
                "menu_items": [
                    {"name": "Greek Salad", "price": 9.99},
                ],
                "request_id": "test-123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "vegetarian_items" in data
        assert len(data["vegetarian_items"]) == 1
        assert data["total_sum"] == 9.99

    @patch("app.tools.classify_and_calculate.llm_classifier")
    @patch("app.tools.classify_and_calculate.rag_service")
    def test_classify_non_vegetarian_items(self, mock_rag, mock_llm, client):
        """Test classification excludes non-vegetarian items."""
        mock_rag.search.return_value = []

        from app.models.classification import LLMClassificationResponse
        mock_llm.classify.return_value = LLMClassificationResponse(
            is_vegetarian=False,
            confidence=0.92,
            reasoning="Contains chicken",
        )

        response = client.post(
            "/tools/classify_and_calculate",
            json={
                "menu_items": [
                    {"name": "Grilled Chicken", "price": 15.99},
                ],
                "request_id": "test-123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data.get("vegetarian_items", [])) == 0
        assert data["total_sum"] == 0.0

    @patch("app.tools.classify_and_calculate.llm_classifier")
    @patch("app.tools.classify_and_calculate.rag_service")
    def test_classify_uncertain_items(self, mock_rag, mock_llm, client):
        """Test uncertain items trigger needs_review."""
        mock_rag.search.return_value = []

        from app.models.classification import LLMClassificationResponse
        mock_llm.classify.return_value = LLMClassificationResponse(
            is_vegetarian=True,
            confidence=0.55,  # Below threshold
            reasoning="May contain chicken stock",
        )

        response = client.post(
            "/tools/classify_and_calculate",
            json={
                "menu_items": [
                    {"name": "Mushroom Risotto", "price": 14.00},
                ],
                "request_id": "test-123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "needs_review"
        assert len(data.get("uncertain_items", [])) == 1

    @patch("app.tools.classify_and_calculate.llm_classifier")
    @patch("app.tools.classify_and_calculate.rag_service")
    def test_keyword_fallback(self, mock_rag, mock_llm, client):
        """Test keyword fallback when LLM fails."""
        mock_rag.search.return_value = []
        mock_llm.classify.return_value = None  # LLM failure

        response = client.post(
            "/tools/classify_and_calculate",
            json={
                "menu_items": [
                    {"name": "Grilled Chicken Breast", "price": 15.99},
                ],
                "request_id": "test-123",
            },
        )

        assert response.status_code == 200
        # Keyword classifier should identify "chicken" as non-vegetarian
        data = response.json()
        assert len(data.get("vegetarian_items", [])) == 0


class TestHealthEndpoint:
    def test_health_check(self, client):
        """Test MCP server health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mcp"


class TestToolsEndpoint:
    def test_list_tools(self, client):
        """Test tool listing endpoint."""
        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "classify_and_calculate"
