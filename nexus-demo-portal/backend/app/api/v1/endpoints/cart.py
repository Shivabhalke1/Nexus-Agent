"""Shopping cart API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.api.v1.endpoints.auth import security_scheme
from app.core.security import decode_access_token
from app.models.cart import Cart, CartItem
from app.schemas.response import APIResponse
from app.schemas.cart import CartResponse, CartItemAdd, CartItemUpdate
from app.services.cart_service import (
    get_or_create_cart,
    build_cart_response,
    add_item_to_cart,
    update_cart_item,
    remove_cart_item,
    clear_cart,
)

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


def resolve_cart_identity(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Cart:
    """Resolve current cart either from Bearer token or guest session header."""
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            try:
                user_id = int(payload["sub"])
            except Exception:
                pass

    session_id = x_session_id or request.cookies.get("nexus_session_id") or "guest-default-session"
    return get_or_create_cart(db=db, user_id=user_id, session_id=session_id if not user_id else None)


@router.get("", response_model=APIResponse[CartResponse])
def get_cart(
    cart: Cart = Depends(resolve_cart_identity),
    db: Session = Depends(get_db),
):
    """Retrieve current shopping cart with all items and computed grand totals."""
    loaded_cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.id == cart.id)
        .first()
    )
    return APIResponse(
        success=True,
        message="Cart retrieved successfully",
        data=build_cart_response(loaded_cart),
    )


@router.post("/items", response_model=APIResponse[CartResponse])
def add_to_cart(
    item_in: CartItemAdd,
    request: Request,
    cart: Cart = Depends(resolve_cart_identity),
    db: Session = Depends(get_db),
):
    """Add a product item to the shopping cart."""
    request_id = getattr(request.state, "request_id", None)
    result = add_item_to_cart(
        db=db,
        cart_id=cart.id,
        product_id=item_in.product_id,
        quantity=item_in.quantity,
        request_id=request_id,
    )
    return APIResponse(
        success=True,
        message="Item added to cart",
        data=result,
    )


@router.put("/items/{item_id}", response_model=APIResponse[CartResponse])
def update_item_quantity(
    item_id: int,
    item_in: CartItemUpdate,
    request: Request,
    cart: Cart = Depends(resolve_cart_identity),
    db: Session = Depends(get_db),
):
    """Update item quantity in cart."""
    request_id = getattr(request.state, "request_id", None)
    result = update_cart_item(
        db=db,
        cart_id=cart.id,
        item_id=item_id,
        quantity=item_in.quantity,
        request_id=request_id,
    )
    return APIResponse(
        success=True,
        message="Cart item updated",
        data=result,
    )


@router.delete("/items/{item_id}", response_model=APIResponse[CartResponse])
def remove_from_cart(
    item_id: int,
    cart: Cart = Depends(resolve_cart_identity),
    db: Session = Depends(get_db),
):
    """Remove item from cart."""
    result = remove_cart_item(db=db, cart_id=cart.id, item_id=item_id)
    return APIResponse(
        success=True,
        message="Item removed from cart",
        data=result,
    )


@router.delete("", response_model=APIResponse[CartResponse])
def clear_shopping_cart(
    cart: Cart = Depends(resolve_cart_identity),
    db: Session = Depends(get_db),
):
    """Empty the shopping cart."""
    result = clear_cart(db=db, cart_id=cart.id)
    return APIResponse(
        success=True,
        message="Cart cleared",
        data=result,
    )
