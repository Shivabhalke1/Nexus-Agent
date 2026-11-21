"""Integration tests for Cart, Checkout, and Order Lifecycle."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.seed import seed_database
from app.models.product import Product
from app.models.user import User
from app.models.order import Order
from app.models.event import ApplicationEvent

# Shared in-memory test database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        seed_database(db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    # Register and get token
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "shopper@example.com",
            "password": "ShopperPassword2026!",
            "full_name": "Test Shopper",
        },
    )
    if res.status_code == 201:
        token = res.json()["data"]["access_token"]
    else:
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "shopper@example.com", "password": "ShopperPassword2026!"},
        )
        token = login_res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_empty_cart_retrieval(client, auth_headers):
    res = client.get("/api/v1/cart", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["total_items"] == 0
    assert float(data["data"]["total_amount"]) == 0.0


def test_add_items_to_cart(client, auth_headers):
    # Add product 1
    add_res = client.post(
        "/api/v1/cart/items",
        json={"product_id": 1, "quantity": 2},
        headers=auth_headers,
    )
    assert add_res.status_code == 200
    cart_data = add_res.json()["data"]
    assert cart_data["total_items"] == 2
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["quantity"] == 2
    assert float(cart_data["total_amount"]) > 0

    # Add product 2
    add_res2 = client.post(
        "/api/v1/cart/items",
        json={"product_id": 2, "quantity": 1},
        headers=auth_headers,
    )
    assert add_res2.status_code == 200
    assert add_res2.json()["data"]["total_items"] == 3


def test_update_and_remove_cart_item(client, auth_headers):
    cart_res = client.get("/api/v1/cart", headers=auth_headers)
    items = cart_res.json()["data"]["items"]
    first_item = items[0]

    # Update quantity to 4
    update_res = client.put(
        f"/api/v1/cart/items/{first_item['id']}",
        json={"quantity": 4},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    updated_items = update_res.json()["data"]["items"]
    matched = [i for i in updated_items if i["id"] == first_item["id"]][0]
    assert matched["quantity"] == 4

    # Remove second item
    if len(items) > 1:
        second_item = items[1]
        del_res = client.delete(
            f"/api/v1/cart/items/{second_item['id']}",
            headers=auth_headers,
        )
        assert del_res.status_code == 200
        assert len(del_res.json()["data"]["items"]) == 1


def test_simulated_checkout_and_order_creation(client, auth_headers):
    checkout_payload = {
        "shipping_address": "42 Innovation Way, Tech Hub 2026, California, US",
        "payment_method": "simulated_card",
    }
    checkout_res = client.post(
        "/api/v1/orders/checkout",
        json=checkout_payload,
        headers=auth_headers,
    )
    assert checkout_res.status_code == 201
    order_data = checkout_res.json()["data"]
    assert order_data["order_number"].startswith("NEXUS-")
    assert order_data["status"] == "confirmed"
    assert len(order_data["items"]) >= 1
    assert float(order_data["total_amount"]) > 0

    # Verify cart is empty after checkout
    cart_res = client.get("/api/v1/cart", headers=auth_headers)
    assert cart_res.json()["data"]["total_items"] == 0

    # Verify checkout with empty cart fails with 400
    empty_checkout_res = client.post(
        "/api/v1/orders/checkout",
        json=checkout_payload,
        headers=auth_headers,
    )
    assert empty_checkout_res.status_code == 400
    assert empty_checkout_res.json()["error"]["code"] == "EMPTY_CART"


def test_order_history_and_details(client, auth_headers):
    # List orders
    list_res = client.get("/api/v1/orders", headers=auth_headers)
    assert list_res.status_code == 200
    orders = list_res.json()["data"]
    assert len(orders) >= 1
    order_number = orders[0]["order_number"]

    # Get specific order details
    detail_res = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["order_number"] == order_number
    assert detail_data["status"] == "confirmed"
    assert len(detail_data["items"]) >= 1
