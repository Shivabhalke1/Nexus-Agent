"""Shopping cart service handling items, quantities, and totals."""
import json
import logging
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.exceptions import NotFoundException, AppException
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.event import ApplicationEvent
from app.schemas.cart import CartResponse, CartItemResponse

logger = logging.getLogger(settings.SERVICE_NAME)


def get_or_create_cart(db: Session, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
    """Retrieve existing cart or create a new cart for user or guest session."""
    cart = None
    if user_id:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    elif session_id:
        cart = db.query(Cart).filter(Cart.session_id == session_id).first()

    if not cart:
        cart = Cart(user_id=user_id, session_id=session_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


def build_cart_response(cart: Cart) -> CartResponse:
    """Compute subtotal, item totals, and return serialized CartResponse."""
    items_response = []
    total_items = 0
    total_amount = Decimal("0.00")

    for item in cart.items:
        subtotal = Decimal(str(item.unit_price)) * item.quantity
        total_items += item.quantity
        total_amount += subtotal

        item_dto = CartItemResponse(
            id=item.id,
            cart_id=item.cart_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=subtotal,
            product=item.product,
        )
        items_response.append(item_dto)

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=items_response,
        total_items=total_items,
        total_amount=total_amount,
    )


def add_item_to_cart(
    db: Session,
    cart_id: int,
    product_id: int,
    quantity: int = 1,
    request_id: Optional[str] = None,
) -> CartResponse:
    """Add a product to cart or increment quantity if already present."""
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise NotFoundException(resource="Product", identifier=product_id)

    if product.stock < quantity:
        raise AppException(
            message=f"Only {product.stock} units available in stock.",
            status_code=400,
            error_code="INSUFFICIENT_STOCK",
        )

    cart_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        .first()
    )

    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            raise AppException(
                message=f"Cannot add {quantity} more; total quantity exceeds available stock ({product.stock}).",
                status_code=400,
                error_code="INSUFFICIENT_STOCK",
            )
        cart_item.quantity = new_quantity
    else:
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,
        )
        db.add(cart_item)

    db.commit()

    # Emit telemetry event
    try:
        event = ApplicationEvent(
            event_type="CART_ITEM_ADDED",
            request_id=request_id,
            severity="INFO",
            payload=json.dumps({"cart_id": cart_id, "product_id": product_id, "quantity": quantity}),
        )
        db.add(event)
        db.commit()
    except Exception:
        pass

    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.id == cart_id)
        .first()
    )
    return build_cart_response(cart)


def update_cart_item(
    db: Session,
    cart_id: int,
    item_id: int,
    quantity: int,
    request_id: Optional[str] = None,
) -> CartResponse:
    """Update item quantity in cart."""
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart_id)
        .first()
    )
    if not cart_item:
        raise NotFoundException(resource="CartItem", identifier=item_id)

    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if product and quantity > product.stock:
        raise AppException(
            message=f"Requested quantity ({quantity}) exceeds stock ({product.stock}).",
            status_code=400,
            error_code="INSUFFICIENT_STOCK",
        )

    cart_item.quantity = quantity
    db.commit()

    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.id == cart_id)
        .first()
    )
    return build_cart_response(cart)


def remove_cart_item(db: Session, cart_id: int, item_id: int) -> CartResponse:
    """Remove an item from cart."""
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart_id)
        .first()
    )
    if not cart_item:
        raise NotFoundException(resource="CartItem", identifier=item_id)

    db.delete(cart_item)
    db.commit()

    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.id == cart_id)
        .first()
    )
    return build_cart_response(cart)


def clear_cart(db: Session, cart_id: int) -> CartResponse:
    """Remove all items from cart."""
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.commit()

    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    cart.items = []
    return build_cart_response(cart)
