"""Full End-to-End User Shopping Journey and Telemetry Verification Test."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.seed import seed_database
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


def test_complete_e2e_customer_shopping_journey(client):
    """Simulates a complete real-world customer journey and verifies generated telemetry."""
    # 1. Health Probe
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # 2. Register Account
    reg_payload = {
        "email": "e2e_customer@example.com",
        "password": "StrongPassword2026!",
        "full_name": "E2E Test Customer",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    auth_data = reg_res.json()["data"]
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Browse Categories & Catalog
    cat_res = client.get("/api/v1/products/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json()["data"]
    assert len(categories) >= 4

    catalog_res = client.get("/api/v1/products?category=electronics-audio")
    assert catalog_res.status_code == 200
    products = catalog_res.json()["data"]["items"]
    assert len(products) >= 2
    selected_product = products[0]

    # 4. View Product Details
    detail_res = client.get(f"/api/v1/products/{selected_product['slug']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["sku"] == selected_product["sku"]

    # 5. Add to Cart
    add_res = client.post(
        "/api/v1/cart/items",
        json={"product_id": selected_product["id"], "quantity": 2},
        headers=headers,
    )
    assert add_res.status_code == 200
    cart_data = add_res.json()["data"]
    assert cart_data["total_items"] == 2
    cart_item_id = cart_data["items"][0]["id"]

    # 6. Update Quantity
    update_res = client.put(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 3},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["total_items"] == 3

    # 7. Simulated Checkout
    checkout_payload = {
        "shipping_address": "777 Innovation Way, Silicon Valley, CA 94025, USA",
        "payment_method": "simulated_card",
    }
    checkout_res = client.post(
        "/api/v1/orders/checkout",
        json=checkout_payload,
        headers=headers,
    )
    assert checkout_res.status_code == 201
    order_data = checkout_res.json()["data"]
    order_number = order_data["order_number"]
    assert order_number.startswith("NEXUS-")
    assert order_data["status"] == "confirmed"

    # 8. Verify Cart is Empty
    cart_after = client.get("/api/v1/cart", headers=headers)
    assert cart_after.json()["data"]["total_items"] == 0

    # 9. Verify Order History & Order Details
    history_res = client.get("/api/v1/orders", headers=headers)
    assert history_res.status_code == 200
    orders_list = history_res.json()["data"]
    assert any(o["order_number"] == order_number for o in orders_list)

    order_detail_res = client.get(f"/api/v1/orders/{order_number}", headers=headers)
    assert order_detail_res.status_code == 200
    assert order_detail_res.json()["data"]["order_number"] == order_number
    assert len(order_detail_res.json()["data"]["items"]) == 1

    # 10. Verify Telemetry & Prometheus Scraper
    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    assert "nexus_requests_total" in metrics_res.text

    # 11. Verify Database Audit Events
    with TestingSessionLocal() as db:
        events = db.query(ApplicationEvent).all()
        assert len(events) >= 3
        types = [e.event_type for e in events]
        assert "USER_REGISTERED" in types
        assert "CART_ITEM_ADDED" in types
        assert "ORDER_CREATED" in types
