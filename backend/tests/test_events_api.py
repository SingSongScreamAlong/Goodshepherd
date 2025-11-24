"""
Test cases for events API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "The Good Shepherd" in data["message"]


def test_events_endpoint_requires_auth():
    """Test that events endpoint requires authentication."""
    response = client.get("/events")
    assert response.status_code == 401  # Unauthorized


# Add more tests as needed
