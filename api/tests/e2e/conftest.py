"""
E2E test fixtures and configuration.

These tests require the full system to be running (docker-compose up).
They test the complete flow: Image -> OCR -> MCP Classification -> Sum Calculation
"""
import os
import pytest
import httpx
from pathlib import Path

# Base URL for the API service
API_BASE_URL = os.environ.get("E2E_API_URL", "http://localhost:8000")

# Path to test menu images
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
MENU_IMAGES_DIR = FIXTURES_DIR / "menu_images"


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Return the API base URL."""
    return API_BASE_URL


@pytest.fixture(scope="session")
def http_client():
    """Create an HTTP client for e2e tests."""
    # Long timeout needed for LLM inference on slow hardware
    with httpx.Client(base_url=API_BASE_URL, timeout=300.0) as client:
        yield client


@pytest.fixture(scope="session")
def async_http_client():
    """Create an async HTTP client for e2e tests."""
    # Long timeout needed for LLM inference on slow hardware
    return httpx.AsyncClient(base_url=API_BASE_URL, timeout=300.0)


@pytest.fixture(scope="session")
def menu_images_dir() -> Path:
    """Return the path to the menu images directory."""
    return MENU_IMAGES_DIR


@pytest.fixture
def simple_menu_image(menu_images_dir) -> bytes:
    """Load the simple menu image (mixed veg and non-veg)."""
    image_path = menu_images_dir / "menu_simple.png"
    if not image_path.exists():
        pytest.skip(f"Menu image not found: {image_path}. Run generate_menu_images.py first.")
    return image_path.read_bytes()


@pytest.fixture
def all_veg_menu_image(menu_images_dir) -> bytes:
    """Load the all-vegetarian menu image."""
    image_path = menu_images_dir / "menu_all_veg.png"
    if not image_path.exists():
        pytest.skip(f"Menu image not found: {image_path}. Run generate_menu_images.py first.")
    return image_path.read_bytes()


@pytest.fixture
def mixed_menu_image(menu_images_dir) -> bytes:
    """Load the mixed menu image."""
    image_path = menu_images_dir / "menu_mixed.png"
    if not image_path.exists():
        pytest.skip(f"Menu image not found: {image_path}. Run generate_menu_images.py first.")
    return image_path.read_bytes()


@pytest.fixture
def no_veg_menu_image(menu_images_dir) -> bytes:
    """Load the no-vegetarian menu image."""
    image_path = menu_images_dir / "menu_no_veg.png"
    if not image_path.exists():
        pytest.skip(f"Menu image not found: {image_path}. Run generate_menu_images.py first.")
    return image_path.read_bytes()


@pytest.fixture
def multi_page_images(menu_images_dir) -> tuple[bytes, bytes]:
    """Load the multi-page menu images."""
    page1_path = menu_images_dir / "menu_multi_page1.png"
    page2_path = menu_images_dir / "menu_multi_page2.png"

    if not page1_path.exists() or not page2_path.exists():
        pytest.skip("Multi-page menu images not found. Run generate_menu_images.py first.")

    return page1_path.read_bytes(), page2_path.read_bytes()


def check_services_available():
    """Check if the API and MCP services are available."""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
        return response.status_code == 200
    except httpx.RequestError:
        return False


@pytest.fixture(scope="session", autouse=True)
def verify_services_running():
    """Verify that the services are running before running e2e tests."""
    if not check_services_available():
        pytest.skip(
            f"E2E tests require the full system to be running. "
            f"Start with 'docker-compose up -d' and ensure API is available at {API_BASE_URL}"
        )


# Expected results for test validation
# These are based on the generated menu images
EXPECTED_RESULTS = {
    "menu_simple": {
        # Greek Salad ($9.50), Garden Salad ($7.00), Veggie Burger ($12.00)
        "min_vegetarian_count": 2,  # At least 2 should be detected
        "expected_vegetarian_names": ["Greek Salad", "Garden Salad", "Veggie Burger"],
        "non_vegetarian_names": ["Grilled Chicken", "Beef Steak"],
        "min_total_sum": 16.00,  # At least some vegetarian items
        "max_total_sum": 30.00,  # Should not include meat items
    },
    "menu_all_veg": {
        # Margherita Pizza ($8.00), Vegetable Curry ($11.00), Caesar Salad ($9.50), French Fries ($7.00)
        "min_vegetarian_count": 3,
        "expected_vegetarian_names": ["Margherita Pizza", "Vegetable Curry", "Caesar Salad", "French Fries"],
        "non_vegetarian_names": [],
        "min_total_sum": 25.00,
        "max_total_sum": 40.00,
    },
    "menu_mixed": {
        # Tofu Stir Fry ($13.00), Mushroom Risotto ($14.00), Caprese Salad ($10.00)
        "min_vegetarian_count": 2,
        "expected_vegetarian_names": ["Tofu Stir Fry", "Mushroom Risotto", "Caprese Salad"],
        "non_vegetarian_names": ["Salmon Fillet", "Chicken Wings", "Pork Chops"],
        "min_total_sum": 20.00,
        "max_total_sum": 40.00,
    },
    "menu_no_veg": {
        # All meat items
        "min_vegetarian_count": 0,
        "expected_vegetarian_names": [],
        "non_vegetarian_names": ["Grilled Steak", "Fried Chicken", "Fish and Chips", "Lamb Chops"],
        "min_total_sum": 0.0,
        "max_total_sum": 5.0,  # Allow small margin for misclassification
    },
    "menu_multi_page": {
        # Bruschetta ($8.00), Spring Rolls ($9.00), Veggie Pasta ($14.00), Eggplant Parmesan ($15.00)
        "min_vegetarian_count": 3,
        "expected_vegetarian_names": ["Bruschetta", "Spring Rolls", "Veggie Pasta", "Eggplant Parmesan"],
        "non_vegetarian_names": ["Shrimp Cocktail", "Grilled Salmon"],
        "min_total_sum": 30.00,
        "max_total_sum": 50.00,
    },
}
