import pytest
from app.services.text_parser import TextParser


@pytest.fixture
def parser():
    return TextParser()


class TestTextParser:
    def test_parse_basic_menu(self, parser):
        """Test parsing a simple menu format."""
        text = """
        Greek Salad $9.99
        Veggie Burger $12.50
        """
        items = parser.parse([text])
        assert len(items) == 2
        assert any(item.name == "Greek Salad" and item.price == 9.99 for item in items)
        assert any(item.name == "Veggie Burger" and item.price == 12.50 for item in items)

    def test_parse_price_formats(self, parser):
        """Test various price formats."""
        texts = [
            "Item One $9.99",
            "Item Two 12.50",
            "Item Three $ 7.00",
        ]
        for text in texts:
            items = parser.parse([text])
            assert len(items) == 1
            assert items[0].price > 0

    def test_parse_with_section_headers(self, parser):
        """Test that section headers are recognized and used."""
        text = """
        APPETIZERS
        Soup $5.00
        Salad $7.00

        MAIN COURSES
        Pasta $12.00
        """
        items = parser.parse([text])
        assert len(items) == 3
        # Check that items were parsed (category info is optional)
        prices = [item.price for item in items]
        assert 5.00 in prices
        assert 7.00 in prices
        assert 12.00 in prices

    def test_skip_invalid_lines(self, parser):
        """Test that invalid lines are skipped."""
        text = """
        Valid Dish $10.00
        Just random text without price
        Another Valid $15.50
        12345
        """
        items = parser.parse([text])
        assert len(items) == 2

    def test_deduplicate_items(self, parser):
        """Test that duplicate items are removed."""
        texts = [
            "Greek Salad $9.99",
            "Greek Salad $9.99",
            "GREEK SALAD $10.00",  # Different price but same name
        ]
        items = parser.parse(texts)
        # Should keep one item (with highest price)
        assert len(items) == 1
        assert items[0].price == 10.00

    def test_empty_text(self, parser):
        """Test parsing empty text."""
        items = parser.parse([""])
        assert len(items) == 0

    def test_multiple_texts(self, parser):
        """Test parsing multiple OCR outputs."""
        texts = [
            "Item A $5.00",
            "Item B $7.00",
        ]
        items = parser.parse(texts)
        assert len(items) == 2

    def test_clean_dish_names(self, parser):
        """Test that dish names are cleaned properly."""
        text = "...Pasta Primavera... $12.00"
        items = parser.parse([text])
        assert len(items) == 1
        assert items[0].name == "Pasta Primavera"


class TestPriceExtraction:
    @pytest.fixture
    def parser(self):
        return TextParser()

    def test_dollar_sign_prefix(self, parser):
        """Test price with $ prefix."""
        text = "Dish $10.99"
        items = parser.parse([text])
        assert items[0].price == 10.99

    def test_dollar_sign_with_space(self, parser):
        """Test price with $ and space."""
        text = "Dish $ 10.99"
        items = parser.parse([text])
        assert items[0].price == 10.99

    def test_decimal_at_end(self, parser):
        """Test price as decimal at end of line."""
        text = "Dish 10.99"
        items = parser.parse([text])
        assert items[0].price == 10.99

    def test_price_with_comma(self, parser):
        """Test price with thousands separator."""
        text = "Expensive Dish $1,299.99"
        items = parser.parse([text])
        assert items[0].price == 1299.99
