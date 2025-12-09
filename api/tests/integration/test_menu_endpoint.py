import pytest
import io
import base64
from unittest.mock import patch, AsyncMock, MagicMock
from PIL import Image
from fastapi.testclient import TestClient


@pytest.fixture
def sample_image_bytes():
    """Create a sample JPEG image."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def client():
    """Get test client."""
    from app.main import app
    return TestClient(app)


class TestProcessMenuEndpoint:
    def test_process_menu_success(self, sample_image_bytes):
        """Test successful menu processing with confidence and reasoning."""
        # Create mocks before importing app
        mock_ocr = MagicMock()
        mock_ocr.extract_text_batch.return_value = ["Greek Salad $9.99\nVeggie Burger $12.50"]

        mock_mcp = MagicMock()
        mock_mcp.classify_and_calculate = AsyncMock(return_value={
            "vegetarian_items": [
                {"name": "Greek Salad", "price": 9.99, "confidence": 0.95, "reasoning": "Contains vegetables and feta cheese"},
                {"name": "Veggie Burger", "price": 12.50, "confidence": 0.92, "reasoning": "Plant-based burger patty"},
            ],
            "total_sum": 22.49,
        })

        # Patch at the point of use (the router module)
        import app.routers.menu as menu_module
        original_ocr = menu_module.ocr_service
        original_mcp = menu_module.mcp_client

        try:
            menu_module.ocr_service = mock_ocr
            menu_module.mcp_client = mock_mcp

            from app.main import app
            client = TestClient(app)

            response = client.post(
                "/process-menu",
                files=[("images", ("menu.jpg", sample_image_bytes, "image/jpeg"))],
            )

            assert response.status_code == 200
            data = response.json()
            assert "vegetarian_items" in data
            assert "total_sum" in data
            assert data["total_sum"] == 22.49
            assert data["vegetarian_items"][0]["confidence"] == 0.95
            assert data["vegetarian_items"][0]["reasoning"] == "Contains vegetables and feta cheese"
        finally:
            menu_module.ocr_service = original_ocr
            menu_module.mcp_client = original_mcp

    def test_process_menu_base64(self, sample_image_bytes):
        """Test processing with base64 encoded images."""
        b64_image = base64.b64encode(sample_image_bytes).decode()

        mock_ocr = MagicMock()
        mock_ocr.extract_text_batch.return_value = ["Pasta $10.00"]

        mock_mcp = MagicMock()
        mock_mcp.classify_and_calculate = AsyncMock(return_value={
            "vegetarian_items": [{"name": "Pasta", "price": 10.00, "confidence": 0.88, "reasoning": "Pasta dish without meat"}],
            "total_sum": 10.00,
        })

        import app.routers.menu as menu_module
        original_ocr = menu_module.ocr_service
        original_mcp = menu_module.mcp_client

        try:
            menu_module.ocr_service = mock_ocr
            menu_module.mcp_client = mock_mcp

            from app.main import app
            client = TestClient(app)

            response = client.post(
                "/process-menu-base64",
                json={"images": [b64_image]},
            )

            assert response.status_code == 200
        finally:
            menu_module.ocr_service = original_ocr
            menu_module.mcp_client = original_mcp

    def test_process_menu_no_images(self, client):
        """Test error when no images provided."""
        response = client.post("/process-menu", files=[])
        assert response.status_code == 400

    def test_process_menu_too_many_images(self, client, sample_image_bytes):
        """Test error when too many images provided."""
        files = [("images", (f"menu{i}.jpg", sample_image_bytes, "image/jpeg")) for i in range(6)]
        response = client.post("/process-menu", files=files)
        assert response.status_code == 400

    def test_process_menu_needs_review(self, sample_image_bytes):
        """Test needs_review response handling."""
        mock_ocr = MagicMock()
        mock_ocr.extract_text_batch.return_value = ["Mushroom Risotto $14.00"]

        mock_mcp = MagicMock()
        mock_mcp.classify_and_calculate = AsyncMock(return_value={
            "status": "needs_review",
            "request_id": "test-id",
            "confident_items": [],
            "uncertain_items": [
                {"name": "Mushroom Risotto", "price": 14.00, "confidence": 0.55, "evidence": ["May contain chicken stock"]}
            ],
            "partial_sum": 0.0,
        })

        import app.routers.menu as menu_module
        original_ocr = menu_module.ocr_service
        original_mcp = menu_module.mcp_client

        try:
            menu_module.ocr_service = mock_ocr
            menu_module.mcp_client = mock_mcp

            from app.main import app
            client = TestClient(app)

            response = client.post(
                "/process-menu",
                files=[("images", ("menu.jpg", sample_image_bytes, "image/jpeg"))],
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "needs_review"
            assert "uncertain_items" in data
        finally:
            menu_module.ocr_service = original_ocr
            menu_module.mcp_client = original_mcp

    def test_process_menu_ocr_failure(self, sample_image_bytes):
        """Test OCR failure returns 422."""
        mock_ocr = MagicMock()
        mock_ocr.extract_text_batch.return_value = [""]

        import app.routers.menu as menu_module
        original_ocr = menu_module.ocr_service

        try:
            menu_module.ocr_service = mock_ocr

            from app.main import app
            client = TestClient(app)

            response = client.post(
                "/process-menu",
                files=[("images", ("menu.jpg", sample_image_bytes, "image/jpeg"))],
            )

            assert response.status_code == 422
        finally:
            menu_module.ocr_service = original_ocr
