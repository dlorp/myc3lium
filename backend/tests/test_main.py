"""Tests for main application endpoints"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_nodes():
    """Test nodes endpoint"""
    response = client.get("/api/nodes")
    assert response.status_code == 200
    assert "nodes" in response.json()


def test_get_connections():
    """Test connections endpoint"""
    response = client.get("/api/connections")
    assert response.status_code == 200
    assert "connections" in response.json()
