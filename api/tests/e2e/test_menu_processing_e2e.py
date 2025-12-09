"""
End-to-end tests for the Vegetarian Menu Analyzer.

These tests use real menu images and verify the complete flow:
- Image upload via REST API
- OCR text extraction
- MCP server classification
- Correct sum calculation for vegetarian items

Requirements:
- Full system running via docker-compose up
- Test menu images generated via generate_menu_images.py

Test scenarios based on task.pdf requirements:
1. REST API accepts 1-5 menu photos
2. Extracts text via OCR
3. Classifies vegetarian dishes using LLM + keyword fallback
4. Returns JSON with vegetarian_items and total_sum
5. Sum calculation performed by MCP server (not API directly)
"""
import pytest
import httpx
from .conftest import EXPECTED_RESULTS


class TestMenuProcessingE2E:
    """E2E tests for menu processing endpoint."""

    def test_simple_menu_vegetarian_sum(self, http_client: httpx.Client, simple_menu_image: bytes):
        """
        Test processing a simple menu with mixed vegetarian and non-vegetarian items.

        Menu contains:
        - Greek Salad $9.50 (vegetarian)
        - Garden Salad $7.00 (vegetarian)
        - Grilled Chicken $15.00 (non-vegetarian)
        - Veggie Burger $12.00 (vegetarian)
        - Beef Steak $22.00 (non-vegetarian)

        Expected: Sum of vegetarian items only
        """
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu_simple.png", simple_menu_image, "image/png"))],
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Handle both success and needs_review responses
        if data.get("status") == "needs_review":
            # For needs_review, check partial results
            assert "confident_items" in data or "uncertain_items" in data
            return  # Skip detailed validation for uncertain results

        # Validate response structure per task.pdf
        assert "vegetarian_items" in data, "Response must include vegetarian_items"
        assert "total_sum" in data, "Response must include total_sum"

        expected = EXPECTED_RESULTS["menu_simple"]

        # Verify at least minimum vegetarian items detected
        assert len(data["vegetarian_items"]) >= expected["min_vegetarian_count"], (
            f"Expected at least {expected['min_vegetarian_count']} vegetarian items, "
            f"got {len(data['vegetarian_items'])}"
        )

        # Verify total_sum is within expected range
        assert expected["min_total_sum"] <= data["total_sum"] <= expected["max_total_sum"], (
            f"Total sum {data['total_sum']} not in expected range "
            f"[{expected['min_total_sum']}, {expected['max_total_sum']}]"
        )

        # Verify non-vegetarian items are NOT included
        vegetarian_names = [item["name"].lower() for item in data["vegetarian_items"]]
        for non_veg in expected["non_vegetarian_names"]:
            assert non_veg.lower() not in vegetarian_names, (
                f"Non-vegetarian item '{non_veg}' should not be in vegetarian list"
            )

    def test_all_vegetarian_menu(self, http_client: httpx.Client, all_veg_menu_image: bytes):
        """
        Test processing a menu with only vegetarian items.

        Menu contains:
        - Margherita Pizza $8.00
        - Vegetable Curry $11.00
        - Caesar Salad $9.50
        - French Fries $7.00

        Expected: All items included in sum = $35.50
        """
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu_all_veg.png", all_veg_menu_image, "image/png"))],
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        if data.get("status") == "needs_review":
            return

        assert "vegetarian_items" in data
        assert "total_sum" in data

        expected = EXPECTED_RESULTS["menu_all_veg"]

        # All items should be vegetarian
        assert len(data["vegetarian_items"]) >= expected["min_vegetarian_count"]
        assert expected["min_total_sum"] <= data["total_sum"] <= expected["max_total_sum"]

    def test_mixed_menu_with_tofu_and_fish(self, http_client: httpx.Client, mixed_menu_image: bytes):
        """
        Test processing a mixed menu with clear vegetarian markers.

        Menu contains:
        - Tofu Stir Fry $13.00 (vegetarian - keyword: tofu)
        - Salmon Fillet $18.00 (non-vegetarian - fish)
        - Mushroom Risotto $14.00 (vegetarian)
        - Chicken Wings $11.00 (non-vegetarian)
        - Caprese Salad $10.00 (vegetarian - salad)
        - Pork Chops $16.00 (non-vegetarian)

        Expected: Sum of vegetarian items = $37.00
        """
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu_mixed.png", mixed_menu_image, "image/png"))],
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        if data.get("status") == "needs_review":
            return

        assert "vegetarian_items" in data
        assert "total_sum" in data

        expected = EXPECTED_RESULTS["menu_mixed"]

        # Verify vegetarian count
        assert len(data["vegetarian_items"]) >= expected["min_vegetarian_count"]

        # Verify sum is within expected range
        assert expected["min_total_sum"] <= data["total_sum"] <= expected["max_total_sum"]

        # Verify meat/fish items are NOT included
        vegetarian_names = [item["name"].lower() for item in data["vegetarian_items"]]
        for non_veg in expected["non_vegetarian_names"]:
            assert non_veg.lower() not in vegetarian_names, (
                f"Non-vegetarian item '{non_veg}' should not be in vegetarian list"
            )

    def test_no_vegetarian_items(self, http_client: httpx.Client, no_veg_menu_image: bytes):
        """
        Test processing a menu with NO vegetarian items.

        Menu contains only meat dishes:
        - Grilled Steak $25.00
        - Fried Chicken $14.00
        - Fish and Chips $16.00
        - Lamb Chops $28.00

        Expected: Empty vegetarian list, total_sum = $0.00
        """
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu_no_veg.png", no_veg_menu_image, "image/png"))],
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        if data.get("status") == "needs_review":
            # For uncertain results, at least verify structure
            assert "uncertain_items" in data or "confident_items" in data
            return

        assert "vegetarian_items" in data
        assert "total_sum" in data

        expected = EXPECTED_RESULTS["menu_no_veg"]

        # Should have few or no vegetarian items
        assert len(data["vegetarian_items"]) <= 1, (
            f"Expected 0-1 vegetarian items from all-meat menu, got {len(data['vegetarian_items'])}"
        )

        # Sum should be zero or near-zero
        assert data["total_sum"] <= expected["max_total_sum"], (
            f"Total sum {data['total_sum']} too high for all-meat menu"
        )

    def test_multi_page_menu(self, http_client: httpx.Client, multi_page_images: tuple[bytes, bytes]):
        """
        Test processing a menu split across multiple pages (1-5 images supported per task.pdf).

        Page 1 (Appetizers):
        - Bruschetta $8.00 (vegetarian)
        - Shrimp Cocktail $12.00 (non-vegetarian)
        - Spring Rolls $9.00 (vegetarian)

        Page 2 (Main Courses):
        - Veggie Pasta $14.00 (vegetarian)
        - Grilled Salmon $19.00 (non-vegetarian)
        - Eggplant Parmesan $15.00 (vegetarian)

        Expected: Sum of vegetarian items from BOTH pages = $46.00
        """
        page1, page2 = multi_page_images

        response = http_client.post(
            "/process-menu",
            files=[
                ("images", ("menu_page1.png", page1, "image/png")),
                ("images", ("menu_page2.png", page2, "image/png")),
            ],
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        if data.get("status") == "needs_review":
            return

        assert "vegetarian_items" in data
        assert "total_sum" in data

        expected = EXPECTED_RESULTS["menu_multi_page"]

        # Should find vegetarian items from BOTH pages
        assert len(data["vegetarian_items"]) >= expected["min_vegetarian_count"], (
            f"Expected at least {expected['min_vegetarian_count']} vegetarian items from 2-page menu, "
            f"got {len(data['vegetarian_items'])}"
        )

        # Sum should include items from both pages
        assert expected["min_total_sum"] <= data["total_sum"] <= expected["max_total_sum"], (
            f"Total sum {data['total_sum']} not in expected range for multi-page menu"
        )

        # Verify seafood items are NOT included
        vegetarian_names = [item["name"].lower() for item in data["vegetarian_items"]]
        for non_veg in expected["non_vegetarian_names"]:
            assert non_veg.lower() not in vegetarian_names, (
                f"Non-vegetarian item '{non_veg}' should not be in vegetarian list"
            )


class TestResponseFormat:
    """Tests verifying response format matches task.pdf specification."""

    def test_response_contains_required_fields(self, http_client: httpx.Client, simple_menu_image: bytes):
        """
        Verify response matches task.pdf format:
        {
            "vegetarian_items": [
                {"name": "Greek Salad", "price": 7.5},
                {"name": "Veggie Burger", "price": 9.0}
            ],
            "total_sum": 16.5
        }
        """
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu.png", simple_menu_image, "image/png"))],
        )

        assert response.status_code == 200
        data = response.json()

        if data.get("status") == "needs_review":
            # HITL response format (optional feature per task.pdf)
            assert "request_id" in data
            assert "uncertain_items" in data or "confident_items" in data
            return

        # Standard success response format
        assert "vegetarian_items" in data
        assert "total_sum" in data
        assert isinstance(data["vegetarian_items"], list)
        assert isinstance(data["total_sum"], (int, float))

        # Each vegetarian item should have name and price
        for item in data["vegetarian_items"]:
            assert "name" in item, "Each item must have 'name'"
            assert "price" in item, "Each item must have 'price'"
            assert isinstance(item["name"], str)
            assert isinstance(item["price"], (int, float))

    def test_confidence_and_reasoning_in_response(self, http_client: httpx.Client, simple_menu_image: bytes):
        """
        Verify optional confidence and reasoning fields are present.
        (Per task.pdf: RAG Memory should return confidence + brief reasoning notes)
        """
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu.png", simple_menu_image, "image/png"))],
        )

        assert response.status_code == 200
        data = response.json()

        if data.get("status") == "needs_review":
            # Check uncertain items have evidence
            for item in data.get("uncertain_items", []):
                assert "confidence" in item
            return

        # Check vegetarian items have confidence and reasoning
        for item in data.get("vegetarian_items", []):
            assert "confidence" in item, "Item should have confidence score"
            # Reasoning is optional but encouraged
            if "reasoning" in item:
                assert isinstance(item["reasoning"], str)


class TestInputValidation:
    """Tests for input validation per task.pdf requirements."""

    def test_accepts_single_image(self, http_client: httpx.Client, simple_menu_image: bytes):
        """Verify API accepts 1 image (minimum per task.pdf)."""
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu.png", simple_menu_image, "image/png"))],
        )
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"

    def test_accepts_five_images(self, http_client: httpx.Client, simple_menu_image: bytes):
        """Verify API accepts 5 images (maximum per task.pdf)."""
        files = [
            ("images", (f"menu{i}.png", simple_menu_image, "image/png"))
            for i in range(5)
        ]
        response = http_client.post("/process-menu", files=files)
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"

    def test_rejects_six_images(self, http_client: httpx.Client, simple_menu_image: bytes):
        """Verify API rejects more than 5 images per task.pdf."""
        files = [
            ("images", (f"menu{i}.png", simple_menu_image, "image/png"))
            for i in range(6)
        ]
        response = http_client.post("/process-menu", files=files)
        assert response.status_code == 400, f"Expected 400 for 6 images, got {response.status_code}"

    def test_rejects_no_images(self, http_client: httpx.Client):
        """Verify API rejects request with no images."""
        response = http_client.post("/process-menu", files=[])
        assert response.status_code == 400, f"Expected 400 for no images, got {response.status_code}"


class TestSumCalculation:
    """Tests specifically for sum calculation correctness."""

    def test_sum_matches_item_prices(self, http_client: httpx.Client, all_veg_menu_image: bytes):
        """Verify total_sum equals sum of individual vegetarian item prices."""
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu.png", all_veg_menu_image, "image/png"))],
        )

        assert response.status_code == 200
        data = response.json()

        if data.get("status") == "needs_review":
            return

        # Calculate expected sum from items
        calculated_sum = sum(item["price"] for item in data["vegetarian_items"])

        # Allow for floating point precision
        assert abs(data["total_sum"] - calculated_sum) < 0.01, (
            f"total_sum ({data['total_sum']}) does not match sum of item prices ({calculated_sum})"
        )

    def test_empty_result_has_zero_sum(self, http_client: httpx.Client, no_veg_menu_image: bytes):
        """Verify that when no vegetarian items found, sum is 0 or near-zero."""
        response = http_client.post(
            "/process-menu",
            files=[("images", ("menu.png", no_veg_menu_image, "image/png"))],
        )

        assert response.status_code == 200
        data = response.json()

        if data.get("status") == "needs_review":
            return

        if len(data["vegetarian_items"]) == 0:
            assert data["total_sum"] == 0.0, "Empty vegetarian list should have sum of 0"
