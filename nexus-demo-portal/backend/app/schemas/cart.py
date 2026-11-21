"""Schemas for shopping cart and cart items."""
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductResponse


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1, le=99)


class CartItemAdd(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=99)


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    items: List[CartItemResponse]
    total_items: int
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)
