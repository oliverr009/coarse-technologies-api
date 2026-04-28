from sqlalchemy.orm import Session
from app.models import Product

DEFAULT_PRODUCTS = [
    {"name": "HP EliteBook 840 G6", "description": "Business laptop suitable for office and school work.", "price": 45000, "stock_quantity": 10, "category": "Laptops", "sku": "HP-840-G6", "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80"},
    {"name": "Lenovo ThinkPad T480", "description": "Reliable ThinkPad laptop with business-grade durability.", "price": 52000, "stock_quantity": 8, "category": "Laptops", "sku": "LEN-T480", "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80"},
    {"name": "POS System Bundle", "description": "Complete POS setup for retail shops, supermarkets and restaurants.", "price": 85000, "stock_quantity": 5, "category": "POS Systems", "sku": "POS-BUNDLE-001", "image_url": "https://images.unsplash.com/photo-1556742502-ec7c0e9f34b1?auto=format&fit=crop&w=900&q=80"}
]

def seed_products(db: Session):
    for item in DEFAULT_PRODUCTS:
        if not db.query(Product).filter(Product.sku == item["sku"]).first():
            db.add(Product(**item))
    db.commit()
