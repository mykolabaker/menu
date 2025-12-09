import re
import structlog

from ..models.classification import KeywordClassificationResult

logger = structlog.get_logger()


class KeywordClassifier:
    """Dictionary-based vegetarian classification using keywords."""

    # Positive indicators (vegetarian)
    VEGETARIAN_KEYWORDS = [
        # Explicit markers
        "vegetarian", "veggie", "vegan", "plant-based", "meatless",
        # Proteins
        "tofu", "tempeh", "seitan", "paneer", "halloumi",
        # Legumes
        "beans", "lentils", "chickpea", "hummus", "falafel", "dal", "daal",
        # Vegetables (as main ingredient indicators)
        "vegetable", "veggie", "mushroom", "eggplant", "aubergine",
        "zucchini", "courgette", "spinach", "broccoli", "cauliflower",
        # Cheese dishes (often vegetarian)
        "cheese", "mozzarella", "parmesan", "cheddar", "feta",
        # Common vegetarian dishes
        "caprese", "margherita", "primavera", "marinara", "alfredo",
        "garden", "harvest",
    ]

    # Negative indicators (non-vegetarian)
    NON_VEGETARIAN_KEYWORDS = [
        # Poultry
        "chicken", "turkey", "duck", "poultry", "wing", "wings",
        # Red meat
        "beef", "steak", "lamb", "pork", "veal", "venison", "bison",
        "burger", "meatball", "meatloaf", "meat",
        # Processed meats
        "bacon", "ham", "sausage", "salami", "pepperoni", "prosciutto",
        "chorizo", "pastrami", "corned beef",
        # Seafood
        "fish", "salmon", "tuna", "cod", "halibut", "tilapia", "trout",
        "shrimp", "prawn", "lobster", "crab", "clam", "mussel", "oyster",
        "scallop", "calamari", "squid", "octopus", "seafood", "anchovy",
        "anchovies", "sardine",
        # Other
        "ribs", "brisket", "roast", "carnitas", "pulled pork",
    ]

    def __init__(self):
        # Compile patterns for efficient matching
        self.veg_pattern = self._compile_pattern(self.VEGETARIAN_KEYWORDS)
        self.non_veg_pattern = self._compile_pattern(self.NON_VEGETARIAN_KEYWORDS)

    def _compile_pattern(self, keywords: list[str]) -> re.Pattern:
        """Compile keywords into a regex pattern with word boundaries."""
        escaped = [re.escape(kw) for kw in keywords]
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        return re.compile(pattern, re.IGNORECASE)

    def classify(self, dish_name: str, description: str | None = None) -> KeywordClassificationResult:
        """
        Classify a dish based on keyword matching.

        Args:
            dish_name: Name of the dish
            description: Optional description

        Returns:
            KeywordClassificationResult with classification and confidence
        """
        text = dish_name
        if description:
            text += " " + description

        text = text.lower()

        # Find matches
        veg_matches = self.veg_pattern.findall(text)
        non_veg_matches = self.non_veg_pattern.findall(text)

        # Unique matches
        veg_matches = list(set(veg_matches))
        non_veg_matches = list(set(non_veg_matches))

        log = logger.bind(
            dish_name=dish_name,
            veg_keywords=veg_matches,
            non_veg_keywords=non_veg_matches,
        )

        # Decision logic
        if non_veg_matches and not veg_matches:
            # Clear non-vegetarian
            log.debug("keyword_classification", result="non_vegetarian")
            return KeywordClassificationResult(
                is_vegetarian=False,
                confidence=0.9,
                matched_keywords=non_veg_matches,
            )

        if veg_matches and not non_veg_matches:
            # Clear vegetarian
            log.debug("keyword_classification", result="vegetarian")
            return KeywordClassificationResult(
                is_vegetarian=True,
                confidence=0.8,
                matched_keywords=veg_matches,
            )

        if veg_matches and non_veg_matches:
            # Conflicting signals - need more context
            # Non-veg keywords usually take precedence (e.g., "vegetable chicken stir-fry")
            log.debug("keyword_classification", result="conflicting")
            return KeywordClassificationResult(
                is_vegetarian=False,
                confidence=0.5,
                matched_keywords=non_veg_matches + veg_matches,
            )

        # No keywords found
        log.debug("keyword_classification", result="uncertain")
        return KeywordClassificationResult(
            is_vegetarian=None,
            confidence=0.0,
            matched_keywords=[],
        )


# Singleton instance
keyword_classifier = KeywordClassifier()
