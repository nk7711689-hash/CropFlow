"""Seed local CropFlow demo accounts and marketplace data.

Run with: python seed_demo.py
This script is idempotent and does not delete existing application data.
"""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import app, initialize_database
from models import Product, User, db

DEMO_PASSWORD = "CropFlow123!"


def get_or_create_user(username, email, role, full_name, phone, location):
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username, email=email, role=role)
        db.session.add(user)
    user.email = email
    user.role = role
    user.full_name = full_name
    user.phone = phone
    user.location = location
    user.password = generate_password_hash(DEMO_PASSWORD, method="pbkdf2:sha256")
    return user


def seed_demo_data():
    farmer = get_or_create_user(
        "farmer_demo",
        "farmer.demo@cropflow.local",
        "farmer",
        "مزرعة الوادي الخضراء",
        "+966500000001",
        "القصيم، المملكة العربية السعودية",
    )
    farmer.farm_description = "مزرعة عائلية تزرع خضروات وفواكه موسمية طازجة وتجهزها للمطاعم والمتاجر المحلية."
    farmer.farm_product_type = "خضروات، فواكه، أعشاب"
    buyer = get_or_create_user(
        "buyer_demo",
        "buyer.demo@cropflow.local",
        "buyer",
        "مطاعم الحصاد الحديثة",
        "+966500000002",
        "الرياض، المملكة العربية السعودية",
    )
    db.session.flush()

    products = [
        ("طماطم كرزية", 850, 25, 7.50, 3),
        ("خيار بلدي", 1200, 40, 4.25, 2),
        ("ورقيات مشكلة", 320, 10, 12.00, 1),
        ("فلفل ملون", 560, 20, 9.75, 2),
        ("بصل أحمر", 1800, 75, 3.90, 4),
        ("نعناع طازج", 180, 5, 14.50, 1),
    ]
    expiry_dates = [date.today() + timedelta(days=days) for days in (7, 10, 5, 12, 20, 4)]

    created = 0
    for (name, quantity, minimum, price, _), expiry_date in zip(products, expiry_dates):
        product = Product.query.filter_by(name=name, farmer_id=farmer.id).first()
        if product is None:
            product = Product(name=name, farmer_id=farmer.id)
            db.session.add(product)
            created += 1
        product.quantity = quantity
        product.min_order_quantity = minimum
        product.price = price
        product.expiry_date = expiry_date

    db.session.commit()
    print(f"Demo users ready: {farmer.username}, {buyer.username}")
    print(f"Demo products ready: {created} new, {len(products)} total demo listings")
    print(f"Demo password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
        seed_demo_data()
