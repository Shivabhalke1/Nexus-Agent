"""Order processing, checkout simulation, and order history services."""
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.exceptions import AppException, NotFoundException
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.event import ApplicationEvent
from app.schemas.order import CheckoutRequest, OrderResponse, OrderSummaryResponse

logger = logging.getLogger(settings.SERVICE_NAME)


def generate_order_number() -> str:
    """Generate professional formatted order number: NEXUS-YYYYMMDD-XXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"NEXUS-{date_str}-{random_suffix}"


def process_checkout(
    db: Session,
    user_id: int,
    checkout_in: CheckoutRequest,
    request_id: Optional[str] = None,
) -> OrderResponse:
    """Convert user cart into confirmed simulated order, reducing stock and clearing cart."""
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.user_id == user_id)
        .first()
    )

    if not cart or not cart.items:
        raise AppException(
            message="Cannot checkout with an empty shopping cart.",
            status_code=400,
            error_code="EMPTY_CART",
        )

    # Validate stock for all items atomically
    total_amount = Decimal("0.00")
    order_items_data = []

    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or not product.is_active:
            raise AppException(
                message=f"Product with ID {item.product_id} is no longer available.",
                status_code=400,
                error_code="PRODUCT_UNAVAILABLE",
            )
        if product.stock < item.quantity:
            raise AppException(
                message=f"Insufficient stock for '{product.name}'. Requested: {item.quantity}, Available: {product.stock}.",
                status_code=400,
                error_code="INSUFFICIENT_STOCK",
            )
        
        subtotal = Decimal(str(item.unit_price)) * item.quantity
        total_amount += subtotal
        order_items_data.append((product, item.quantity, item.unit_price, subtotal))

    # Create Order
    order_number = generate_order_number()
    order = Order(
        order_number=order_number,
        user_id=user_id,
        total_amount=total_amount,
        status="confirmed",
        shipping_address=checkout_in.shipping_address,
        payment_method=checkout_in.payment_method,
    )
    db.add(order)
    db.flush()

    # Create OrderItems and deduct stock
    for product, quantity, unit_price, subtotal in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        db.add(order_item)
        # Deduct stock
        product.stock -= quantity

    # Clear user cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    # Emit telemetry event
    event = ApplicationEvent(
        event_type="ORDER_CREATED",
        request_id=request_id,
        severity="INFO",
        payload=json.dumps({
            "order_number": order_number,
            "user_id": user_id,
            "total_amount": str(total_amount),
            "item_count": len(order_items_data),
        }),
    )
    db.add(event)

    db.commit()

    # Reload with relationships
    created_order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )
    return OrderResponse.model_validate(created_order)


def list_user_orders(db: Session, user_id: int) -> List[OrderSummaryResponse]:
    """Retrieve all past orders for an authenticated user."""
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    summaries = []
    for order in orders:
        total_items = sum(item.quantity for item in order.items)
        summaries.append(
            OrderSummaryResponse(
                id=order.id,
                order_number=order.order_number,
                total_amount=order.total_amount,
                status=order.status,
                created_at=order.created_at,
                total_items=total_items,
            )
        )
    return summaries


def get_order_details(db: Session, order_number: str, user_id: int) -> OrderResponse:
    """Retrieve full details of a specific order belonging to the user."""
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.order_number == order_number, Order.user_id == user_id)
        .first()
    )
    if not order:
        raise NotFoundException(resource="Order", identifier=order_number)

    return OrderResponse.model_validate(order)
