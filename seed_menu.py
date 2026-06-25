import os
from app import create_app
from models import db
from models.menu import Menu

app = create_app()

menu_items = [
    # COFFEE DRINKS
    {"name": "Espresso", "category": "Coffee Drinks", "price": 490.0, "description": "Rich and bold."},
    {"name": "Iced Coffee", "category": "Coffee Drinks", "price": 410.0, "description": "Chilled perfection."},
    {"name": "Macchiato", "category": "Coffee Drinks", "price": 490.0, "description": "Espresso with a dash of milk."},
    {"name": "Coffee with Cream", "category": "Coffee Drinks", "price": 490.0, "description": "Smooth and creamy."},
    {"name": "Chocolate Coffee", "category": "Coffee Drinks", "price": 350.0, "description": "A sweet chocolate blend."},
    {"name": "Long Black", "category": "Coffee Drinks", "price": 250.0, "description": "Robust and strong."},
    {"name": "House Blend", "category": "Coffee Drinks", "price": 250.0, "description": "Our signature roast."},
    {"name": "Decaf Coffee", "category": "Coffee Drinks", "price": 250.0, "description": "All flavor, no jitters."},
    {"name": "Latte", "category": "Coffee Drinks", "price": 410.0, "description": "Creamy espresso classic."},
    
    # SALADS
    {"name": "Arugula", "category": "Salads", "price": 490.0, "description": "Fresh and peppery."},
    {"name": "Spinach", "category": "Salads", "price": 410.0, "description": "Healthy and crisp."},
    {"name": "Cauliflower", "category": "Salads", "price": 490.0, "description": "Roasted to perfection."},
    {"name": "Avocado", "category": "Salads", "price": 490.0, "description": "Creamy and satisfying."},
    {"name": "Cucumber", "category": "Salads", "price": 350.0, "description": "Cool and refreshing."},
    {"name": "Lettuce", "category": "Salads", "price": 250.0, "description": "Classic greens."},
    {"name": "Beets", "category": "Salads", "price": 250.0, "description": "Sweet and earthy."},
    {"name": "Carrots", "category": "Salads", "price": 250.0, "description": "Crunchy and sweet."},
    {"name": "Mixed", "category": "Salads", "price": 410.0, "description": "A perfect blend."},
    
    # SOUPS
    {"name": "Cheddar & Broccoli", "category": "Soups", "price": 410.0, "description": "Rich and cheesy."},
    {"name": "Pumpkin", "category": "Soups", "price": 410.0, "description": "Warm and seasonal."},
    {"name": "Carrots & Celery", "category": "Soups", "price": 410.0, "description": "Hearty and wholesome."},
    {"name": "Cream of Potato", "category": "Soups", "price": 440.0, "description": "Comfort in a bowl."},
    {"name": "Butter Squash", "category": "Soups", "price": 440.0, "description": "Smooth and slightly sweet."},
    {"name": "Split Pea", "category": "Soups", "price": 440.0, "description": "Classic comfort."},
    {"name": "Clam Chowder", "category": "Soups", "price": 580.0, "description": "A seafood delight."},
    {"name": "House Special", "category": "Soups", "price": 580.0, "description": "Chef's daily creation."},
    {"name": "Lobster Bisque", "category": "Soups", "price": 660.0, "description": "Premium and creamy."},
    
    # DESSERTS
    {"name": "Chocolate Cheesecake", "category": "Desserts", "price": 490.0, "description": "Decadent and rich."},
    {"name": "Sticky Toffee Pudding", "category": "Desserts", "price": 410.0, "description": "Sweet and sticky."},
    {"name": "Fried Ice Cream", "category": "Desserts", "price": 490.0, "description": "Hot and cold contrast."},
    {"name": "Banana Boat Pie", "category": "Desserts", "price": 490.0, "description": "Fruity and fun."},
    {"name": "Strawberry Pudding", "category": "Desserts", "price": 350.0, "description": "Light and sweet."},
    {"name": "Rum Cake", "category": "Desserts", "price": 250.0, "description": "A mature treat."},
    {"name": "Nutella Cheesecake", "category": "Desserts", "price": 250.0, "description": "Hazelnut perfection."},
    {"name": "Tiramisu", "category": "Desserts", "price": 250.0, "description": "Classic Italian layer cake."},
    {"name": "Brownie Gelato", "category": "Desserts", "price": 410.0, "description": "Warm brownie with gelato."},

    # TEA
    {"name": "Matcha Latte", "category": "Tea", "price": 350.0, "description": "Creamy stone-ground green tea."},
    {"name": "Earl Grey Tea", "category": "Tea", "price": 250.0, "description": "Classic black tea infused with bergamot."},
    {"name": "Lemon Miso Kefir", "category": "Tea", "price": 410.0, "description": "White miso, preserved lemon, live cultures."},

    # COLD DRINKS
    {"name": "Iced Latte", "category": "Cold Drinks", "price": 410.0, "description": "Chilled creamy espresso classic."},
    {"name": "Cold Brew Coffee", "category": "Cold Drinks", "price": 350.0, "description": "Slow-steeped smooth iced coffee."},

    # SNACKS
    {"name": "Avocado Toast", "category": "Snacks", "price": 490.0, "description": "Creamy avocado on rustic sourdough toast."},
    {"name": "Wild Mushroom Crostini", "category": "Snacks", "price": 410.0, "description": "Roasted forest mushrooms on crispy bread."},

    # BREAKFAST
    {"name": "Granola Fruit Bowl", "category": "Breakfast", "price": 350.0, "description": "Organic granola, seasonal berries, honey."},
    {"name": "Classic Pancake", "category": "Breakfast", "price": 410.0, "description": "Fluffy pancakes served with maple syrup."},

    # COMBOS
    {"name": "Espresso & Cheesecake Combo", "category": "Combos", "price": 600.0, "description": "Rich espresso paired with Nutella cheesecake."},
    {"name": "Soup & Salad Combo", "category": "Combos", "price": 700.0, "description": "Cheddar & Broccoli soup with Avocado salad."}
]

def get_slug(name):
    return name.lower().replace(" & ", "_").replace(" ", "_").replace("'", "")

with app.app_context():
    # Clear existing menu items before seeding
    db.session.query(Menu).delete()
    
    for item in menu_items:
        slug = get_slug(item['name'])
        new_item = Menu(
            name=item['name'],
            category=item['category'],
            price=item['price'],
            description=item['description'],
            image_url=f"/static/images/menu_previews/{slug}.jpg"
        )
        db.session.add(new_item)
    
    db.session.commit()
    print("Menu successfully seeded.")
