from datetime import datetime
from models import db

class MessageLog(db.Model):
    __tablename__ = 'message_logs'
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    message_type = db.Column(db.String(20), nullable=False) # 'Email', 'SMS', 'WhatsApp'
    subject = db.Column(db.String(200), nullable=True)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Sent')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<MessageLog to {self.recipient} - {self.status}>"
