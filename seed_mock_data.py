import os
import json
import random
import datetime
from datetime import datetime as dt, timedelta
from app import create_app
from models import db
from models.user import User
from models.order import Order
from models.booking import Booking
from models.menu import Menu
from models import bcrypt

app = create_app('dev')

with app.app_context():
    # Make sure we have the menu items
    menu_items = Menu.query.all()
    if not menu_items:
        print("Please seed menu first using seed_menu.py!")
        exit(1)
        
    # Find or create users
    admin_user = User.query.filter_by(email='admin@cafe.com').first()
    if not admin_user:
        hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(name='System Admin', email='admin@cafe.com', password_hash=hashed, role='Admin')
        db.session.add(admin_user)
        
    staff_user = User.query.filter_by(email='staff@cafe.com').first()
    if not staff_user:
        hashed = bcrypt.generate_password_hash('staff123').decode('utf-8')
        staff_user = User(name='Staff Member', email='staff@cafe.com', password_hash=hashed, role='Customer', phone='+919999999999')
        db.session.add(staff_user)
    else:
        staff_user.phone = '+919999999999'
        
    db.session.commit()
    
    # Generate mock customers
    customer_users = []
    for i in range(1, 11):
        email = f"customer{i}@example.com"
        u = User.query.filter_by(email=email).first()
        phone = f"+9198765432{i-1:02d}"
        if not u:
            hashed = bcrypt.generate_password_hash('password123').decode('utf-8')
            u = User(name=f"Customer {i}", email=email, password_hash=hashed, role='Customer', phone=phone)
            db.session.add(u)
            customer_users.append(u)
        else:
            u.phone = phone
            customer_users.append(u)
            
    db.session.commit()
    
    # Remove existing orders and bookings for mock data
    db.session.query(Order).delete()
    db.session.query(Booking).delete()
    db.session.commit()
    
    # Generate mock orders and bookings for the past 30 days
    now = dt.utcnow()
    print("Generating mock data for the past 30 days...")
    
    all_users = [staff_user] + customer_users
    
    for day_offset in range(30, -1, -1):
        target_date = now - timedelta(days=day_offset)
        # Random number of orders per day
        num_orders = random.randint(3, 12) if day_offset > 0 else random.randint(6, 14)
        
        for _ in range(num_orders):
            user = random.choice(all_users)
            order_items = []
            total_amount = 0
            for _ in range(random.randint(1, 4)):
                item = random.choice(menu_items)
                qty = random.randint(1, 3)
                exists = next((x for x in order_items if x['menu_item_id'] == item.item_id), None)
                if exists:
                    exists['quantity'] += qty
                else:
                    order_items.append({
                        'menu_item_id': item.item_id,
                        'name': item.name,
                        'price': item.price,
                        'quantity': qty
                    })
                total_amount += item.price * qty
                
            order_time = dt(
                target_date.year, target_date.month, target_date.day,
                random.randint(9, 21), random.randint(0, 59), random.randint(0, 59)
            )
            
            status = 'Completed' if day_offset > 0 else random.choice(['Completed', 'Received', 'Processing'])
            
            o = Order(
                user_id=user.id,
                items=json.dumps(order_items),
                amount=total_amount,
                status=status,
                created_at=order_time
            )
            db.session.add(o)
            
        num_bookings = random.randint(1, 5)
        for _ in range(num_bookings):
            user = random.choice(all_users)
            booking_date = target_date.date()
            booking_time = datetime.time(hour=random.randint(9, 21), minute=0)
            b = Booking(
                user_id=user.id,
                date=booking_date,
                time=booking_time,
                guests=random.randint(1, 6),
                seat_type=random.choice(['Window Seating', 'Coffee Bar seating', 'Quiet Corner Tables', 'Center Tables', 'Outdoor Seating']),
                created_at=target_date
            )
            db.session.add(b)
            
    db.session.commit()
    print("Mock data successfully seeded!")
