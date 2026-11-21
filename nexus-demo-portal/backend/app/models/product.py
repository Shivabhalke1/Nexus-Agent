"""Product model for e-commerce inventory."""
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
