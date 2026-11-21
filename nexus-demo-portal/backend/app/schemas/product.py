"""Product validation and filter schemas."""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.category import CategoryResponse


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    description: str
    price: Decimal = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    sku: str = Field(..., min_length=3, max_length=64)
    image_url: Optional[str] = None
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
