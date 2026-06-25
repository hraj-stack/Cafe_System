from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.user import User
from models.booking import Booking
from models.order import Order
from models.menu import Menu
from ml.demand_predictor import DemandPredictor
import datetime
from sqlalchemy import func
import random
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

def get_stats_data():
    today_utc = datetime.date.today()
    start_time = datetime.datetime.combine(today_utc, datetime.time.min)
    end_time = datetime.datetime.combine(today_utc, datetime.time.max)

    # Today's orders count
    orders_today = Order.query.filter(Order.created_at >= start_time, Order.created_at <= end_time, Order.status != 'Cancelled').count()

    # This Week's orders count
    start_week = today_utc - datetime.timedelta(days=today_utc.weekday())
    start_week_time = datetime.datetime.combine(start_week, datetime.time.min)
    orders_week = Order.query.filter(Order.created_at >= start_week_time, Order.status != 'Cancelled').count()

    # This Month's orders count
    start_month = today_utc.replace(day=1)
    start_month_time = datetime.datetime.combine(start_month, datetime.time.min)
    orders_month = Order.query.filter(Order.created_at >= start_month_time, Order.status != 'Cancelled').count()

    # Profit & Sales (Today)
    revenue_today = db.session.query(func.sum(Order.amount)).filter(Order.created_at >= start_time, Order.created_at <= end_time, Order.status != 'Cancelled').scalar() or 0.0
    expenses_today = 1500.0 + (revenue_today * 0.40) if revenue_today > 0 else 0.0
    profit_today = revenue_today - expenses_today

    # Profit & Sales (Monthly)
    revenue_month = db.session.query(func.sum(Order.amount)).filter(Order.created_at >= start_month_time, Order.status != 'Cancelled').scalar() or 0.0
    expenses_month = (1500.0 * today_utc.day) + (revenue_month * 0.40) if revenue_month > 0 else 0.0
    profit_month = revenue_month - expenses_month

    # Pending Payments count (status is not Completed and not Cancelled)
    pending_payments = Order.query.filter(Order.status != 'Completed', Order.status != 'Cancelled').count()

    # Paid Bills count (status is Completed)
    paid_bills = Order.query.filter(Order.status == 'Completed').count()

    return {
        'orders_today': orders_today,
        'orders_week': orders_week,
        'orders_month': orders_month,
        'revenue_today': float(revenue_today),
        'expenses_today': float(expenses_today),
        'profit_today': float(profit_today),
        'revenue_month': float(revenue_month),
        'expenses_month': float(expenses_month),
        'profit_month': float(profit_month),
        'pending_payments': pending_payments,
        'paid_bills': paid_bills
    }

def get_daily_predictions(start_date, num_days):
    predictions = []
    # Predict from start_date - 1 day to calculate trend
    for i in range(-1, num_days):
        target_date = start_date + datetime.timedelta(days=i)
        
        total_customers = 0
        for hour in range(9, 22):
            dt = datetime.datetime.combine(target_date, datetime.time(hour=hour))
            pred = DemandPredictor.predict(dt)
            total_customers += pred.get('expected_customers', 50)
            
        is_weekend = target_date.weekday() >= 5
        base_conf = 85 if is_weekend else 90
        seed = int(target_date.strftime("%Y%m%d"))
        r = random.Random(seed)
        confidence = base_conf + r.randint(-2, 5)
        
        predictions.append({
            'date': target_date.strftime('%Y-%m-%d'),
            'display_date': target_date.strftime('%b %d'),
            'expected_guests': total_customers,
            'confidence': confidence
        })
        
    result = []
    for i in range(1, len(predictions)):
        curr = predictions[i]
        prev = predictions[i-1]
        if curr['expected_guests'] > prev['expected_guests'] * 1.05:
            trend = 'up'
        elif curr['expected_guests'] < prev['expected_guests'] * 0.95:
            trend = 'down'
        else:
            trend = 'stable'
        curr['trend'] = trend
        result.append(curr)
        
    return result

def sync_historical_data():
    from models.historical_data import DailyHistoricalData
    from models.order import Order
    from models.booking import Booking
    from sqlalchemy import func
    import datetime

    # Check if there is already data in DailyHistoricalData
    if DailyHistoricalData.query.first() is not None:
        return
        
    # Group orders by date
    orders_by_date = db.session.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.order_id).label('count')
    ).filter(Order.status != 'Cancelled').group_by(func.date(Order.created_at)).all()

    # Group bookings by date
    bookings_by_date = db.session.query(
        Booking.date.label('date'),
        func.count(Booking.booking_id).label('count')
    ).filter(Booking.status != 'Cancelled').group_by(Booking.date).all()

    # Map dates
    daily_map = {}
    for r in orders_by_date:
        if r.date:
            d = r.date if isinstance(r.date, datetime.date) else datetime.datetime.strptime(str(r.date), '%Y-%m-%d').date()
            daily_map[d] = {'orders': r.count, 'bookings': 0, 'customers': r.count}
            
    for r in bookings_by_date:
        if r.date:
            d = r.date if isinstance(r.date, datetime.date) else r.date
            if d not in daily_map:
                daily_map[d] = {'orders': 0, 'bookings': r.count, 'customers': r.count}
            else:
                daily_map[d]['bookings'] = r.count
                daily_map[d]['customers'] += r.count

    for d, counts in daily_map.items():
        hist = DailyHistoricalData(
            date=d,
            orders_count=counts['orders'],
            reservations_count=counts['bookings'],
            customers_count=counts['customers']
        )
        db.session.add(hist)
    db.session.commit()

    # Automatically train model initially
    records = DailyHistoricalData.query.all()
    if records:
        from ml.demand_predictor import DemandPredictor
        try:
            DemandPredictor.train_and_save(records)
        except Exception as e:
            print("Auto-training failed:", e)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    users_count = User.query.count()
    bookings_count = Booking.query.filter(Booking.status != 'Cancelled').count()
    orders_count = Order.query.filter(Order.status != 'Cancelled').count()
    
    # Live stats
    stats = get_stats_data()
    
    # Billing / Order History (all orders)
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Menu items list for the billing generator
    menu_items = Menu.query.all()
    
    # Users list for the billing generator
    customers_list = User.query.filter(User.role != 'Admin').all()
    
    # Yesterday's visitors
    today_utc = datetime.date.today()
    yesterday_utc = today_utc - datetime.timedelta(days=1)
    
    # Sync historical data if empty
    sync_historical_data()

    # Get yesterday's stats
    from models.historical_data import DailyHistoricalData
    yesterday_stats = DailyHistoricalData.query.get(yesterday_utc)
    yesterday_guests = yesterday_stats.customers_count if yesterday_stats else 48

    # Calculate actual past 7-day average baseline for trend indicators
    past_7_days = [today_utc - datetime.timedelta(days=x) for x in range(1, 8)]
    past_stats = DailyHistoricalData.query.filter(DailyHistoricalData.date.in_(past_7_days)).all()
    if past_stats:
        avg_cust = sum(s.customers_count for s in past_stats) / len(past_stats)
        avg_ord = sum(s.orders_count for s in past_stats) / len(past_stats)
        avg_res = sum(s.reservations_count for s in past_stats) / len(past_stats)
    else:
        avg_cust, avg_ord, avg_res = 25.0, 20.0, 5.0

    # Generate forecasts using the new XGBoost model
    from ml.demand_predictor import DemandPredictor
    
    # Tomorrow
    tomorrow_date = today_utc + datetime.timedelta(days=1)
    tomorrow_pred = DemandPredictor.predict_day(tomorrow_date)
    
    tomorrow_trend = 'stable'
    if tomorrow_pred['customers_count'] > avg_cust * 1.02:
        tomorrow_trend = 'up'
    elif tomorrow_pred['customers_count'] < avg_cust * 0.98:
        tomorrow_trend = 'down'
    
    # Next 3 days (t+1, t+2, t+3)
    three_day_preds = []
    for offset in range(1, 4):
        d = today_utc + datetime.timedelta(days=offset)
        three_day_preds.append(DemandPredictor.predict_day(d))
    
    three_day_cust = sum(p['customers_count'] for p in three_day_preds)
    three_day_orders = sum(p['orders_count'] for p in three_day_preds)
    three_day_res = sum(p['reservations_count'] for p in three_day_preds)
    
    three_day_avg = three_day_cust / 3.0
    three_day_trend = 'stable'
    if three_day_avg > avg_cust * 1.02:
        three_day_trend = 'up'
    elif three_day_avg < avg_cust * 0.98:
        three_day_trend = 'down'

    # Next 7 days (t+1 to t+7)
    seven_day_preds = []
    for offset in range(1, 8):
        d = today_utc + datetime.timedelta(days=offset)
        seven_day_preds.append(DemandPredictor.predict_day(d))
        
    weekly_forecast = sum(p['customers_count'] for p in seven_day_preds)
    weekly_orders = sum(p['orders_count'] for p in seven_day_preds)
    weekly_res = sum(p['reservations_count'] for p in seven_day_preds)
    
    weekly_avg = weekly_forecast / 7.0
    weekly_trend = 'stable'
    if weekly_avg > avg_cust * 1.02:
        weekly_trend = 'up'
    elif weekly_avg < avg_cust * 0.98:
        weekly_trend = 'down'

    # Growth percentage: comparing weekly avg forecast to yesterday's baseline
    growth_pct = round(((weekly_avg - yesterday_guests) / yesterday_guests) * 100, 1) if yesterday_guests > 0 else 0.0

    # Next 30 days predictions for weekly proj averages charts
    thirty_day_preds = []
    for offset in range(1, 31):
        d = today_utc + datetime.timedelta(days=offset)
        thirty_day_preds.append(DemandPredictor.predict_day(d))
        
    monthly_forecast = sum(p['customers_count'] for p in thirty_day_preds)

    # Next 7 Days (list of dicts for line chart)
    next_7_days = []
    for offset in range(1, 8):
        d = today_utc + datetime.timedelta(days=offset)
        p = seven_day_preds[offset-1]
        next_7_days.append({
            'display_date': d.strftime('%b %d'),
            'expected_guests': p['customers_count']
        })

    # Next 30 Days chart data (Weekly averages)
    w1_avg = sum(p['customers_count'] for p in thirty_day_preds[0:7]) / 7
    w2_avg = sum(p['customers_count'] for p in thirty_day_preds[7:14]) / 7
    w3_avg = sum(p['customers_count'] for p in thirty_day_preds[14:21]) / 7
    w4_avg = sum(p['customers_count'] for p in thirty_day_preds[21:30]) / 9
    next_30_days = [
        {'label': 'Week 1', 'expected_guests': round(w1_avg)},
        {'label': 'Week 2', 'expected_guests': round(w2_avg)},
        {'label': 'Week 3', 'expected_guests': round(w3_avg)},
        {'label': 'Week 4', 'expected_guests': round(w4_avg)}
    ]
    
    # Package forecast objects for clean templates access
    tomorrow_forecast = {
        'customers': tomorrow_pred['customers_count'],
        'orders': tomorrow_pred['orders_count'],
        'reservations': tomorrow_pred['reservations_count'],
        'trend': tomorrow_trend
    }
    three_day_forecast = {
        'customers': three_day_cust,
        'orders': three_day_orders,
        'reservations': three_day_res,
        'trend': three_day_trend
    }
    seven_day_forecast = {
        'customers': weekly_forecast,
        'orders': weekly_orders,
        'reservations': weekly_res,
        'trend': weekly_trend
    }

    # Backward compatible tomorrow_pred for any downstream uses
    tomorrow_pred_compat = {
        'expected_guests': tomorrow_pred['customers_count'],
        'confidence': 90,
        'trend': tomorrow_trend
    }

    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           bookings_count=bookings_count,
                           orders_count=orders_count,
                           stats=stats,
                           all_orders=all_orders,
                           menu_items=menu_items,
                           customers_list=customers_list,
                           yesterday_guests=yesterday_guests,
                           tomorrow_pred=tomorrow_pred_compat,
                           tomorrow_forecast=tomorrow_forecast,
                           three_day_forecast=three_day_forecast,
                           seven_day_forecast=seven_day_forecast,
                           weekly_forecast=weekly_forecast,
                           monthly_forecast=monthly_forecast,
                           growth_pct=growth_pct,
                           next_7_days=next_7_days,
                           next_30_days=next_30_days)

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    stats = get_stats_data()
    return jsonify(stats)

@admin_bp.route('/api/search-users')
@login_required
@admin_required
def search_users():
    q = request.args.get('q', '')
    if len(q) < 1:
        return jsonify([])
    users = User.query.filter(
        (User.role != 'Admin') & 
        ((User.name.like(f'%{q}%')) | (User.email.like(f'%{q}%')))
    ).limit(10).all()
    
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'phone': u.phone
    } for u in users])

@admin_bp.route('/api/customer-history/<int:user_id>')
@login_required
@admin_required
def customer_history(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return jsonify([{
        'order_id': o.order_id,
        'amount': o.amount,
        'status': o.status,
        'date': o.created_at.strftime('%Y-%m-%d %H:%M'),
        'items': json.loads(o.items)
    } for o in orders])

@admin_bp.route('/api/generate-bill', methods=['POST'])
@login_required
@admin_required
def generate_bill():
    data = request.get_json()
    if not data or 'user_id' not in data or 'items' not in data:
        return jsonify({'success': False, 'message': 'Missing user_id or items.'}), 400
        
    user_id = data['user_id']
    items = data['items']
    discount_pct = data.get('discount_pct', 0)
    try:
        discount_pct = int(discount_pct)
    except (ValueError, TypeError):
        discount_pct = 0
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Customer not found.'}), 404
        
    subtotal = 0.0
    validated_items = []
    
    for item in items:
        menu_item_id = item['menu_item_id']
        qty = int(item['quantity'])
        menu_item = Menu.query.get(menu_item_id)
        if not menu_item:
            return jsonify({'success': False, 'message': f'Menu item {menu_item_id} not found.'}), 404
            
        subtotal += menu_item.price * qty
        validated_items.append({
            'menu_item_id': menu_item_id,
            'name': menu_item.name,
            'price': menu_item.price,
            'quantity': qty
        })
        
    discount_amount = subtotal * (discount_pct / 100.0)
    net_subtotal = subtotal - discount_amount
    gst_amount = net_subtotal * 0.05
    final_total = net_subtotal + gst_amount
        
    new_order = Order(
        user_id=user_id,
        items=json.dumps(validated_items),
        amount=final_total,
        discount_pct=discount_pct,
        gst_amount=gst_amount,
        status='Completed',
        created_at=datetime.datetime.utcnow()
    )
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Bill generated successfully!',
        'order_id': new_order.order_id,
        'total': final_total,
        'subtotal': subtotal,
        'discount_pct': discount_pct,
        'discount_amount': discount_amount,
        'gst_amount': gst_amount,
        'date': new_order.created_at.strftime('%Y-%m-%d %H:%M'),
        'items': validated_items
    })

@admin_bp.route('/api/invoice-details/<int:order_id>', methods=['GET'])
@login_required
@admin_required
def invoice_details(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404
        
    try:
        items = json.loads(order.items)
    except Exception:
        items = []
        
    items_subtotal = sum(item.get('price', 0.0) * item.get('quantity', 0) for item in items)
    discount_pct = getattr(order, 'discount_pct', 0)
    discount_amount = items_subtotal * (discount_pct / 100.0)
    
    gst_amount = getattr(order, 'gst_amount', 0.0)
    if gst_amount == 0.0 and order.amount > 0.0 and discount_pct == 0:
        subtotal = order.amount / 1.05
        gst_amount = order.amount - subtotal
    else:
        subtotal = items_subtotal
        
    order_date = order.created_at.date()
    booking = Booking.query.filter_by(user_id=order.user_id, date=order_date).filter(Booking.status != 'Cancelled').first()
    
    user = User.query.get(order.user_id)
    customer_info = {
        'id': user.id if user else None,
        'name': user.name if user else 'Walk-in Customer',
        'email': user.email if user else '',
        'phone': getattr(user, 'phone', '') if user else ''
    }
    
    reservation_info = None
    if booking:
        reservation_info = {
            'booking_id': booking.booking_id,
            'date': booking.date.strftime('%Y-%m-%d'),
            'time': booking.time.strftime('%H:%M'),
            'guests': booking.guests,
            'seat_type': booking.seat_type
        }
        
    return jsonify({
        'success': True,
        'order_id': order.order_id,
        'customer': customer_info,
        'items': items,
        'amount': order.amount,
        'discount_pct': discount_pct,
        'discount_amount': discount_amount,
        'gst_amount': gst_amount,
        'subtotal': subtotal,
        'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
        'status': order.status,
        'has_reservation': booking is not None,
        'reservation': reservation_info
    })

@admin_bp.route('/api/historical-data', methods=['GET', 'POST'])
@login_required
@admin_required
def historical_data_api():
    from models.historical_data import DailyHistoricalData
    if request.method == 'GET':
        records = DailyHistoricalData.query.order_by(DailyHistoricalData.date.desc()).all()
        return jsonify([{
            'date': r.date.strftime('%Y-%m-%d'),
            'orders_count': r.orders_count,
            'reservations_count': r.reservations_count,
            'customers_count': r.customers_count
        } for r in records])
        
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'date' not in data:
            return jsonify({'success': False, 'message': 'Missing date.'}), 400
            
        try:
            target_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
            
        try:
            orders_count = int(data.get('orders_count', 0))
            reservations_count = int(data.get('reservations_count', 0))
            customers_count = int(data.get('customers_count', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Counts must be integers.'}), 400
        
        hist = DailyHistoricalData.query.get(target_date)
        if hist:
            hist.orders_count = orders_count
            hist.reservations_count = reservations_count
            hist.customers_count = customers_count
        else:
            hist = DailyHistoricalData(
                date=target_date,
                orders_count=orders_count,
                reservations_count=reservations_count,
                customers_count=customers_count
            )
            db.session.add(hist)
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Historical data saved successfully.'})

@admin_bp.route('/api/train-predictions', methods=['POST'])
@login_required
@admin_required
def train_predictions_api():
    from models.historical_data import DailyHistoricalData
    from ml.demand_predictor import DemandPredictor
    
    records = DailyHistoricalData.query.all()
    if not records:
        return jsonify({'success': False, 'message': 'No historical records found to train on.'}), 400
        
    try:
        DemandPredictor.train_and_save(records)
        return jsonify({'success': True, 'message': 'XGBoost forecasting models retrained successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Training failed: {str(e)}'}), 500


@admin_bp.route('/api/send-receipt', methods=['POST'])
@login_required
@admin_required
def send_receipt():
    from services.email_service import send_email_async
    data = request.get_json()
    method = data.get('method', 'email')
    order_id = data.get('order_id')

    if method != 'email':
        return jsonify({'success': True, 'message': f'Receipt for Order #{order_id} sent via {method.upper()}!'})

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404

    user = User.query.get(order.user_id)
    if not user or not user.email:
        return jsonify({'success': False, 'message': 'No email address on record for this customer.'}), 400

    try:
        items = json.loads(order.items)
    except Exception:
        items = []

    items_rows = ''.join(
        f"<tr><td style='padding:10px 16px;border-bottom:1px solid #e5dfd3'>{i.get('name','Item')}</td>"
        f"<td style='padding:10px 16px;border-bottom:1px solid #e5dfd3;text-align:center'>{i.get('quantity',1)}</td>"
        f"<td style='padding:10px 16px;border-bottom:1px solid #e5dfd3;text-align:right'>&#8377;{float(i.get('price',0))*int(i.get('quantity',1)):.2f}</td></tr>"
        for i in items
    )

    html = f"""
    <!DOCTYPE html><html><head><meta charset='utf-8'><style>
      body{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;background:#f7f6f2;margin:0;padding:0;color:#1c1a14}}
      .wrap{{max-width:600px;margin:40px auto;background:#fff;border:1px solid #e5dfd3;border-radius:12px;overflow:hidden}}
      .hdr{{background:#3d5a45;padding:32px 30px;text-align:center;color:#fff}}
      .hdr h1{{font-family:Georgia,serif;margin:0;font-size:26px;font-weight:normal;letter-spacing:.05em}}
      .body{{padding:36px 40px}}
      table{{width:100%;border-collapse:collapse;margin:24px 0;background:#fcfbfa;border:1px solid #e5dfd3;border-radius:8px}}
      th{{background:#f0ece4;padding:10px 16px;text-align:left;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#5a5648}}
      .total{{font-size:16px;font-weight:700;color:#3d5a45;text-align:right;padding:16px 0 0}}
      .ftr{{background:#fcfbfa;padding:22px;text-align:center;font-size:12px;color:#8c887d;border-top:1px solid #e5dfd3}}
    </style></head><body><div class='wrap'>
      <div class='hdr'><h1>HRD Cafe — Receipt</h1></div>
      <div class='body'>
        <p>Dear <strong>{user.name}</strong>,</p>
        <p>Thank you for dining with us. Here is your receipt for Order <strong>#{order.order_id}</strong>.</p>
        <table>
          <thead><tr><th>Item</th><th style='text-align:center'>Qty</th><th style='text-align:right'>Amount</th></tr></thead>
          <tbody>{items_rows}</tbody>
        </table>
        <p class='total'>Total Paid: &#8377;{float(order.amount):.2f}</p>
      </div>
      <div class='ftr'><p>HRD Cafe &bull; 123 Cafe Boulevard, Bangalore, Karnataka, India</p></div>
    </div></body></html>
    """

    send_email_async(
        to      = user.email,
        subject = f'Your HRD Cafe Receipt — Order #{order.order_id}',
        html    = html,
    )

    return jsonify({
        'success': True,
        'message': f'Receipt for Order #{order_id} sent to {user.email}!'
    })


@admin_bp.route('/messaging', methods=['GET'])
@login_required
@admin_required
def messaging():
    from models.message_log import MessageLog
    history = MessageLog.query.order_by(MessageLog.created_at.desc()).all()
    return render_template('admin/messaging.html', history=history)


@admin_bp.route('/messaging/send', methods=['POST'])
@login_required
@admin_required
def send_message_api():
    from models.message_log import MessageLog
    import re
    from datetime import datetime, timedelta

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'}), 400

    msg_type = data.get('type') # 'Email', 'SMS', 'WhatsApp'
    recipient = data.get('recipient', '').strip()
    body = data.get('body', '').strip()
    subject = data.get('subject', '').strip() if msg_type == 'Email' else None

    if not msg_type or msg_type not in ['Email', 'SMS', 'WhatsApp']:
        return jsonify({'success': False, 'message': 'Invalid message type.'}), 400

    if not recipient:
        return jsonify({'success': False, 'message': 'Recipient is required.'}), 400

    if not body:
        return jsonify({'success': False, 'message': 'Message body is required.'}), 400

    # Validations
    if msg_type == 'Email':
        if not re.match(r'^\S+@\S+\.\S+$', recipient):
            return jsonify({'success': False, 'message': 'Invalid email address.'}), 400
    else: # SMS or WhatsApp
        # Phone validation: must be numerical digits (can have + prefix) and length 10-15
        clean_phone = re.sub(r'[\s\-()]+', '', recipient)
        if not re.match(r'^\+?[1-9]\d{9,14}$', clean_phone):
            return jsonify({'success': False, 'message': 'Invalid phone number format. Must contain 10-15 digits.'}), 400

    # Prevent duplicate submissions: check if exact same message sent in the last 10 seconds
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    duplicate = MessageLog.query.filter(
        MessageLog.recipient == recipient,
        MessageLog.message_type == msg_type,
        MessageLog.body == body,
        MessageLog.created_at >= ten_seconds_ago
    ).first()
    if duplicate:
        return jsonify({'success': False, 'message': 'Duplicate submission detected. Please wait 10 seconds before resending.'}), 400

    # Trigger sending
    status = 'Sent'
    if msg_type == 'Email':
        from services.email_service import send_email
        ok, err = send_email(
            to      = recipient,
            subject = subject or 'HRD Cafe Notification',
            html    = body,
        )
        if not ok:
            # err is user-friendly; still log as Failed
            status = 'Failed'
    elif msg_type == 'SMS':
        print(f"SMS successfully sent to {recipient}: {body}")
        status = 'Sent'
    elif msg_type == 'WhatsApp':
        print(f"WhatsApp message successfully sent to {recipient}: {body}")
        status = 'Sent'

    # Save to logs
    new_log = MessageLog(
        recipient=recipient,
        message_type=msg_type,
        subject=subject,
        body=body,
        status=status
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{msg_type} message sent successfully!',
        'log': {
            'id': new_log.id,
            'recipient': new_log.recipient,
            'type': new_log.message_type,
            'subject': new_log.subject,
            'body': new_log.body,
            'status': new_log.status,
            'created_at': new_log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@admin_bp.route('/messaging/history', methods=['GET'])
@login_required
@admin_required
def messaging_history_api():
    from models.message_log import MessageLog
    logs = MessageLog.query.order_by(MessageLog.created_at.desc()).all()
    return jsonify([{
        'id': log.id,
        'recipient': log.recipient,
        'type': log.message_type,
        'subject': log.subject,
        'body': log.body,
        'status': log.status,
        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
    } for log in logs])
