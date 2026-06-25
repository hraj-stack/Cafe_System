from dotenv import load_dotenv
load_dotenv(override=True)

from flask import Flask, request
from config import config_by_name
from models import db, bcrypt, login_manager


def create_app(config_name='dev'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    print("DB URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))
    print("SECRET_KEY =", app.config.get("SECRET_KEY"))
    print("app.secret_key =", app.secret_key)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():

        # Import models so SQLAlchemy knows about them
        from models.user import User
        from models.booking import Booking
        from models.order import Order
        from models.menu import Menu
        from models.recommendation import Recommendation
        from models.contact import Contact
        from models.prediction_log import PredictionLog
        from models.message_log import MessageLog
        from models.historical_data import DailyHistoricalData

        from sqlalchemy import text

        try:
            db.session.execute(text("SELECT 1"))
            print("Connected to MySQL")

            # Alter users table to add phone column if missing
            try:
                db.session.execute(text("SELECT phone FROM users LIMIT 1"))
            except Exception:
                db.session.rollback()
                db.session.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL"))
                db.session.commit()
                print("Added phone column to users table")

            # Alter orders table to add discount_pct and gst_amount columns if missing
            try:
                db.session.execute(text("SELECT discount_pct FROM orders LIMIT 1"))
            except Exception:
                db.session.rollback()
                db.session.execute(text("ALTER TABLE orders ADD COLUMN discount_pct INT NOT NULL DEFAULT 0"))
                db.session.execute(text("ALTER TABLE orders ADD COLUMN gst_amount DOUBLE NOT NULL DEFAULT 0.0"))
                db.session.commit()
                print("Added discount_pct and gst_amount columns to orders table")

            # Create tables if they don't exist
            db.create_all()

            # Create database indexes on commonly filtered/queried columns for speed
            for index_name, table_name, column_name in [
                ('idx_orders_user_id', 'orders', 'user_id'),
                ('idx_orders_created_at', 'orders', 'created_at'),
                ('idx_orders_status', 'orders', 'status'),
                ('idx_bookings_user_id', 'bookings', 'user_id'),
                ('idx_bookings_date', 'bookings', 'date'),
                ('idx_bookings_status', 'bookings', 'status')
            ]:
                try:
                    db.session.execute(text(f"CREATE INDEX {index_name} ON {table_name} ({column_name})"))
                    db.session.commit()
                    print(f"Created index {index_name} on {table_name}({column_name})")
                except Exception:
                    db.session.rollback() # Index likely already exists

        except Exception as e:
            print(f"Database Error: {e}")

    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.admin import admin_bp
    from routes.orders import orders_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(orders_bp)

    @app.template_filter('load_json')
    def load_json(value):
        import json
        try:
            return json.loads(value)
        except Exception:
            return []

    @app.after_request
    def optimize_responses(response):
        # 1. Enable Browser Caching for static assets
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        
        # 2. Gzip Compression for text/JSON responses
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if (response.status_code == 200 and
            'gzip' in accept_encoding.lower() and
            response.direct_passthrough is False and
            not response.headers.get('Content-Encoding') and
            response.mimetype in ['text/html', 'text/css', 'application/javascript', 'application/json', 'text/xml', 'image/svg+xml']):
            
            import gzip
            import io
            
            try:
                gzip_buffer = io.BytesIO()
                with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gzip_file:
                    gzip_file.write(response.get_data())
                
                response.set_data(gzip_buffer.getvalue())
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(response.get_data())
                response.headers['Vary'] = 'Accept-Encoding'
            except Exception as e:
                print(f"Error compressing response: {e}")
                
        return response

    return app


if __name__ == '__main__':
    app = create_app('dev')
    app.run(debug=True, port=5000)