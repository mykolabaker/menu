import structlog

logger = structlog.get_logger()


class Calculator:
    """Service for calculating totals of vegetarian items."""

    def calculate_total(
        self,
        items: list[dict],
        request_id: str = "",
    ) -> float:
        """
        Calculate the sum of prices for vegetarian items.

        Args:
            items: List of items with 'price' field
            request_id: Request ID for logging

        Returns:
            Sum of prices rounded to 2 decimal places
        """
        log = logger.bind(request_id=request_id)

        if not items:
            log.debug("calculate_total", total=0.0, item_count=0)
            return 0.0

        total = sum(item.get("price", 0) for item in items)
        total = round(total, 2)

        log.debug("calculate_total", total=total, item_count=len(items))
        return total


# Singleton instance
calculator = Calculator()
