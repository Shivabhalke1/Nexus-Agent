"""Order management and simulated checkout API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.order import CheckoutRequest, OrderResponse, OrderSummaryResponse
from app.services.order_service import process_checkout, list_user_orders, get_order_details

router = APIRouter(prefix="/orders", tags=["Orders & Checkout"])


@router.post("/checkout", response_model=APIResponse[OrderResponse], status_code=status.HTTP_201_CREATED)
def checkout(
    checkout_in: CheckoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute simulated checkout on the user's shopping cart, creating a confirmed order."""
    request_id = getattr(request.state, "request_id", None)
    order = process_checkout(
        db=db,
        user_id=current_user.id,
        checkout_in=checkout_in,
        request_id=request_id,
    )
    return APIResponse(
        success=True,
        message="Order placed successfully",
        data=order,
    )


@router.get("", response_model=APIResponse[List[OrderSummaryResponse]])
def get_order_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve order history for authenticated user."""
    orders = list_user_orders(db=db, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Order history retrieved successfully",
        data=orders,
    )


@router.get("/{order_number}", response_model=APIResponse[OrderResponse])
def get_order(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full order details by unique order number."""
    order = get_order_details(db=db, order_number=order_number, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Order details retrieved successfully",
        data=order,
    )
