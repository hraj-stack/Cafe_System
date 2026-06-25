from models import db

class Menu(db.Model):
    __tablename__ = 'menu'
    item_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Coffee, AI Signature Drinks, Food
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True, default='/static/img/default_menu.jpg')

    def __repr__(self):
        return f"<Menu {self.name} - ${self.price}>"
