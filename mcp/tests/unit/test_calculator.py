import pytest
from app.services.calculator import Calculator


@pytest.fixture
def calculator():
    return Calculator()


class TestCalculator:
    def test_calculate_total_basic(self, calculator):
        """Test basic total calculation."""
        items = [
            {"name": "Item A", "price": 10.00},
            {"name": "Item B", "price": 5.50},
        ]
        total = calculator.calculate_total(items)
        assert total == 15.50

    def test_calculate_total_empty(self, calculator):
        """Test with empty list."""
        total = calculator.calculate_total([])
        assert total == 0.0

    def test_calculate_total_single(self, calculator):
        """Test with single item."""
        items = [{"name": "Item A", "price": 12.99}]
        total = calculator.calculate_total(items)
        assert total == 12.99

    def test_calculate_total_precision(self, calculator):
        """Test decimal precision."""
        items = [
            {"name": "Item A", "price": 10.333},
            {"name": "Item B", "price": 5.666},
        ]
        total = calculator.calculate_total(items)
        # Should round to 2 decimal places
        assert total == 16.00

    def test_calculate_total_large_numbers(self, calculator):
        """Test with larger numbers."""
        items = [
            {"name": "Item A", "price": 100.00},
            {"name": "Item B", "price": 250.50},
            {"name": "Item C", "price": 75.25},
        ]
        total = calculator.calculate_total(items)
        assert total == 425.75

    def test_calculate_total_with_missing_price(self, calculator):
        """Test graceful handling of missing price."""
        items = [
            {"name": "Item A", "price": 10.00},
            {"name": "Item B"},  # Missing price
        ]
        total = calculator.calculate_total(items)
        assert total == 10.00

    def test_calculate_total_with_request_id(self, calculator):
        """Test that request_id doesn't affect calculation."""
        items = [{"name": "Item A", "price": 10.00}]
        total = calculator.calculate_total(items, request_id="test-123")
        assert total == 10.00
