from datetime import datetime
from models import db

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.Column(db.Text, nullable=False) # JSON string representation of cart
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Received')
    discount_pct = db.Column(db.Integer, nullable=False, default=0)
    gst_amount = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Order {self.order_id} - {self.status}>"
