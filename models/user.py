from datetime import datetime
from flask_login import UserMixin
from models import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Customer') # Customer or Admin
    phone = db.Column(db.String(20), nullable=True)
    loyalty_points = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    recommendations = db.relationship('Recommendation', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name} - {self.role}>"
