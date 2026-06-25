"""
Dashboard routes blueprint for HRD Café.
Handles the user dashboard with profile, bookings, orders, and recommendations.
"""

from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.booking import Booking
from models.order import Order
from models.recommendation import Recommendation

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the user dashboard with all relevant data."""
    today = date.today()

    try:
        # Upcoming bookings: not cancelled and date >= today
        upcoming_bookings = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.status != 'cancelled',
            Booking.date >= today
        ).order_by(Booking.date.asc(), Booking.time_slot.asc()).all()

        # Past bookings: date < today or cancelled
        past_bookings = Booking.query.filter(
            Booking.user_id == current_user.id,
            (Booking.date < today) | (Booking.status == 'cancelled')
        ).order_by(Booking.date.desc()).all()

    except Exception:
        upcoming_bookings = []
        past_bookings = []

    try:
        # Recent orders (last 10)
        recent_orders = Order.query.filter_by(
            user_id=current_user.id
        ).order_by(Order.created_at.desc()).limit(10).all()
    except Exception:
        recent_orders = []

    try:
        # Recommendation history (last 10)
        recommendation_history = Recommendation.query.filter_by(
            user_id=current_user.id
        ).order_by(Recommendation.created_at.desc()).limit(10).all()
    except Exception:
        recommendation_history = []

    return render_template(
        'dashboard.html',
        user=current_user,
        upcoming_bookings=upcoming_bookings,
        past_bookings=past_bookings,
        recent_orders=recent_orders,
        recommendation_history=recommendation_history,
        loyalty_points=current_user.loyalty_points or 0
    )
