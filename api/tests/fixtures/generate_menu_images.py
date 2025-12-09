"""
Generate sample menu images for e2e testing.

These images contain known dishes with known prices for verifying
the vegetarian sum calculation is correct.
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Get the directory where this script is located
FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_IMAGES_DIR = os.path.join(FIXTURE_DIR, "menu_images")


def get_font(size: int):
    """Get a font, falling back to default if system fonts aren't available."""
    try:
        # Try common system fonts
        for font_name in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "arial.ttf",
        ]:
            if os.path.exists(font_name):
                return ImageFont.truetype(font_name, size)
    except Exception:
        pass
    # Fall back to default
    return ImageFont.load_default()


def create_menu_image(
    items: list[tuple[str, float]],
    title: str = "MENU",
    filename: str = "menu.png",
    width: int = 600,
    height: int = 800,
) -> str:
    """
    Create a menu image with the given items.

    Args:
        items: List of (dish_name, price) tuples
        title: Menu title
        filename: Output filename
        width: Image width
        height: Image height

    Returns:
        Path to the created image
    """
    # Create white background
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = get_font(36)
    item_font = get_font(24)

    # Draw title
    y_pos = 40
    draw.text((width // 2 - 50, y_pos), title, fill="black", font=title_font)
    y_pos += 80

    # Draw separator line
    draw.line([(50, y_pos), (width - 50, y_pos)], fill="black", width=2)
    y_pos += 40

    # Draw each item
    for dish_name, price in items:
        # Draw dish name on the left
        draw.text((60, y_pos), dish_name, fill="black", font=item_font)
        # Draw price on the right
        price_str = f"${price:.2f}"
        draw.text((width - 120, y_pos), price_str, fill="black", font=item_font)
        y_pos += 50

    # Save image
    output_path = os.path.join(MENU_IMAGES_DIR, filename)
    os.makedirs(MENU_IMAGES_DIR, exist_ok=True)
    img.save(output_path, "PNG")

    return output_path


def generate_test_menus():
    """Generate all test menu images."""

    # Menu 1: Simple vegetarian menu
    # Expected vegetarian: Greek Salad ($9.50), Garden Salad ($7.00), Veggie Burger ($12.00)
    # Expected non-vegetarian: Grilled Chicken ($15.00), Beef Steak ($22.00)
    # Expected total: 9.50 + 7.00 + 12.00 = $28.50
    menu1_items = [
        ("Greek Salad", 9.50),
        ("Garden Salad", 7.00),
        ("Grilled Chicken", 15.00),
        ("Veggie Burger", 12.00),
        ("Beef Steak", 22.00),
    ]
    create_menu_image(menu1_items, "LUNCH MENU", "menu_simple.png")

    # Menu 2: All vegetarian items
    # Expected total: 8.00 + 11.00 + 9.50 + 7.00 = $35.50
    menu2_items = [
        ("Margherita Pizza", 8.00),
        ("Vegetable Curry", 11.00),
        ("Caesar Salad", 9.50),
        ("French Fries", 7.00),
    ]
    create_menu_image(menu2_items, "VEGETARIAN", "menu_all_veg.png")

    # Menu 3: Mixed menu with clear items
    # Expected vegetarian: Tofu Stir Fry ($13.00), Mushroom Risotto ($14.00), Caprese Salad ($10.00)
    # Expected non-vegetarian: Salmon Fillet ($18.00), Chicken Wings ($11.00), Pork Chops ($16.00)
    # Expected total: 13.00 + 14.00 + 10.00 = $37.00
    menu3_items = [
        ("Tofu Stir Fry", 13.00),
        ("Salmon Fillet", 18.00),
        ("Mushroom Risotto", 14.00),
        ("Chicken Wings", 11.00),
        ("Caprese Salad", 10.00),
        ("Pork Chops", 16.00),
    ]
    create_menu_image(menu3_items, "DINNER MENU", "menu_mixed.png")

    # Menu 4: No vegetarian items
    # Expected total: $0.00
    menu4_items = [
        ("Grilled Steak", 25.00),
        ("Fried Chicken", 14.00),
        ("Fish and Chips", 16.00),
        ("Lamb Chops", 28.00),
    ]
    create_menu_image(menu4_items, "MEAT LOVERS", "menu_no_veg.png")

    # Menu 5: Appetizers section (for multi-image test - page 1)
    # Expected vegetarian: Bruschetta ($8.00), Spring Rolls ($9.00)
    # Expected non-vegetarian: Shrimp Cocktail ($12.00)
    menu5a_items = [
        ("Bruschetta", 8.00),
        ("Shrimp Cocktail", 12.00),
        ("Spring Rolls", 9.00),
    ]
    create_menu_image(menu5a_items, "APPETIZERS", "menu_multi_page1.png", height=500)

    # Menu 5: Main courses section (for multi-image test - page 2)
    # Expected vegetarian: Veggie Pasta ($14.00), Eggplant Parmesan ($15.00)
    # Expected non-vegetarian: Grilled Salmon ($19.00)
    menu5b_items = [
        ("Veggie Pasta", 14.00),
        ("Grilled Salmon", 19.00),
        ("Eggplant Parmesan", 15.00),
    ]
    create_menu_image(menu5b_items, "MAIN COURSES", "menu_multi_page2.png", height=500)

    print("Generated test menu images in:", MENU_IMAGES_DIR)
    print("Files created:")
    for f in os.listdir(MENU_IMAGES_DIR):
        if f.endswith(".png"):
            print(f"  - {f}")


if __name__ == "__main__":
    generate_test_menus()
