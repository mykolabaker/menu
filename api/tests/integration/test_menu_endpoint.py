import pytest
import io
import base64
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Create a sample JPEG image."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


class TestProcessMenuEndpoint:
    @patch("app.routers.menu.ocr_service")
    @patch("app.routers.menu.mcp_client")
    def test_process_menu_success(self, mock_mcp, mock_ocr, client, sample_image_bytes):
        """Test successful menu processing."""
        # Mock OCR to return menu text
        mock_ocr.extract_text_batch.return_value = ["Greek Salad $9.99\nVeggie Burger $12.50"]

        # Mock MCP response
        mock_mcp.classify_and_calculate = AsyncMock(return_value={
            "vegetarian_items": [
                {"name": "Greek Salad", "price": 9.99},
                {"name": "Veggie Burger", "price": 12.50},
            ],
            "total_sum": 22.49,
        })

        # Send request
        response = client.post(
            "/process-menu",
            files=[("images", ("menu.jpg", sample_image_bytes, "image/jpeg"))],
        )

        assert response.status_code == 200
        data = response.json()
        assert "vegetarian_items" in data
        assert "total_sum" in data
        assert data["total_sum"] == 22.49

    @patch("app.routers.menu.ocr_service")
    @patch("app.routers.menu.mcp_client")
    def test_process_menu_base64(self, mock_mcp, mock_ocr, client, sample_image_bytes):
        """Test processing with base64 encoded images."""
        b64_image = base64.b64encode(sample_image_bytes).decode()

        mock_ocr.extract_text_batch.return_value = ["Pasta $10.00"]
        mock_mcp.classify_and_calculate = AsyncMock(return_value={
            "vegetarian_items": [{"name": "Pasta", "price": 10.00}],
            "total_sum": 10.00,
        })

        response = client.post(
            "/process-menu",
            json={"images": [b64_image]},
        )

        assert response.status_code == 200

    def test_process_menu_no_images(self, client):
        """Test error when no images provided."""
        response = client.post("/process-menu", json={"images": []})
        assert response.status_code == 400

    def test_process_menu_too_many_images(self, client, sample_image_bytes):
        """Test error when too many images provided."""
        files = [("images", (f"menu{i}.jpg", sample_image_bytes, "image/jpeg")) for i in range(6)]
        response = client.post("/process-menu", files=files)
        assert response.status_code == 400

    @patch("app.routers.menu.ocr_service")
    @patch("app.routers.menu.mcp_client")
    def test_process_menu_needs_review(self, mock_mcp, mock_ocr, client, sample_image_bytes):
        """Test needs_review response handling."""
        mock_ocr.extract_text_batch.return_value = ["Mushroom Risotto $14.00"]
        mock_mcp.classify_and_calculate = AsyncMock(return_value={
            "status": "needs_review",
            "request_id": "test-id",
            "confident_items": [],
            "uncertain_items": [
                {"name": "Mushroom Risotto", "price": 14.00, "confidence": 0.55, "evidence": ["May contain chicken stock"]}
            ],
            "partial_sum": 0.0,
        })

        response = client.post(
            "/process-menu",
            files=[("images", ("menu.jpg", sample_image_bytes, "image/jpeg"))],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_review"
        assert "uncertain_items" in data

    @patch("app.routers.menu.ocr_service")
    def test_process_menu_ocr_failure(self, mock_ocr, client, sample_image_bytes):
        """Test OCR failure returns 422."""
        mock_ocr.extract_text_batch.return_value = [""]  # Empty OCR result

        response = client.post(
            "/process-menu",
            files=[("images", ("menu.jpg", sample_image_bytes, "image/jpeg"))],
        )

        assert response.status_code == 422


class TestHealthEndpoint:
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api"
