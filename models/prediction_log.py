from datetime import datetime
from models import db

class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'
    prediction_id = db.Column(db.Integer, primary_key=True)
    prediction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expected_customers = db.Column(db.Integer, nullable=False)
    expected_orders = db.Column(db.Integer, nullable=False)
    inventory_alert = db.Column(db.Text, nullable=True) # JSON format array
    
    def __repr__(self):
        return f"<PredictionLog {self.prediction_date.date()} - Cust: {self.expected_customers}>"
