from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    FARMER = 'farmer'
    BUYER = 'buyer'
    ROLES = (FARMER, BUYER)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True) # Optional for now, required if normal register
    password = db.Column(db.String(150), nullable=True) # Nullable for Google login
    role = db.Column(db.String(50), nullable=False, default='buyer') # 'farmer' or 'buyer'
    theme = db.Column(db.String(20), nullable=False, default='system')
    message_policy = db.Column(db.String(20), nullable=False, default='everyone')
    
    # New fields for Phase 2
    full_name = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    farm_description = db.Column(db.Text, nullable=True)
    farm_product_type = db.Column(db.String(120), nullable=True)
    avatar_path = db.Column(db.String(300), nullable=True)
    google_id = db.Column(db.String(200), unique=True, nullable=True)

    products = db.relationship('Product', backref='farmer', lazy=True)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')


class MessagePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    __table_args__ = (db.UniqueConstraint('owner_id', 'contact_id'),)
    owner = db.relationship('User', foreign_keys=[owner_id], backref='message_permissions')
    contact = db.relationship('User', foreign_keys=[contact_id])


class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    farmer = db.relationship('User', backref=db.backref('workers', lazy=True, cascade='all, delete-orphan'))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    min_order_quantity = db.Column(db.Float, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reservations = db.relationship('Reservation', backref='product', lazy=True)
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'min_order_quantity': self.min_order_quantity,
            'price': self.price,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d'),
            'farmer_name': self.farmer.username
            , 'images': [image.path for image in self.images]
        }


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(200), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='reserved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer = db.relationship('User', backref='reservations')
