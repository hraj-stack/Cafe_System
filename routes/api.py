"""
REST API routes blueprint for HRD Café.
Provides JSON endpoints for menu, availability, order status, and demand prediction.
"""

from flask import Blueprint, request, jsonify
from models.menu_item import MenuItem
from models.order import Order
from services.booking_service import BookingService

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/menu', methods=['GET'])
def get_menu():
    """Return all available menu items as JSON."""
    try:
        category = request.args.get('category')

        query = MenuItem.query.filter_by(available=True)
        if category:
            query = query.filter_by(category=category)

        items = query.order_by(MenuItem.category, MenuItem.name).all()

        menu_data = []
        for item in items:
            menu_data.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'sub_category': item.sub_category,
                'description': item.description,
                'price': float(item.price),
                'image_url': item.image_url,
                'available': item.available
            })

        return jsonify({
            'success': True,
            'count': len(menu_data),
            'items': menu_data
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching menu: {str(e)}'
        }), 500


@api_bp.route('/availability', methods=['GET'])
def check_availability():
    """Check seat availability for a given date, time slot, and seat type."""
    try:
        date_str = request.args.get('date')
        time_slot = request.args.get('time_slot')
        seat_type = request.args.get('seat_type')

        if not date_str or not time_slot or not seat_type:
            return jsonify({
                'success': False,
                'message': 'date, time_slot, and seat_type parameters are required.'
            }), 400

        booking_service = BookingService()
        availability = booking_service.check_availability(
            date=date_str,
            time_slot=time_slot,
            seat_type=seat_type
        )

        return jsonify({
            'success': True,
            'date': date_str,
            'time_slot': time_slot,
            'seat_type': seat_type,
            'available_count': availability
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error checking availability: {str(e)}'
        }), 500


@api_bp.route('/order/<order_id>/status', methods=['GET'])
def get_order_status(order_id):
    """Return the current status of an order."""
    try:
        order = Order.query.filter_by(order_id=order_id).first()

        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found.'
            }), 404

        return jsonify({
            'success': True,
            'order_id': order.order_id,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching order status: {str(e)}'
        }), 500


@api_bp.route('/predict', methods=['POST'])
def predict_demand():
    """Generate a demand prediction for a given day and hour."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required.'
            }), 400

        day_of_week = data.get('day_of_week')
        hour = data.get('hour')
        weather_code = data.get('weather_code', 0)

        if day_of_week is None or hour is None:
            return jsonify({
                'success': False,
                'message': 'day_of_week and hour are required.'
            }), 400

        try:
            day_of_week = int(day_of_week)
            hour = int(hour)
            weather_code = int(weather_code)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'day_of_week, hour, and weather_code must be integers.'
            }), 400

        if not (0 <= day_of_week <= 6):
            return jsonify({
                'success': False,
                'message': 'day_of_week must be between 0 (Monday) and 6 (Sunday).'
            }), 400

        if not (0 <= hour <= 23):
            return jsonify({
                'success': False,
                'message': 'hour must be between 0 and 23.'
            }), 400

        from ml.demand_predictor import DemandPredictor
        predictor = DemandPredictor()
        prediction = predictor.predict(
            day_of_week=day_of_week,
            hour=hour,
            weather_code=weather_code
        )

        return jsonify({
            'success': True,
            'prediction': {
                'day_of_week': day_of_week,
                'hour': hour,
                'weather_code': weather_code,
                'expected_customers': prediction.get('expected_customers', 0),
                'expected_orders': prediction.get('expected_orders', 0),
                'inventory_alert': prediction.get('inventory_alert', '')
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating prediction: {str(e)}'
        }), 500
