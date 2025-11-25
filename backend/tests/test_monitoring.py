"""
Tests for monitoring and health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_liveness_probe():
    """Test liveness probe endpoint."""
    response = client.get("/monitoring/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["alive"] is True
    assert "timestamp" in data


def test_readiness_probe():
    """Test readiness probe endpoint."""
    response = client.get("/monitoring/health/ready")
    # Should return 200 if database is connected, 503 otherwise
    assert response.status_code in [200, 503]
    data = response.json()
    assert "ready" in data
    assert "database" in data


def test_detailed_health_check():
    """Test detailed health check endpoint."""
    response = client.get("/monitoring/health/detailed")
    # Should return 200 (healthy/degraded) or 503 (unhealthy)
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "components" in data
    assert "database" in data["components"]


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/monitoring/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    # These metrics should be present if database is connected
    if "error" not in data:
        assert "total_events" in data
        assert "total_users" in data
        assert "total_organizations" in data
        assert "total_dossiers" in data
        assert "events_last_24h" in data


def test_version_endpoint():
    """Test version endpoint."""
    response = client.get("/monitoring/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.8.0"
    assert data["name"] == "The Good Shepherd"
    assert "description" in data
    assert "phase" in data


def test_backward_compatible_health_endpoint():
    """Test that old /health endpoint still works."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "postgis" in data


def test_request_tracking_header():
    """Test that request tracking adds X-Request-ID header."""
    response = client.get("/monitoring/health/live")
    assert response.status_code == 200
    # Should have request ID in response headers
    assert "X-Request-ID" in response.headers
    # Request ID should be a valid UUID format
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36  # UUID format with dashes


def test_security_headers():
    """Test that security headers are present."""
    response = client.get("/monitoring/health/live")
    assert response.status_code == 200
    # Check for security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Referrer-Policy" in response.headers
