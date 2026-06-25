from models import db

class DailyHistoricalData(db.Model):
    __tablename__ = 'daily_historical_data'
    date = db.Column(db.Date, primary_key=True)
    orders_count = db.Column(db.Integer, nullable=False, default=0)
    reservations_count = db.Column(db.Integer, nullable=False, default=0)
    customers_count = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<DailyHistoricalData {self.date} - O:{self.orders_count} R:{self.reservations_count} C:{self.customers_count}>"
