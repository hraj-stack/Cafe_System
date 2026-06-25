from datetime import datetime
from models import db

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    recommendation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    recommendations = db.Column(db.Text, nullable=False) # JSON format of recommended items
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Recommendation {self.recommendation_id} for User {self.user_id}>"
