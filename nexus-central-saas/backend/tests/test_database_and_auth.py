"""Unit Tests for Database Models and Authentication"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.entities import User, Collector, ActiveIncidentRecord
from app.core.security import hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_engineer_login_success():
    resp = client.post("/api/v1/auth/login", json={"username": "engineer", "password": "engineer123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["username"] == "engineer"
    assert data["role"] == "engineer"


def test_engineer_login_failure():
    resp = client.post("/api/v1/auth/login", json={"username": "engineer", "password": "wrong_password"})
    assert resp.status_code == 401


def test_database_user_persistence():
    db = SessionLocal()
    try:
        # Create custom engineer user
        custom_user = User(
            username="ops_lead",
            password_hash=hash_password("ops123!"),
            role="engineer",
        )
        db.add(custom_user)
        db.commit()

        # Login with newly created user
        resp = client.post("/api/v1/auth/login", json={"username": "ops_lead", "password": "ops123!"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "ops_lead"
    finally:
        # Cleanup
        db.query(User).filter(User.username == "ops_lead").delete()
        db.commit()
        db.close()
