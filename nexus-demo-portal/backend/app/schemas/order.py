"""Schemas for simulated checkout and order management."""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductResponse


class CheckoutRequest(BaseModel):
    shipping_address: str = Field(..., min_length=5, max_length=500, description="Customer shipping address")
    payment_method: str = Field("simulated_card", max_length=64)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    total_amount: Decimal
    status: str
    shipping_address: str
    payment_method: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderSummaryResponse(BaseModel):
    id: int
    order_number: str
    total_amount: Decimal
    status: str
    created_at: datetime
    total_items: int

    model_config = ConfigDict(from_attributes=True)
