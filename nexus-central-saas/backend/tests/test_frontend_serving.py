"""Test for Frontend UI serving."""
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ui_serves_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "NEXUS Central SaaS" in res.text
    assert "System Health" in res.text
    assert "Active Incidents" in res.text
    assert "Engineer Approvals" in res.text
    assert "Resolve Problem" in res.text

def test_ui_alias():
    res = client.get("/ui")
    assert res.status_code == 200
    assert "NEXUS Central SaaS" in res.text
