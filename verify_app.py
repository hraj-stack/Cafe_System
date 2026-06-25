from app import create_app
from models import db
from models.user import User
from models.menu import Menu

app = create_app('dev')
client = app.test_client()

# Let's run test requests
print("Testing GET /")
resp = client.get('/')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert b'Login' in resp.data, "Login button not found in home page"
print("GET / passed!")

print("Testing GET /auth/login")
resp = client.get('/auth/login')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert b'autocomplete="username"' in resp.data, "Autofill username not found"
assert b'autocomplete="current-password"' in resp.data, "Autofill password not found"
print("GET /auth/login passed!")

# Simulate login using Flask-Login or by POSTing to /auth/login
print("Testing POST /auth/login as Admin")
resp = client.post('/auth/login', data={
    'email': 'admin@cafe.com',
    'password': 'admin123',
    'remember': 'on'
}, follow_redirects=True)
if b'Command Center' not in resp.data:
    print("STATUS:", resp.status_code)
    print("PATH:", resp.request.path)
    print("HEADERS:", resp.headers)
    body_str = resp.data.decode('utf-8', errors='ignore')
    if "Login Unsuccessful" in body_str:
        print("Flashed: Login Unsuccessful!")
    elif "Register" in body_str:
        print("Page seems to be registration/login page.")
    else:
        print("Body contains (first 500 chars):", body_str[:500].encode('ascii', errors='replace').decode('ascii'))
assert b'Command Center' in resp.data, "Did not redirect to Admin Dashboard or title not found"
print("Admin Login and Dashboard GET passed!")

print("Testing GET /admin/api/stats")
resp = client.get('/admin/api/stats')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
data = resp.get_json()
assert 'orders_today' in data, "orders_today not in stats response"
assert 'revenue_today' in data, "revenue_today not in stats response"
print("API stats passed!")

print("Testing GET /admin/api/search-users")
resp = client.get('/admin/api/search-users?q=customer')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
users = resp.get_json()
assert len(users) > 0, "No customer users returned"
customer = users[0]
print(f"User search passed! Found user: {customer}")

print("Testing GET /admin/api/customer-history/<id>")
resp = client.get(f"/admin/api/customer-history/{customer['id']}")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
history = resp.get_json()
print(f"Customer history passed! History count: {len(history)}")

print("Testing POST /admin/api/generate-bill")
with app.app_context():
    first_item = Menu.query.first()
    first_item_id = first_item.item_id if first_item else 1

resp = client.post('/admin/api/generate-bill', json={
    'user_id': customer['id'],
    'items': [
        {'menu_item_id': first_item_id, 'quantity': 2}
    ]
})
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}. Details: {resp.data.decode('utf-8', errors='ignore')}"
bill_data = resp.get_json()
assert bill_data['success'] is True, "Generate bill response was not success"
print(f"Generate bill passed! New order ID: {bill_data['order_id']}")

# Log out from Admin session
client.get('/auth/logout')

# Log in as Customer (staff@cafe.com)
print("Testing POST /auth/login as Customer")
resp = client.post('/auth/login', data={
    'email': 'staff@cafe.com',
    'password': 'staff123'
}, follow_redirects=True)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert b'Customer Portal' in resp.data, "Did not redirect to Customer Portal"
print("Customer Login passed!")

# Create a table booking
print("Testing POST /customer/book")
import datetime
tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# Clean up conflicting booking slot for testing reliability
with app.app_context():
    from models.booking import Booking
    tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_time = datetime.time(18, 0)
    Booking.query.filter_by(date=tomorrow_date, time=tomorrow_time, seat_type='O2').delete()
    db.session.commit()

resp = client.post('/customer/book', data={
    'date': tomorrow,
    'time': '18:00',
    'guests': '3',
    'seat_type': 'O2'
}, follow_redirects=True)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert b'Reservation Confirmed' in resp.data, "Toast header 'Reservation Confirmed' not found"
assert b'Hello <strong>Staff Member</strong>' in resp.data, "Toast greeting not found"
assert b'O2' in resp.data, "Toast table info not found"
print("Booking with Toast Notification passed!")

# Place a cafe order
print("Testing POST /orders/place")
resp = client.post('/orders/place', json={
    'items': [
        {'menu_item_id': first_item_id, 'quantity': 3}
    ]
})
assert resp.status_code == 201, f"Expected 201, got {resp.status_code}. Details: {resp.data.decode('utf-8', errors='ignore')}"
order_res = resp.get_json()
assert order_res['success'] is True
print("Place order API passed!")

# GET customer dashboard to check order toast
print("Testing GET /customer/dashboard for Order Toast")
resp = client.get('/customer/dashboard')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert b'Order Placed Successfully' in resp.data, "Toast header 'Order Placed Successfully' not found"
assert b'your order has been placed successfully.' in resp.data, "Toast message not found"
assert b'Est. Prep Time' in resp.data, "Toast prep time not found"
print("Order Toast Notification passed!")

# GET /customer/api/orders
print("Testing GET /customer/api/orders")
resp = client.get('/customer/api/orders?filter=all&sort=latest')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
orders_list = resp.get_json()
assert len(orders_list) > 0, "No orders returned in list"
latest_order = next((o for o in orders_list if o['order_id'] == order_res['order_id']), None)
assert latest_order is not None, "Placed order not found in customer orders list"
assert latest_order['status'] == 'Pending', f"Expected status Pending, got {latest_order['status']}"
assert latest_order['total_quantity'] == 3, f"Expected total quantity 3, got {latest_order['total_quantity']}"
print("Customer orders API passed!")

# Test Order Cancellation
print("Testing POST /customer/order/cancel/<order_id>")
order_id_to_cancel = order_res['order_id']
resp = client.post(f'/customer/order/cancel/{order_id_to_cancel}')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
cancel_data = resp.get_json()
assert cancel_data['success'] is True, "Order cancellation failed"

# Verify order status is Cancelled
with app.app_context():
    from models.order import Order
    db_order = Order.query.get(order_id_to_cancel)
    assert db_order.status == 'Cancelled', f"Expected status Cancelled, got {db_order.status}"

# Verify second cancellation attempt fails
resp = client.post(f'/customer/order/cancel/{order_id_to_cancel}')
assert resp.status_code == 400, f"Expected 400 for already cancelled order, got {resp.status_code}"
print("Order Cancellation API passed!")

# Test Booking Cancellation
print("Testing POST /customer/booking/cancel/<booking_id>")
with app.app_context():
    from models.booking import Booking
    # Find the booking we created earlier
    latest_booking = Booking.query.filter_by(seat_type='O2').order_by(Booking.created_at.desc()).first()
    assert latest_booking is not None, "Could not find the booking to cancel"
    booking_id_to_cancel = latest_booking.booking_id

resp = client.post(f'/customer/booking/cancel/{booking_id_to_cancel}')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
cancel_book_data = resp.get_json()
assert cancel_book_data['success'] is True, "Booking cancellation failed"

# Verify booking status is Cancelled
with app.app_context():
    from models.booking import Booking
    db_booking = Booking.query.get(booking_id_to_cancel)
    assert db_booking.status == 'Cancelled', f"Expected status Cancelled, got {db_booking.status}"

# Verify second cancellation attempt fails
resp = client.post(f'/customer/booking/cancel/{booking_id_to_cancel}')
assert resp.status_code == 400, f"Expected 400 for already cancelled booking, got {resp.status_code}"
print("Booking Cancellation API passed!")

# Verify order is not returned in customer API orders (Invisibility test)
print("Testing customer orders API filter out Cancelled")
resp = client.get('/customer/api/orders?filter=all&sort=latest')
assert resp.status_code == 200
orders_list = resp.get_json()
cancelled_order_in_api = next((o for o in orders_list if o['order_id'] == order_id_to_cancel), None)
assert cancelled_order_in_api is None, "Cancelled order was returned in customer orders API!"
print("Order Dashboard Invisibility passed!")

# Verify booking is not returned in customer dashboard bookings (Invisibility test)
print("Testing customer dashboard filter out Cancelled bookings")
resp = client.get('/customer/dashboard')
assert resp.status_code == 200
assert f'booking-row-{booking_id_to_cancel}'.encode('utf-8') not in resp.data, "Cancelled booking was rendered in customer dashboard!"
print("Booking Dashboard Invisibility passed!")

# Verify order is still in customer history logs for admin (Visibility test)
print("Testing admin customer history has Cancelled order")
client.get('/auth/logout')
resp = client.post('/auth/login', data={
    'email': 'admin@cafe.com',
    'password': 'admin123'
}, follow_redirects=True)
assert b'Command Center' in resp.data

with app.app_context():
    from models.user import User
    staff_user = User.query.filter_by(email='staff@cafe.com').first()
    staff_user_id = staff_user.id

resp = client.get(f"/admin/api/customer-history/{staff_user_id}")
assert resp.status_code == 200
history = resp.get_json()
cancelled_order_in_history = next((o for o in history if o['order_id'] == order_id_to_cancel), None)
assert cancelled_order_in_history is not None, "Cancelled order not found in admin customer history!"
assert cancelled_order_in_history['status'] == 'Cancelled', f"Expected Cancelled status, got {cancelled_order_in_history['status']}"
print("Admin Cancellation Visibility passed!")

# Restore customer login session for downstream test cases
client.get('/auth/logout')
resp = client.post('/auth/login', data={
    'email': 'staff@cafe.com',
    'password': 'staff123'
}, follow_redirects=True)
assert b'Customer Portal' in resp.data

# Test AI Chat route
print("Testing POST /ai/chat with mocked Gemini response")
from unittest.mock import patch
with patch('services.gemini_service.GeminiService.chat') as mock_chat:
    mock_chat.return_value = "Mocked response: Cold coffee goes best with a warm chocolate brownie!"
    
    resp = client.post('/ai/chat', json={
        'message': 'What goes best with cold coffee?',
        'history': []
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.get_json()
    assert data['success'] is True
    assert "Mocked response" in data['response']
    print("Mocked AI chat passed!")

# Test AI Chat route with missing parameters
print("Testing POST /ai/chat validation errors")
resp = client.post('/ai/chat', json={})
assert resp.status_code == 400, f"Expected 400 for empty payload, got {resp.status_code}"

resp = client.post('/ai/chat', json={'message': '   '})
assert resp.status_code == 400, f"Expected 400 for empty message, got {resp.status_code}"
print("AI chat input validation passed!")

# Test Messaging Security (Customer cannot access)
print("Testing messaging security — unauthorized customer access attempts")
resp = client.get('/admin/messaging')
assert resp.status_code in [302, 403], f"Expected redirect or 403, got {resp.status_code}"

resp = client.post('/admin/messaging/send', json={
    'type': 'Email',
    'recipient': 'test@example.com',
    'subject': 'Alert',
    'body': 'Test body'
})
assert resp.status_code in [302, 403], f"Expected redirect or 403, got {resp.status_code}"

# Log in as Admin
print("Logging in as Admin for messaging tests")
client.get('/auth/logout')
resp = client.post('/auth/login', data={
    'email': 'admin@cafe.com',
    'password': 'admin123'
}, follow_redirects=True)
assert b'Command Center' in resp.data

# GET messaging page
print("Testing GET /admin/messaging as Admin")
resp = client.get('/admin/messaging')
assert resp.status_code == 200
assert b'Messaging <em>Center</em>' in resp.data

# Test search-users phone integration
print("Testing GET /admin/api/search-users returns phone")
resp = client.get('/admin/api/search-users?q=staff')
assert resp.status_code == 200
users = resp.get_json()
assert len(users) > 0
assert 'phone' in users[0], "Phone number was not returned in search-users API"
assert users[0]['phone'] == '+919999999999', f"Expected +919999999999, got {users[0]['phone']}"

# Send Email validation (invalid email)
print("Testing POST /admin/messaging/send email validation error")
resp = client.post('/admin/messaging/send', json={
    'type': 'Email',
    'recipient': 'not-an-email',
    'subject': 'Test Subject',
    'body': 'Test Body'
})
assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
assert b'Invalid email address' in resp.data

# Send Email success
print("Testing POST /admin/messaging/send email success")
resp = client.post('/admin/messaging/send', json={
    'type': 'Email',
    'recipient': 'customer_test@example.com',
    'subject': 'Welcome to HRD!',
    'body': 'This is a test notification.'
})
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert resp.get_json()['success'] is True

# Send SMS validation (invalid phone)
print("Testing POST /admin/messaging/send SMS validation error")
resp = client.post('/admin/messaging/send', json={
    'type': 'SMS',
    'recipient': 'abc12345',
    'body': 'Test SMS body'
})
assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
assert b'Invalid phone number format' in resp.data

# Send SMS success
print("Testing POST /admin/messaging/send SMS success")
resp = client.post('/admin/messaging/send', json={
    'type': 'SMS',
    'recipient': '+919876543210',
    'body': 'Custom notification body text.'
})
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert resp.get_json()['success'] is True

# Send SMS duplicate check
print("Testing POST /admin/messaging/send SMS duplicate prevention")
resp = client.post('/admin/messaging/send', json={
    'type': 'SMS',
    'recipient': '+919876543210',
    'body': 'Custom notification body text.'
})
assert resp.status_code == 400, f"Expected 400 for duplicate, got {resp.status_code}"
assert b'Duplicate submission detected' in resp.data

# Verify logs history
print("Testing GET /admin/messaging/history")
resp = client.get('/admin/messaging/history')
assert resp.status_code == 200
history = resp.get_json()
assert len(history) >= 2
sms_log = next((h for h in history if h['type'] == 'SMS' and h['recipient'] == '+919876543210'), None)
email_log = next((h for h in history if h['type'] == 'Email' and h['recipient'] == 'customer_test@example.com'), None)
assert sms_log is not None, "SMS log not found in messaging history!"
assert sms_log['body'] == 'Custom notification body text.', f"Unexpected SMS body: {sms_log['body']}"
assert email_log is not None, "Email log not found in messaging history!"
assert email_log['subject'] == 'Welcome to HRD!', f"Unexpected Email subject: {email_log['subject']}"
print("Messaging Center API checks passed successfully!")

# Clean up sessions and restore Customer login
client.get('/auth/logout')
resp = client.post('/auth/login', data={
    'email': 'staff@cafe.com',
    'password': 'staff123'
}, follow_redirects=True)
assert b'Customer Portal' in resp.data

# --- APPENDED TESTS FOR FORECASTING & BILLING MATH ---
print("\n--- Running New Forecasting & Billing Tests ---")
# Log back in as Admin
client.get('/auth/logout')
resp = client.post('/auth/login', data={
    'email': 'admin@cafe.com',
    'password': 'admin123'
}, follow_redirects=True)
assert b'Command Center' in resp.data

# Test POST /admin/api/generate-bill with discount
print("Testing POST /admin/api/generate-bill with 10% discount")
resp = client.post('/admin/api/generate-bill', json={
    'user_id': customer['id'],
    'items': [
        {'menu_item_id': first_item_id, 'quantity': 2}
    ],
    'discount_pct': 10
})
assert resp.status_code == 200
bill_data = resp.get_json()
assert bill_data['success'] is True
order_id = bill_data['order_id']

# Verify calculations:
# subtotal = Menu price * 2
# discount = subtotal * 0.1
# net_subtotal = subtotal - discount
# gst = net_subtotal * 0.05
# total = net_subtotal + gst
with app.app_context():
    item_price = Menu.query.get(first_item_id).price
    expected_subtotal = item_price * 2
    expected_discount = expected_subtotal * 0.10
    expected_net = expected_subtotal - expected_discount
    expected_gst = expected_net * 0.05
    expected_total = expected_net + expected_gst
    
    assert abs(bill_data['subtotal'] - expected_subtotal) < 0.01, f"Expected subtotal {expected_subtotal}, got {bill_data['subtotal']}"
    assert abs(bill_data['discount_amount'] - expected_discount) < 0.01, f"Expected discount {expected_discount}, got {bill_data['discount_amount']}"
    assert abs(bill_data['gst_amount'] - expected_gst) < 0.01, f"Expected GST {expected_gst}, got {bill_data['gst_amount']}"
    assert abs(bill_data['total'] - expected_total) < 0.01, f"Expected total {expected_total}, got {bill_data['total']}"
print("Billing math verification passed!")

# Test GET /admin/api/invoice-details/<order_id>
print("Testing GET /admin/api/invoice-details/<order_id>")
resp = client.get(f'/admin/api/invoice-details/{order_id}')
assert resp.status_code == 200
inv_data = resp.get_json()
assert inv_data['success'] is True
assert inv_data['order_id'] == order_id
assert inv_data['customer']['email'] == customer['email']
assert 'discount_pct' in inv_data
assert inv_data['discount_pct'] == 10
assert 'has_reservation' in inv_data
print("Invoice details API passed!")

# Test GET /admin/api/historical-data
print("Testing GET /admin/api/historical-data")
resp = client.get('/admin/api/historical-data')
assert resp.status_code == 200
hist_data = resp.get_json()
assert isinstance(hist_data, list)
print("Historical data GET passed!")

# Test POST /admin/api/historical-data
print("Testing POST /admin/api/historical-data")
tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
resp = client.post('/admin/api/historical-data', json={
    'date': tomorrow_str,
    'customers_count': 50,
    'orders_count': 40,
    'reservations_count': 10
})
assert resp.status_code == 200
assert resp.get_json()['success'] is True

# Verify saved in db
with app.app_context():
    from models.historical_data import DailyHistoricalData
    hist_record = DailyHistoricalData.query.get(tomorrow_str)
    assert hist_record is not None
    assert hist_record.customers_count == 50
    assert hist_record.orders_count == 40
    assert hist_record.reservations_count == 10
print("Historical data POST passed!")

# Test POST /admin/api/train-predictions
print("Testing POST /admin/api/train-predictions")
resp = client.post('/admin/api/train-predictions')
assert resp.status_code == 200
assert resp.get_json()['success'] is True
print("Retrain prediction API passed!")

# Restore customer login session for downstream test cases (or end tests)
client.get('/auth/logout')
resp = client.post('/auth/login', data={
    'email': 'staff@cafe.com',
    'password': 'staff123'
}, follow_redirects=True)
assert b'Customer Portal' in resp.data

print("All tests passed successfully!")
