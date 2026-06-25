from datetime import datetime, timezone

from models import db


class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prediction_date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.Integer)
    hour = db.Column(db.Integer)
    expected_customers = db.Column(db.Integer)
    expected_orders = db.Column(db.Integer)
    inventory_alert = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<PredictionLog {self.prediction_date} - {self.expected_customers} customers>'
