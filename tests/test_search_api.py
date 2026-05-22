import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "search-gateway"


def test_ready():
    resp = client.get("/ready")
    assert resp.status_code in (200, 200)
    data = resp.json()
    assert "dependencies" in data


def test_search_validation_empty_query():
    resp = client.post("/v1/search", json={"query": ""})
    assert resp.status_code == 422


def test_search_validation_limit_too_high():
    resp = client.post("/v1/search", json={"query": "test", "limit": 50})
    assert resp.status_code == 422


def test_engines_status():
    resp = client.get("/v1/engines/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "engines" in data
