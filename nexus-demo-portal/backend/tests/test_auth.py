"""Unit and Integration tests for Authentication, JWT, and Security Events."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
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
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_user_registration_success(client):
    payload = {
        "email": "sarah.connor@example.com",
        "password": "SecurePassword2026!",
        "full_name": "Sarah Connor",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    token_data = data["data"]
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["email"] == "sarah.connor@example.com"
    assert token_data["user"]["full_name"] == "Sarah Connor"


def test_duplicate_registration_rejected(client):
    payload = {
        "email": "sarah.connor@example.com",
        "password": "AnotherPassword2026!",
        "full_name": "Sarah Duplicate",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"


def test_login_success(client):
    payload = {
        "email": "sarah.connor@example.com",
        "password": "SecurePassword2026!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_login_invalid_password(client):
    payload = {
        "email": "sarah.connor@example.com",
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_profile_requires_authentication(client):
    # Missing token
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

    # Invalid token
    bad_token_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert bad_token_response.status_code == 401


def test_authenticated_profile_access(client):
    # Log in first
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "sarah.connor@example.com", "password": "SecurePassword2026!"},
    )
    token = login_res.json()["data"]["access_token"]

    # Access /auth/me with valid Bearer token
    profile_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_res.status_code == 200
    user_data = profile_res.json()["data"]
    assert user_data["email"] == "sarah.connor@example.com"
    assert user_data["full_name"] == "Sarah Connor"


def test_auth_telemetry_events_recorded(client):
    # Verify that ApplicationEvent was populated in DB
    with TestingSessionLocal() as db:
        events = db.query(ApplicationEvent).filter(ApplicationEvent.event_type.like("AUTH_%") | ApplicationEvent.event_type.like("USER_%")).all()
        assert len(events) >= 3
        event_types = [e.event_type for e in events]
        assert "USER_REGISTERED" in event_types
        assert "AUTH_LOGIN_SUCCESS" in event_types
        assert "AUTH_LOGIN_FAILED" in event_types
