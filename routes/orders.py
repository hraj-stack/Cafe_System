"""
Orders routes blueprint for HRD Café.
Handles order placement and order tracking.
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db
from models.order import Order
from models.menu import Menu
from models.booking import Booking
import json

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders/place', methods=['POST'])
@login_required
def place_order():
    """Place a new order from cart items (JSON endpoint)."""
    try:
        data = request.get_json()

        if not data or 'items' not in data:
            return jsonify({
                'success': False,
                'message': 'No items provided in the order.'
            }), 400

        cart_items = data['items']

        if not cart_items or len(cart_items) == 0:
            return jsonify({
                'success': False,
                'message': 'Cart is empty. Please add items to your cart.'
            }), 400

        # Validate each cart item and calculate total
        total_amount = 0.0
        validated_items = []
        
        for item in cart_items:
            if 'menu_item_id' not in item or 'quantity' not in item:
                return jsonify({
                    'success': False,
                    'message': 'Each item must have menu_item_id and quantity.'
                }), 400

            try:
                menu_item_id = int(item['menu_item_id'])
                quantity = int(item['quantity'])
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Invalid menu_item_id or quantity format.'
                }), 400

            if quantity < 1:
                return jsonify({
                    'success': False,
                    'message': 'Quantity must be at least 1.'
                }), 400

            menu_item = Menu.query.get(menu_item_id)
            if not menu_item:
                return jsonify({
                    'success': False,
                    'message': f'Menu item with ID {menu_item_id} not found.'
                }), 400

            total_amount += menu_item.price * quantity
            validated_items.append({
                'menu_item_id': menu_item_id,
                'name': menu_item.name,
                'price': menu_item.price,
                'quantity': quantity
            })

        # Create the order
        new_order = Order(
            user_id=current_user.id,
            items=json.dumps(validated_items),
            amount=total_amount,
            status='Pending'
        )
        db.session.add(new_order)

        # Award loyalty points (1 point for every ₹100 spent, minimum 10 points)
        points_earned = max(10, int(total_amount // 100))
        current_user.loyalty_points = (current_user.loyalty_points or 0) + points_earned
        db.session.commit()

        # Save order ID in session for dashboard toast notification
        from flask import session
        session['new_order_id'] = new_order.order_id

        return jsonify({
            'success': True,
            'message': 'Order placed successfully!',
            'order_id': new_order.order_id,
            'total_amount': float(new_order.amount),
            'loyalty_points_earned': 10,
            'total_loyalty_points': current_user.loyalty_points
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred while placing your order: {str(e)}'
        }), 500


@orders_bp.route('/orders/track')
@login_required
def track_orders():
    """Render order tracking page with user's orders and bookings."""
    try:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date.desc()).all()
    except Exception:
        orders = []
        bookings = []

    return render_template(
        'order_tracking.html',
        orders=orders,
        bookings=bookings
    )
