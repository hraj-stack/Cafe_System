from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db
from models.booking import Booking
from models.order import Order
from datetime import datetime
import os
from services.email_service import send_email_async

customer_bp = Blueprint('customer', __name__)

def send_booking_email(booking, user):
    subject = f"HRD Reservation Confirmation — Table {booking.seat_type}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #f7f6f2;
                margin: 0;
                padding: 0;
                color: #1c1a14;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 40px auto;
                background: #ffffff;
                border: 1px solid #e5dfd3;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            }}
            .header {{
                background-color: #3d5a45;
                padding: 35px 30px;
                text-align: center;
                color: #ffffff;
            }}
            .header h1 {{
                font-family: 'Georgia', serif;
                margin: 0;
                font-size: 28px;
                font-weight: normal;
                letter-spacing: 0.05em;
            }}
            .content {{
                padding: 40px;
            }}
            .greeting {{
                font-size: 15px;
                line-height: 1.6;
                color: #2c2a24;
                margin-bottom: 24px;
            }}
            .details-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 24px 0;
                background-color: #fcfbfa;
                border: 1px solid #e5dfd3;
                border-radius: 8px;
            }}
            .details-table td {{
                padding: 14px 18px;
                border-bottom: 1px solid #e5dfd3;
                font-size: 14px;
            }}
            .details-table tr:last-child td {{
                border-bottom: none;
            }}
            .details-label {{
                font-weight: bold;
                color: #1c1a14;
                width: 35%;
            }}
            .details-value {{
                color: #3d5a45;
                font-weight: 600;
                text-align: right;
            }}
            .footer {{
                background-color: #fcfbfa;
                padding: 24px;
                text-align: center;
                font-size: 12px;
                color: #8c887d;
                border-top: 1px solid #e5dfd3;
            }}
            .button-container {{
                text-align: center;
                margin-top: 30px;
            }}
            .button {{
                display: inline-block;
                background-color: #1c1a14;
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                letter-spacing: 0.05em;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>HRD Cafe</h1>
            </div>
            <div class="content">
                <div class="greeting">
                    <p>Dear <strong>{user.name}</strong>,</p>
                    <p>Your table reservation at <strong>HRD</strong> has been successfully confirmed. We look forward to welcoming you.</p>
                </div>
                
                <table class="details-table">
                    <tr>
                        <td class="details-label">Date</td>
                        <td class="details-value">{booking.date.strftime('%A, %B %d, %Y')}</td>
                    </tr>
                    <tr>
                        <td class="details-label">Time Slot</td>
                        <td class="details-value">{booking.time.strftime('%I:%M %p')}</td>
                    </tr>
                    <tr>
                        <td class="details-label">Table Code</td>
                        <td class="details-value">Table {booking.seat_type}</td>
                    </tr>
                    <tr>
                        <td class="details-label">Guests Count</td>
                        <td class="details-value">{booking.guests} Guests</td>
                    </tr>
                </table>

                <div class="button-container">
                    <a href="http://localhost:5000/customer/dashboard" class="button">View Reservation</a>
                </div>
            </div>
            <div class="footer">
                <p>Thank you for choosing HRD Cafe.</p>
                <p style="margin-top: 6px;">123 Cafe Boulevard, Bangalore, Karnataka, India</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email_async(
        to      = user.email,
        subject = subject,
        html    = html_content,
    )

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter(Booking.user_id == current_user.id, Booking.status != 'Cancelled').order_by(Booking.date.desc()).all()
    orders = Order.query.filter(Order.user_id == current_user.id, Order.status != 'Cancelled').order_by(Order.created_at.desc()).all()
    
    # Calculate stats
    orders_placed = len(orders)
    reservations_made = len(bookings)
    total_spending = sum(o.amount for o in orders if o.status != 'Cancelled')
    
    item_counts = {}
    import json
    for o in orders:
        if o.status != 'Cancelled':
            try:
                items_list = json.loads(o.items)
                for item in items_list:
                    name = item.get('name')
                    qty = item.get('quantity', 0)
                    item_counts[name] = item_counts.get(name, 0) + qty
            except Exception:
                pass
    favorite_item = max(item_counts, key=item_counts.get) if item_counts else "None"

    # Check for newly created bookings and orders to show toasts
    from flask import session
    new_bookings = []
    new_booking_ids = session.pop('new_booking_ids', [])
    if new_booking_ids:
        new_bookings = Booking.query.filter(Booking.booking_id.in_(new_booking_ids)).all()
        
    new_order = None
    new_order_id = session.pop('new_order_id', None)
    if new_order_id:
        new_order = Order.query.get(new_order_id)
        
    return render_template('customer/dashboard.html', 
                           bookings=bookings, 
                           orders=orders, 
                           new_bookings=new_bookings,
                           new_order=new_order,
                           orders_placed=orders_placed,
                           reservations_made=reservations_made,
                           total_spending=total_spending,
                           favorite_item=favorite_item,
                           loyalty_points=current_user.loyalty_points or 0)

@customer_bp.route('/api/orders')
@login_required
def api_orders():
    sort_param = request.args.get('sort', 'latest')
    filter_param = request.args.get('filter', 'all')
    
    query = Order.query.filter(Order.user_id == current_user.id, Order.status != 'Cancelled')
    
    # Apply filtering
    if filter_param == 'current':
        query = query.filter(Order.status.in_(['Pending', 'Confirmed', 'Preparing', 'Ready', 'Received', 'Processing']))
    elif filter_param == 'past':
        query = query.filter(Order.status.in_(['Completed']))
        
    # Apply sorting
    if sort_param == 'oldest':
        query = query.order_by(Order.created_at.asc())
    else:
        query = query.order_by(Order.created_at.desc())
        
    orders = query.all()
    
    import json
    results = []
    for o in orders:
        items_list = []
        try:
            items_list = json.loads(o.items)
        except Exception:
            pass
            
        total_quantity = sum(item.get('quantity', 0) for item in items_list)
        
        results.append({
            'order_id': o.order_id,
            'date': o.created_at.strftime('%Y-%m-%d %H:%M'),
            'display_date': o.created_at.strftime('%B %d, %Y'),
            'amount': float(o.amount),
            'status': o.status,
            'items': items_list,
            'total_quantity': total_quantity
        })
        
    return jsonify(results)

@customer_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book_slot():
    if request.method == 'POST':
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        guests = int(request.form.get('guests'))
        seat_type = request.form.get('seat_type')
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            booking_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Simple check for existing booking (in a real app, check capacity)
            existing = Booking.query.filter_by(date=booking_date, time=booking_time, seat_type=seat_type).first()
            if existing:
                flash('This slot is already booked for that seat type. Please choose another.', 'warning')
                return redirect(url_for('customer.book_slot'))
                
            new_booking = Booking(
                user_id=current_user.id,
                date=booking_date,
                time=booking_time,
                guests=guests,
                seat_type=seat_type
            )
            db.session.add(new_booking)
            db.session.commit()
            
            # Send conformation mail
            send_booking_email(new_booking, current_user)
            
            # Store in session for toast notification
            from flask import session
            session_list = session.get('new_booking_ids', [])
            session_list.append(new_booking.booking_id)
            session['new_booking_ids'] = session_list
            session.modified = True
            
            flash('Booking confirmed successfully!', 'success')
            return redirect(url_for('customer.dashboard'))
            
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            
    return render_template('booking.html')

@customer_bp.route('/booked-tables')
@login_required
def booked_tables():
    date_str = request.args.get('date')
    time_str = request.args.get('time')
    if not date_str or not time_str:
        return jsonify({'booked_tables': []})
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        booking_time = datetime.strptime(time_str, '%H:%M').time()
        bookings = Booking.query.filter_by(date=booking_date, time=booking_time).all()
        return jsonify({'booked_tables': [b.seat_type for b in bookings if b.status != 'Cancelled']})
    except Exception as e:
        return jsonify({'booked_tables': [], 'error': str(e)})


@customer_bp.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404
        
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized action.'}), 403
        
    if order.status == 'Completed':
        return jsonify({'success': False, 'message': 'Completed orders cannot be cancelled.'}), 400
        
    if order.status == 'Cancelled':
        return jsonify({'success': False, 'message': 'Order is already cancelled.'}), 400
        
    order.status = 'Cancelled'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Order cancelled successfully!'})


@customer_bp.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_reservation(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Reservation not found.'}), 404
        
    if booking.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized action.'}), 403
        
    if booking.status == 'Cancelled':
        return jsonify({'success': False, 'message': 'Reservation is already cancelled.'}), 400
        
    booking.status = 'Cancelled'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Reservation cancelled successfully!'})
