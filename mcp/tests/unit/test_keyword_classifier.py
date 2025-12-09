import pytest
from app.services.keyword_classifier import KeywordClassifier


@pytest.fixture
def classifier():
    return KeywordClassifier()


class TestKeywordClassifier:
    def test_clear_vegetarian(self, classifier):
        """Test dish with clear vegetarian keywords."""
        result = classifier.classify("Tofu Stir Fry")
        assert result.is_vegetarian is True
        assert result.confidence >= 0.8
        assert "tofu" in [k.lower() for k in result.matched_keywords]

    def test_clear_non_vegetarian(self, classifier):
        """Test dish with clear non-vegetarian keywords."""
        result = classifier.classify("Grilled Chicken Breast")
        assert result.is_vegetarian is False
        assert result.confidence >= 0.8
        assert "chicken" in [k.lower() for k in result.matched_keywords]

    def test_vegetarian_keywords(self, classifier):
        """Test various vegetarian keywords."""
        vegetarian_dishes = [
            "Vegetarian Pasta",
            "Veggie Burger",
            "Paneer Tikka",
            "Mushroom Risotto",
            "Falafel Wrap",
            "Hummus Plate",
        ]
        for dish in vegetarian_dishes:
            result = classifier.classify(dish)
            assert result.is_vegetarian is True, f"Failed for {dish}"

    def test_non_vegetarian_keywords(self, classifier):
        """Test various non-vegetarian keywords."""
        non_veg_dishes = [
            "Beef Steak",
            "Grilled Salmon",
            "Bacon Burger",
            "Shrimp Scampi",
            "Pork Ribs",
            "Duck Confit",
        ]
        for dish in non_veg_dishes:
            result = classifier.classify(dish)
            assert result.is_vegetarian is False, f"Failed for {dish}"

    def test_conflicting_keywords(self, classifier):
        """Test dish with both vegetarian and non-vegetarian keywords."""
        # "Vegetable Chicken Stir Fry" has both "vegetable" and "chicken"
        result = classifier.classify("Vegetable Chicken Stir Fry")
        # Non-vegetarian should win in conflicts
        assert result.is_vegetarian is False
        assert result.confidence <= 0.6  # Lower confidence due to conflict

    def test_no_keywords(self, classifier):
        """Test dish with no recognized keywords."""
        result = classifier.classify("Special of the Day")
        assert result.is_vegetarian is None  # Uncertain
        assert result.confidence == 0.0
        assert len(result.matched_keywords) == 0

    def test_description_included(self, classifier):
        """Test that description is also analyzed."""
        result = classifier.classify("House Special", description="Made with fresh tofu and vegetables")
        assert result.is_vegetarian is True

    def test_case_insensitive(self, classifier):
        """Test case-insensitive matching."""
        result1 = classifier.classify("TOFU STIR FRY")
        result2 = classifier.classify("tofu stir fry")
        assert result1.is_vegetarian == result2.is_vegetarian


class TestSpecificIngredients:
    @pytest.fixture
    def classifier(self):
        return KeywordClassifier()

    def test_seafood_detection(self, classifier):
        """Test various seafood is detected."""
        seafood_dishes = ["Tuna Tartare", "Lobster Bisque", "Calamari", "Shrimp Cocktail"]
        for dish in seafood_dishes:
            result = classifier.classify(dish)
            assert result.is_vegetarian is False, f"Failed for {dish}"

    def test_cheese_dishes(self, classifier):
        """Test cheese dishes are vegetarian."""
        result = classifier.classify("Four Cheese Pizza")
        assert result.is_vegetarian is True

    def test_egg_based(self, classifier):
        """Test egg dishes (eggs are vegetarian per requirements)."""
        egg_dishes = [
            "Eggs Benedict",
            "Vegetable Omelette",
            "Spinach Frittata",
            "Quiche Lorraine",  # Note: Traditional has bacon, but keyword gives veg signal
        ]
        for dish in egg_dishes:
            result = classifier.classify(dish)
            assert result.is_vegetarian is True, f"Failed for {dish}"
