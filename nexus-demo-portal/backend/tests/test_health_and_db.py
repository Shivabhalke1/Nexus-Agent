"""Unit and Integration tests for Database, Seed Data, and Health Endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.seed import seed_database
from app.models import Category, Product

# StaticPool ensures shared in-memory SQLite database across connections
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
        # Seed test catalog
        seed_database(db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "components" in data
    assert "database" in data["components"]
    assert response.headers.get("x-request-id") is not None
    assert response.headers.get("x-response-time-ms") is not None


def test_liveness_and_readiness(client):
    live_res = client.get("/api/v1/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "alive"

    ready_res = client.get("/api/v1/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"


def test_seed_categories_available(client):
    response = client.get("/api/v1/products/categories")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    categories = json_data["data"]
    assert len(categories) >= 4
    slugs = [c["slug"] for c in categories]
    assert "electronics-audio" in slugs


def test_seed_products_available(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    paginated = json_data["data"]
    assert paginated["total"] >= 6
    assert len(paginated["items"]) >= 6


def test_product_filter_and_detail(client):
    # Filter by category
    cat_res = client.get("/api/v1/products?category=electronics-audio")
    assert cat_res.status_code == 200
    assert cat_res.json()["data"]["total"] >= 2

    # Get single product details
    detail_res = client.get("/api/v1/products/aeropulse-wireless-anc-headphones")
    assert detail_res.status_code == 200
    product = detail_res.json()["data"]
    assert product["name"] == "AeroPulse Wireless ANC Headphones"
    assert float(product["price"]) > 0

    # Non-existent product returns 404 with custom envelope
    not_found_res = client.get("/api/v1/products/non-existent-item")
    assert not_found_res.status_code == 404
    error_json = not_found_res.json()
    assert error_json["success"] is False
    assert error_json["error"]["code"] == "NOT_FOUND"
