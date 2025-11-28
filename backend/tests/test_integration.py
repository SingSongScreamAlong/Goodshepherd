"""Integration tests for Good Shepherd API with database fixtures."""

import os
# Set admin key and disable rate limiting before importing app
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
import uuid

from httpx import ASGITransport, AsyncClient

from backend.processing.api_main import app, geofence_service, email_digest_service
from backend.location.geofencing import CircleGeofence, Coordinate, ThreatZoneLevel
from backend.auth.jwt import create_access_token

# Admin headers for protected endpoints
ADMIN_HEADERS = {"X-Admin-API-Key": "test-admin-key"}


def get_auth_headers() -> dict:
    """Get authorization headers with a valid JWT token."""
    token = create_access_token({"sub": "test-user-id", "email": "test@example.com", "roles": ["user"]})
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_events():
    """Sample events for testing."""
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "Armed Conflict in Eastern Europe",
            "summary": "Ongoing armed conflict reported in the region.",
            "category": "conflict",
            "region": "Europe",
            "threat_level": "critical",
            "published_at": datetime.utcnow().isoformat(),
            "link": "https://example.com/event/1",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Earthquake in Pacific Region",
            "summary": "Magnitude 6.5 earthquake detected.",
            "category": "disaster",
            "region": "Asia",
            "threat_level": "high",
            "published_at": datetime.utcnow().isoformat(),
            "link": "https://example.com/event/2",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Travel Advisory Update",
            "summary": "Updated travel advisory for the region.",
            "category": "advisory",
            "region": "Africa",
            "threat_level": "medium",
            "published_at": datetime.utcnow().isoformat(),
            "link": "https://example.com/event/3",
        },
    ]


@pytest.fixture
def sample_geofence():
    """Sample geofence for testing."""
    return CircleGeofence(
        id=str(uuid.uuid4()),
        name="Test Danger Zone",
        center=Coordinate(latitude=40.7128, longitude=-74.0060),
        radius_km=10.0,
        threat_level=ThreatZoneLevel.DANGER,
        description="Test danger zone for integration testing",
    )


@pytest.fixture
async def client():
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    """Headers with admin API key."""
    return {"X-Admin-API-Key": "test-admin-key"}


# =============================================================================
# Geofencing API Integration Tests
# =============================================================================

class TestGeofencingAPI:
    """Integration tests for geofencing endpoints."""

    @pytest.mark.asyncio
    async def test_list_geofences_empty(self, client):
        """Test listing geofences when none exist."""
        # Clear any existing geofences
        for fence in geofence_service.list_geofences():
            geofence_service.remove_geofence(fence.id)

        response = await client.get("/api/geofences")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_circle_geofence(self, client):
        """Test creating a circular geofence."""
        payload = {
            "name": "Test Zone",
            "center": {"latitude": 40.0, "longitude": -74.0},
            "radius_km": 15.0,
            "threat_level": "warning",
            "description": "Test geofence",
        }

        response = await client.post(
            "/api/geofences/circle",
            json=payload,
            headers=ADMIN_HEADERS,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Zone"
        assert data["geofence_type"] == "circle"
        assert data["threat_level"] == "warning"

        # Cleanup
        geofence_service.remove_geofence(data["id"])

    @pytest.mark.asyncio
    async def test_create_polygon_geofence(self, client):
        """Test creating a polygon geofence."""
        payload = {
            "name": "Polygon Zone",
            "vertices": [
                {"latitude": 40.0, "longitude": -74.0},
                {"latitude": 40.0, "longitude": -73.0},
                {"latitude": 41.0, "longitude": -73.0},
                {"latitude": 41.0, "longitude": -74.0},
            ],
            "threat_level": "danger",
        }

        response = await client.post(
            "/api/geofences/polygon",
            json=payload,
            headers=ADMIN_HEADERS,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Polygon Zone"
        assert data["geofence_type"] == "polygon"

        # Cleanup
        geofence_service.remove_geofence(data["id"])

    @pytest.mark.asyncio
    async def test_get_geofence_not_found(self, client):
        """Test getting a non-existent geofence."""
        response = await client.get("/api/geofences/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_geofence(self, client, sample_geofence):
        """Test deleting a geofence."""
        # Add the geofence first
        geofence_service.add_geofence(sample_geofence)

        response = await client.delete(
            f"/api/geofences/{sample_geofence.id}",
            headers=ADMIN_HEADERS,
        )

        assert response.status_code == 204
        assert geofence_service.get_geofence(sample_geofence.id) is None


# =============================================================================
# Location Tracking API Integration Tests
# =============================================================================

class TestLocationAPI:
    """Integration tests for location tracking endpoints."""

    @pytest.mark.asyncio
    async def test_update_user_location(self, client, sample_geofence):
        """Test updating user location."""
        # Add a geofence
        geofence_service.add_geofence(sample_geofence)

        payload = {
            "user_id": "test-user-1",
            "latitude": 40.7128,  # Inside the geofence
            "longitude": -74.0060,
            "accuracy_meters": 10.0,
        }

        response = await client.post("/api/location/update", json=payload, headers=get_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-1"
        assert "current_threat_level" in data
        assert "alerts" in data

        # Cleanup
        geofence_service.remove_geofence(sample_geofence.id)

    @pytest.mark.asyncio
    async def test_get_user_threat_level(self, client):
        """Test getting user threat level."""
        response = await client.get("/api/location/test-user/threat-level")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user"
        assert "threat_level" in data

    @pytest.mark.asyncio
    async def test_get_nearby_threats(self, client, sample_geofence):
        """Test getting nearby threats."""
        geofence_service.add_geofence(sample_geofence)

        response = await client.get(
            "/api/location/nearby-threats",
            params={
                "latitude": 40.7128,
                "longitude": -74.0060,
                "radius_km": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should find our test geofence
        if len(data) > 0:
            assert "geofence_id" in data[0]
            assert "distance_km" in data[0]

        # Cleanup
        geofence_service.remove_geofence(sample_geofence.id)


# =============================================================================
# Email Digest API Integration Tests
# =============================================================================

class TestDigestAPI:
    """Integration tests for email digest endpoints."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, client):
        """Test creating a digest subscription."""
        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "frequency": "daily",
            "regions": ["europe", "asia"],
            "min_threat_level": "high",
        }

        response = await client.post("/api/digests/subscriptions", json=payload, headers=get_auth_headers())

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["frequency"] == "daily"
        # Regions may be in any order
        assert set(data["regions"]) == {"europe", "asia"}

        # Cleanup
        email_digest_service.remove_subscription("test@example.com")

    @pytest.mark.asyncio
    async def test_get_subscription(self, client):
        """Test getting a subscription."""
        # Create subscription first
        from backend.reporting.email_digest import DigestSubscription
        sub = DigestSubscription(email="get-test@example.com", name="Get Test")
        email_digest_service.add_subscription(sub)

        response = await client.get("/api/digests/subscriptions/get-test@example.com", headers=get_auth_headers())

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "get-test@example.com"

        # Cleanup
        email_digest_service.remove_subscription("get-test@example.com")

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, client):
        """Test getting a non-existent subscription."""
        response = await client.get("/api/digests/subscriptions/nonexistent@example.com", headers=get_auth_headers())

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_subscription(self, client):
        """Test deleting a subscription."""
        # Create subscription first
        from backend.reporting.email_digest import DigestSubscription
        sub = DigestSubscription(email="delete-test@example.com")
        email_digest_service.add_subscription(sub)

        response = await client.delete("/api/digests/subscriptions/delete-test@example.com", headers=get_auth_headers())

        assert response.status_code == 204
        assert email_digest_service.get_subscription("delete-test@example.com") is None


# =============================================================================
# WebSocket Integration Tests
# =============================================================================

class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_websocket_stats(self, client):
        """Test WebSocket stats endpoint."""
        response = await client.get("/api/ws/stats")

        assert response.status_code == 200
        data = response.json()
        assert "connected_clients" in data
        assert "timestamp" in data


# =============================================================================
# PDF Report Integration Tests
# =============================================================================

class TestPDFReportAPI:
    """Integration tests for PDF report generation."""

    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, client):
        """Test PDF report generation."""
        # Mock the database session to return empty events
        with patch('backend.processing.api_main.list_recent_events', new_callable=AsyncMock) as mock_events:
            mock_events.return_value = []

            payload = {
                "title": "Test Situational Report",
                "region": "Europe",
                "max_events": 50,
            }

            response = await client.post("/api/reports/pdf", json=payload)

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "attachment" in response.headers["content-disposition"]


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================

class TestE2EWorkflows:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_geofence_alert_workflow(self, client):
        """Test complete geofence alert workflow."""
        # 1. Create a geofence
        create_response = await client.post(
            "/api/geofences/circle",
            json={
                "name": "E2E Test Zone",
                "center": {"latitude": 51.5074, "longitude": -0.1278},
                "radius_km": 5.0,
                "threat_level": "danger",
            },
            headers=ADMIN_HEADERS,
        )

        assert create_response.status_code == 201
        geofence_id = create_response.json()["id"]

        # 2. Update user location to enter the geofence
        location_response = await client.post(
            "/api/location/update",
            json={
                "user_id": "e2e-test-user",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "accuracy_meters": 10.0,
            },
            headers=get_auth_headers(),
        )

        assert location_response.status_code == 200
        location_data = location_response.json()
        assert location_data["current_threat_level"] == "danger"
        assert len(location_data["alerts"]) > 0
        assert location_data["alerts"][0]["event_type"] == "enter"
        assert "message" in location_data["alerts"][0]

        # 3. Check user threat level
        threat_response = await client.get("/api/location/e2e-test-user/threat-level")

        assert threat_response.status_code == 200
        assert threat_response.json()["threat_level"] == "danger"

        # 4. Cleanup
        await client.delete(
            f"/api/geofences/{geofence_id}",
            headers=ADMIN_HEADERS,
        )

    @pytest.mark.asyncio
    async def test_digest_subscription_workflow(self, client):
        """Test complete digest subscription workflow."""
        email = "workflow-test@example.com"

        # Ensure clean state
        email_digest_service.remove_subscription(email)

        # 1. Create subscription
        create_response = await client.post(
            "/api/digests/subscriptions",
            json={
                "email": email,
                "name": "Workflow Test",
                "frequency": "daily",
                "regions": ["europe"],
                "min_threat_level": "high",
            },
            headers=get_auth_headers(),
        )

        assert create_response.status_code == 201

        # 2. Verify subscription exists
        get_response = await client.get(f"/api/digests/subscriptions/{email}", headers=get_auth_headers())

        assert get_response.status_code == 200
        assert get_response.json()["email"] == email

        # 3. Delete subscription
        delete_response = await client.delete(f"/api/digests/subscriptions/{email}", headers=get_auth_headers())

        assert delete_response.status_code == 204

        # 4. Verify deletion
        verify_response = await client.get(f"/api/digests/subscriptions/{email}", headers=get_auth_headers())

        assert verify_response.status_code == 404
