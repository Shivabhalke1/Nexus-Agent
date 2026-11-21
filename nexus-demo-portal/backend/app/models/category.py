"""Category model for product grouping."""
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)

    # Relationships
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
