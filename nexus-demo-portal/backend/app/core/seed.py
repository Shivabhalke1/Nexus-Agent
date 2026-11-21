"""Seed initial realistic e-commerce data."""
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Category, Product, User
from app.core.database import SessionLocal, engine, Base


CATEGORIES_DATA = [
    {
        "name": "Electronics & Audio",
        "slug": "electronics-audio",
        "description": "High-fidelity sound, active noise-canceling headphones, and audio gear.",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
    },
    {
        "name": "Wearables & Smart Devices",
        "slug": "wearables-smart-devices",
        "description": "Smartwatches, fitness rings, and health monitoring wearables.",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
    },
    {
        "name": "Computing & Accessories",
        "slug": "computing-accessories",
        "description": "Ergonomic keyboards, precision mice, monitors, and hubs.",
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80",
    },
    {
        "name": "Cameras & Optics",
        "slug": "cameras-optics",
        "description": "Mirrorless cameras, premium lenses, and creator gear.",
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&q=80",
    },
]

PRODUCTS_DATA = [
    {
        "category_slug": "electronics-audio",
        "name": "AeroPulse Wireless ANC Headphones",
        "slug": "aeropulse-wireless-anc-headphones",
        "description": "Ultra-lightweight wireless headphones featuring hybrid active noise cancellation, 40-hour battery life, and spatial audio with dynamic head tracking.",
        "price": Decimal("249.99"),
        "stock": 45,
        "sku": "AUD-AERO-001",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
    },
    {
        "category_slug": "electronics-audio",
        "name": "SonicStream Studio Monitor Speakers",
        "slug": "sonicstream-studio-monitors",
        "description": "Bi-amplified near-field studio monitors with precision Kevlar drivers, optical digital input, and balanced acoustic room tuning.",
        "price": Decimal("399.00"),
        "stock": 18,
        "sku": "AUD-SONIC-002",
        "image_url": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800&q=80",
    },
    {
        "category_slug": "wearables-smart-devices",
        "name": "Nexus Chrono Pro Smartwatch",
        "slug": "nexus-chrono-pro-smartwatch",
        "description": "Titanium chassis smartwatch with continuous ECG, blood oxygen tracking, dual-band GPS, and 14-day battery life.",
        "price": Decimal("329.50"),
        "stock": 60,
        "sku": "WEAR-CHRONO-001",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
    },
    {
        "category_slug": "computing-accessories",
        "name": "KeyCraft Pro Wireless Mechanical Keyboard",
        "slug": "keycraft-pro-mechanical-keyboard",
        "description": "Hot-swappable mechanical switches, CNC aluminum chassis, gasket-mounted sound dampening, and multi-device Bluetooth connectivity.",
        "price": Decimal("169.00"),
        "stock": 80,
        "sku": "COMP-KEYCRAFT-001",
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80",
    },
    {
        "category_slug": "computing-accessories",
        "name": "ErgoGlide Precision Ergonomic Mouse",
        "slug": "ergoglide-precision-mouse",
        "description": "Sculpted ergonomic vertical mouse designed to alleviate wrist strain, featuring a 4000 DPI darkfield sensor and infinite scroll wheel.",
        "price": Decimal("89.99"),
        "stock": 120,
        "sku": "COMP-ERGOGLIDE-002",
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80",
    },
    {
        "category_slug": "cameras-optics",
        "name": "Lumina Mark IV Mirrorless Camera",
        "slug": "lumina-mark-iv-camera",
        "description": "33MP full-frame sensor camera with 4K 60p 10-bit recording, AI-driven real-time autofocus, and 5-axis in-body image stabilization.",
        "price": Decimal("1899.00"),
        "stock": 12,
        "sku": "CAM-LUMINA-001",
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&q=80",
    },
]


def seed_database(db: Session) -> None:
    """Populate database with categories and products if empty."""
    # Ensure tables exist on the bound engine
    target_engine = db.get_bind()
    Base.metadata.create_all(bind=target_engine)

    # Check existing categories
    if db.query(Category).first():
        return

    # Seed categories
    category_map = {}
    for cat_data in CATEGORIES_DATA:
        category = Category(**cat_data)
        db.add(category)
        db.flush()
        category_map[category.slug] = category.id

    # Seed products
    for prod_data in PRODUCTS_DATA:
        cat_slug = prod_data.get("category_slug")
        category_id = category_map.get(cat_slug)
        if category_id:
            product_dict = {k: v for k, v in prod_data.items() if k != "category_slug"}
            product = Product(category_id=category_id, **product_dict)
            db.add(product)

    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_database(session)
        print("Database seeded successfully!")
