"""Order and order items models."""
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Order(BaseModel):
    __tablename__ = "orders"

    order_number = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(32), default="pending", nullable=False, index=True)  # pending, confirmed, shipped, completed, cancelled
    shipping_address = Column(Text, nullable=False)
    payment_method = Column(String(64), default="simulated_card", nullable=False)

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
