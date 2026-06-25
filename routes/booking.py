"""
Booking routes blueprint for HRD Café.
Handles table/workspace booking functionality.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from services.booking_service import BookingService

booking_bp = Blueprint('booking', __name__)

TIME_SLOTS = [
    '09:00', '10:00', '11:00', '12:00', '13:00',
    '14:00', '15:00', '16:00', '17:00', '18:00',
    '19:00', '20:00', '21:00'
]

SEAT_TYPES = [
    ('standard', 'Standard'),
    ('ai_workspace', 'AI Workspace'),
    ('meeting_pod', 'Meeting Pod'),
    ('private_cabin', 'Private Cabin')
]


@booking_bp.route('/booking', methods=['GET'])
def booking_page():
    """Render the booking form page."""
    return render_template(
        'booking.html',
        time_slots=TIME_SLOTS,
        seat_types=SEAT_TYPES
    )


@booking_bp.route('/booking', methods=['POST'])
@login_required
def create_booking():
    """Handle booking form submission."""
    date = request.form.get('date', '').strip()
    time_slot = request.form.get('time_slot', '').strip()
    guests = request.form.get('guests', '1').strip()
    seat_type = request.form.get('seat_type', 'standard').strip()
    special_requests = request.form.get('special_requests', '').strip()

    # Validate required fields
    if not date:
        flash('Please select a date for your booking.', 'error')
        return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)

    if not time_slot:
        flash('Please select a time slot.', 'error')
        return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)

    if time_slot not in TIME_SLOTS:
        flash('Invalid time slot selected.', 'error')
        return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)

    valid_seat_codes = [s[0] for s in SEAT_TYPES]
    if seat_type not in valid_seat_codes:
        flash('Invalid seat type selected.', 'error')
        return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)

    try:
        guests = int(guests)
        if guests < 1 or guests > 20:
            flash('Number of guests must be between 1 and 20.', 'error')
            return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)
    except ValueError:
        flash('Invalid number of guests.', 'error')
        return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)

    try:
        booking_service = BookingService()
        booking = booking_service.create_booking(
            user_id=current_user.id,
            date=date,
            time_slot=time_slot,
            guests=guests,
            seat_type=seat_type,
            special_requests=special_requests
        )

        flash(
            f'Booking confirmed! Your booking ID is {booking.booking_id}. '
            f'We look forward to seeing you!',
            'success'
        )
        return redirect(url_for('dashboard.dashboard'))

    except Exception as e:
        flash(f'An error occurred while creating your booking: {str(e)}', 'error')
        return render_template('booking.html', time_slots=TIME_SLOTS, seat_types=SEAT_TYPES)
