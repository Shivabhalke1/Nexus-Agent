"""Shopping cart and cart items models."""
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Cart(BaseModel):
    __tablename__ = "carts"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    session_id = Column(String(128), unique=True, nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(BaseModel):
    __tablename__ = "cart_items"

    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
