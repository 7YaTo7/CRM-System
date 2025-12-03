from datetime import date, datetime
from database import db

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    registration_date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='customer', cascade='all, delete-orphan', lazy=True)
    
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()
    
    def __repr__(self):
        return f'<Customer {self.full_name()}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_price(self):
        return self.quantity * self.price
    
    def __repr__(self):
        return f'<Order {self.product_name} for customer {self.customer_id}>'