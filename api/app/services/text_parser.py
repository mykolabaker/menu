import re
import structlog
from typing import NamedTuple

from ..models.menu_item import MenuItem

logger = structlog.get_logger()


class PriceMatch(NamedTuple):
    """Represents a matched price in text."""
    value: float
    start: int
    end: int


class TextParser:
    """Parses OCR text to extract menu items with names and prices."""

    # Price patterns in order of specificity
    PRICE_PATTERNS = [
        # $12.99 or $ 12.99
        r'\$\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
        # 12.99$ or 12.99 $
        r'(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*\$',
        # 12.99 USD/EUR/GBP
        r'(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:USD|EUR|GBP|usd|eur|gbp)',
        # Plain decimal at end of line (like "Burger 12.99")
        r'(\d+\.\d{2})\s*$',
    ]

    # Section headers to skip
    SECTION_HEADERS = [
        "appetizers", "starters", "main courses", "mains", "entrees",
        "desserts", "beverages", "drinks", "sides", "salads", "soups",
        "breakfast", "lunch", "dinner", "specials", "today's specials",
    ]

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PRICE_PATTERNS]

    def parse(self, texts: list[str], request_id: str = "") -> list[MenuItem]:
        """
        Parse multiple OCR text outputs into structured menu items.

        Args:
            texts: List of OCR text strings
            request_id: Request ID for logging

        Returns:
            Deduplicated list of MenuItem objects
        """
        log = logger.bind(request_id=request_id)
        log.debug("Starting text parsing", text_count=len(texts))

        all_items: list[MenuItem] = []

        for i, text in enumerate(texts):
            items = self._parse_single(text, request_id, i)
            all_items.extend(items)

        # Deduplicate by normalized name
        deduplicated = self._deduplicate(all_items)

        log.info(
            "parsing_completed",
            total_items=len(all_items),
            deduplicated_items=len(deduplicated),
        )

        return deduplicated

    def _parse_single(self, text: str, request_id: str, text_index: int) -> list[MenuItem]:
        """Parse a single OCR text output."""
        log = logger.bind(request_id=request_id, text_index=text_index)
        items = []

        lines = text.split("\n")
        current_category = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if self._is_section_header(line):
                current_category = line.title()
                continue

            # Try to extract menu item
            item = self._extract_item(line, current_category)
            if item:
                items.append(item)

        log.debug("Parsed text", items_found=len(items))
        return items

    def _is_section_header(self, line: str) -> bool:
        """Check if line is a menu section header."""
        normalized = line.lower().strip()
        # Remove common punctuation
        normalized = re.sub(r'[:\-_=*#]', '', normalized).strip()

        if normalized in self.SECTION_HEADERS:
            return True

        # Check if line is all caps and short (likely header)
        if line.isupper() and len(line.split()) <= 3:
            return True

        return False

    def _extract_item(self, line: str, category: str | None) -> MenuItem | None:
        """Extract a menu item from a single line."""
        # Find price in line
        price_match = self._find_price(line)
        if not price_match:
            return None

        # Extract name (text before price)
        name = line[:price_match.start].strip()

        # Clean up name
        name = self._clean_name(name)

        if not name or len(name) < 2:
            return None

        # Check if name looks like a valid dish
        if not self._is_valid_dish_name(name):
            return None

        return MenuItem(
            name=name,
            price=price_match.value,
            description=None,
            category=category,
        )

    def _find_price(self, text: str) -> PriceMatch | None:
        """Find a price in text using multiple patterns."""
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                price_str = match.group(1)
                # Remove commas and convert to float
                price = float(price_str.replace(",", ""))
                return PriceMatch(
                    value=round(price, 2),
                    start=match.start(),
                    end=match.end(),
                )
        return None

    def _clean_name(self, name: str) -> str:
        """Clean up extracted dish name."""
        # Remove trailing dots, dashes, periods often used as fillers
        name = re.sub(r'[\.\-_]+$', '', name)
        name = re.sub(r'^[\.\-_]+', '', name)

        # Remove multiple spaces
        name = re.sub(r'\s+', ' ', name)

        # Remove common noise patterns
        name = re.sub(r'\*+', '', name)

        return name.strip()

    def _is_valid_dish_name(self, name: str) -> bool:
        """Check if a string looks like a valid dish name."""
        # Too short
        if len(name) < 3:
            return False

        # Only numbers
        if name.replace(" ", "").isdigit():
            return False

        # Only special characters
        if not re.search(r'[a-zA-Z]', name):
            return False

        # Has at least one word with 2+ letters
        words = name.split()
        if not any(len(w) >= 2 and w.isalpha() for w in words):
            return False

        return True

    def _deduplicate(self, items: list[MenuItem]) -> list[MenuItem]:
        """Remove duplicate items by normalized name, keeping highest price."""
        seen: dict[str, MenuItem] = {}

        for item in items:
            key = item.normalized_name()
            if key not in seen or item.price > seen[key].price:
                seen[key] = item

        return list(seen.values())


# Singleton instance
text_parser = TextParser()
