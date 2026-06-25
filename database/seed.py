from models import db
from models.user import User
from models.menu import MenuItem


def seed_database():
    """Seed the database with initial admin, sample customer, and menu items.

    Checks for existing data before inserting to prevent duplicates.
    """

    # --- Users ---
    if User.query.count() == 0:
        print('[Seed] Creating users...')

        admin = User(name='Admin', email='admin@hrdcafe.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        customer = User(name='John Doe', email='john@example.com', role='customer')
        customer.set_password('customer123')
        db.session.add(customer)

        db.session.commit()
        print('[Seed] ✓ Users created (admin + sample customer)')
    else:
        print('[Seed] Users already exist — skipping.')

    # --- Menu Items ---
    if MenuItem.query.count() == 0:
        print('[Seed] Creating menu items...')

        menu_items = [
            # ── Coffee ──────────────────────────────────────────────
            MenuItem(
                name='Espresso',
                category='coffee',
                description='Rich and bold single shot of pure espresso',
                price=3.99,
            ),
            MenuItem(
                name='Cappuccino',
                category='coffee',
                description='Classic Italian espresso with steamed milk foam',
                price=4.99,
            ),
            MenuItem(
                name='Latte',
                category='coffee',
                description='Smooth espresso with velvety steamed milk',
                price=4.99,
            ),
            MenuItem(
                name='Mocha',
                category='coffee',
                description='Espresso with chocolate and steamed milk',
                price=5.49,
            ),
            MenuItem(
                name='Cold Brew',
                category='coffee',
                description='Slow-steeped for 20 hours, smooth and refreshing',
                price=4.49,
            ),

            # ── AI Signature Drinks ─────────────────────────────────
            MenuItem(
                name='GPT Mocha',
                category='ai_signature',
                description='AI-crafted blend of premium chocolate and espresso with neural flavor optimization',
                price=6.99,
            ),
            MenuItem(
                name='Neural Latte',
                category='ai_signature',
                description='Machine-learned perfect milk-to-espresso ratio with vanilla undertones',
                price=6.49,
            ),
            MenuItem(
                name='Quantum Cold Brew',
                category='ai_signature',
                description='Superposition of flavors: citrus, chocolate, and caramel in cold brew',
                price=6.99,
            ),
            MenuItem(
                name='Algorithm Affogato',
                category='ai_signature',
                description='Computationally perfect espresso poured over artisan gelato',
                price=7.49,
            ),

            # ── Food — Sandwiches ───────────────────────────────────
            MenuItem(
                name='Classic Club Sandwich',
                category='food',
                sub_category='sandwiches',
                description='Triple-decker sandwich with turkey, bacon, lettuce, and tomato on toasted bread',
                price=8.99,
            ),
            MenuItem(
                name='Grilled Chicken Panini',
                category='food',
                sub_category='sandwiches',
                description='Herb-marinated grilled chicken with mozzarella and sun-dried tomatoes on ciabatta',
                price=9.49,
            ),
            MenuItem(
                name='Veggie Wrap',
                category='food',
                sub_category='sandwiches',
                description='Fresh seasonal vegetables with hummus and mixed greens in a whole-wheat wrap',
                price=7.99,
            ),
            MenuItem(
                name='Protein Sandwich',
                category='food',
                sub_category='sandwiches',
                description='Grilled chicken breast with egg whites, avocado, and spinach on multigrain bread',
                price=9.99,
            ),

            # ── Food — Pastries ─────────────────────────────────────
            MenuItem(
                name='Butter Croissant',
                category='food',
                sub_category='pastries',
                description='Flaky, golden-baked French croissant made with pure butter',
                price=3.99,
            ),
            MenuItem(
                name='Chocolate Danish',
                category='food',
                sub_category='pastries',
                description='Layered pastry filled with rich Belgian chocolate cream',
                price=4.49,
            ),
            MenuItem(
                name='Blueberry Muffin',
                category='food',
                sub_category='pastries',
                description='Moist muffin bursting with fresh blueberries and a crumble topping',
                price=3.99,
            ),
            MenuItem(
                name='Cinnamon Roll',
                category='food',
                sub_category='pastries',
                description='Warm, soft roll swirled with cinnamon sugar and topped with cream-cheese icing',
                price=4.99,
            ),

            # ── Food — Cakes ───────────────────────────────────────
            MenuItem(
                name='Dark Chocolate Brownie',
                category='food',
                sub_category='cakes',
                description='Dense, fudgy brownie made with 70% dark chocolate',
                price=5.49,
            ),
            MenuItem(
                name='New York Cheesecake',
                category='food',
                sub_category='cakes',
                description='Classic creamy cheesecake with a buttery graham-cracker crust',
                price=6.99,
            ),
            MenuItem(
                name='Red Velvet Slice',
                category='food',
                sub_category='cakes',
                description='Velvety cocoa cake layered with tangy cream-cheese frosting',
                price=6.49,
            ),
            MenuItem(
                name='Tiramisu',
                category='food',
                sub_category='cakes',
                description='Italian classic with espresso-soaked ladyfingers and mascarpone cream',
                price=7.49,
            ),

            # ── Food — Salads ──────────────────────────────────────
            MenuItem(
                name='Caesar Salad',
                category='food',
                sub_category='salads',
                description='Crisp romaine lettuce with parmesan, croutons, and house-made Caesar dressing',
                price=8.49,
            ),
            MenuItem(
                name='Greek Salad',
                category='food',
                sub_category='salads',
                description='Cucumber, tomatoes, olives, red onion, and feta tossed in herb vinaigrette',
                price=7.99,
            ),
            MenuItem(
                name='Quinoa Bowl',
                category='food',
                sub_category='salads',
                description='Protein-packed quinoa with roasted vegetables, avocado, and lemon-tahini dressing',
                price=9.49,
            ),

            # ── Food — Snacks ──────────────────────────────────────
            MenuItem(
                name='French Fries',
                category='food',
                sub_category='snacks',
                description='Crispy golden fries seasoned with sea salt, served with ketchup and aioli',
                price=4.99,
            ),
            MenuItem(
                name='Nachos',
                category='food',
                sub_category='snacks',
                description='Tortilla chips loaded with melted cheese, jalapeños, salsa, and sour cream',
                price=6.49,
            ),
            MenuItem(
                name='Bruschetta',
                category='food',
                sub_category='snacks',
                description='Toasted baguette slices topped with diced tomatoes, basil, and balsamic glaze',
                price=5.99,
            ),
        ]

        db.session.add_all(menu_items)
        db.session.commit()
        print(f'[Seed] ✓ {len(menu_items)} menu items created')
    else:
        print('[Seed] Menu items already exist — skipping.')

    print('[Seed] Database seeding complete.')
