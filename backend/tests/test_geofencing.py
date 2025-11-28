"""Tests for geofencing and location tracking."""

import pytest
from datetime import datetime, timedelta

from backend.location.geofencing import (
    Coordinate,
    CircleGeofence,
    PolygonGeofence,
    ThreatZoneLevel,
    UserLocation,
    GeofenceService,
)


class TestCoordinate:
    """Tests for Coordinate class."""

    def test_distance_same_point(self):
        """Distance to same point should be zero."""
        coord = Coordinate(latitude=40.7128, longitude=-74.0060)
        assert coord.distance_to(coord) == 0.0

    def test_distance_known_points(self):
        """Test distance calculation with known points."""
        # New York to Los Angeles is approximately 3944 km
        nyc = Coordinate(latitude=40.7128, longitude=-74.0060)
        la = Coordinate(latitude=34.0522, longitude=-118.2437)

        distance = nyc.distance_to(la)
        assert 3900 < distance < 4000  # Allow some tolerance

    def test_distance_short(self):
        """Test short distance calculation."""
        # Two points about 1 km apart
        point1 = Coordinate(latitude=51.5074, longitude=-0.1278)  # London
        point2 = Coordinate(latitude=51.5174, longitude=-0.1278)  # ~1.1 km north

        distance = point1.distance_to(point2)
        assert 1.0 < distance < 1.2


class TestCircleGeofence:
    """Tests for CircleGeofence."""

    def test_contains_center(self):
        """Center point should be inside the geofence."""
        center = Coordinate(latitude=40.0, longitude=-74.0)
        fence = CircleGeofence(
            id="test-1",
            name="Test Zone",
            center=center,
            radius_km=10.0,
            threat_level=ThreatZoneLevel.WARNING,
        )

        assert fence.contains(center) is True

    def test_contains_inside(self):
        """Point inside radius should be contained."""
        center = Coordinate(latitude=40.0, longitude=-74.0)
        fence = CircleGeofence(
            id="test-1",
            name="Test Zone",
            center=center,
            radius_km=10.0,
            threat_level=ThreatZoneLevel.WARNING,
        )

        # Point about 5 km away
        inside_point = Coordinate(latitude=40.045, longitude=-74.0)
        assert fence.contains(inside_point) is True

    def test_contains_outside(self):
        """Point outside radius should not be contained."""
        center = Coordinate(latitude=40.0, longitude=-74.0)
        fence = CircleGeofence(
            id="test-1",
            name="Test Zone",
            center=center,
            radius_km=10.0,
            threat_level=ThreatZoneLevel.WARNING,
        )

        # Point about 20 km away
        outside_point = Coordinate(latitude=40.18, longitude=-74.0)
        assert fence.contains(outside_point) is False

    def test_distance_to_boundary(self):
        """Test distance to boundary calculation."""
        center = Coordinate(latitude=40.0, longitude=-74.0)
        fence = CircleGeofence(
            id="test-1",
            name="Test Zone",
            center=center,
            radius_km=10.0,
            threat_level=ThreatZoneLevel.WARNING,
        )

        # Point at center - should be -10 km (inside)
        assert fence.distance_to_boundary(center) == -10.0

        # Point 15 km away - should be ~5 km (outside)
        far_point = Coordinate(latitude=40.135, longitude=-74.0)
        dist = fence.distance_to_boundary(far_point)
        assert 4.5 < dist < 5.5


class TestPolygonGeofence:
    """Tests for PolygonGeofence."""

    def test_contains_inside_square(self):
        """Point inside a square polygon should be contained."""
        vertices = [
            Coordinate(latitude=40.0, longitude=-74.0),
            Coordinate(latitude=40.0, longitude=-73.0),
            Coordinate(latitude=41.0, longitude=-73.0),
            Coordinate(latitude=41.0, longitude=-74.0),
        ]

        fence = PolygonGeofence(
            id="test-1",
            name="Test Zone",
            vertices=vertices,
            threat_level=ThreatZoneLevel.DANGER,
        )

        # Point in center
        center = Coordinate(latitude=40.5, longitude=-73.5)
        assert fence.contains(center) is True

    def test_contains_outside_square(self):
        """Point outside a square polygon should not be contained."""
        vertices = [
            Coordinate(latitude=40.0, longitude=-74.0),
            Coordinate(latitude=40.0, longitude=-73.0),
            Coordinate(latitude=41.0, longitude=-73.0),
            Coordinate(latitude=41.0, longitude=-74.0),
        ]

        fence = PolygonGeofence(
            id="test-1",
            name="Test Zone",
            vertices=vertices,
            threat_level=ThreatZoneLevel.DANGER,
        )

        # Point outside
        outside = Coordinate(latitude=42.0, longitude=-73.5)
        assert fence.contains(outside) is False

    def test_contains_triangle(self):
        """Test containment in a triangular polygon."""
        vertices = [
            Coordinate(latitude=40.0, longitude=-74.0),
            Coordinate(latitude=40.0, longitude=-73.0),
            Coordinate(latitude=41.0, longitude=-73.5),
        ]

        fence = PolygonGeofence(
            id="test-1",
            name="Triangle Zone",
            vertices=vertices,
            threat_level=ThreatZoneLevel.CAUTION,
        )

        # Point inside triangle
        inside = Coordinate(latitude=40.3, longitude=-73.5)
        assert fence.contains(inside) is True

        # Point outside triangle
        outside = Coordinate(latitude=40.9, longitude=-73.1)
        assert fence.contains(outside) is False


class TestGeofenceService:
    """Tests for GeofenceService."""

    @pytest.fixture
    def service(self):
        """Create a fresh geofence service."""
        return GeofenceService()

    @pytest.fixture
    def sample_geofence(self):
        """Create a sample geofence."""
        return CircleGeofence(
            id="zone-1",
            name="Danger Zone",
            center=Coordinate(latitude=40.0, longitude=-74.0),
            radius_km=10.0,
            threat_level=ThreatZoneLevel.DANGER,
        )

    def test_add_geofence(self, service, sample_geofence):
        """Test adding a geofence."""
        service.add_geofence(sample_geofence)

        assert len(service.list_geofences()) == 1
        assert service.get_geofence("zone-1") is not None

    def test_remove_geofence(self, service, sample_geofence):
        """Test removing a geofence."""
        service.add_geofence(sample_geofence)
        result = service.remove_geofence("zone-1")

        assert result is True
        assert len(service.list_geofences()) == 0

    def test_update_location_enter_alert(self, service, sample_geofence):
        """Test that entering a geofence generates an alert."""
        service.add_geofence(sample_geofence)

        # User enters the zone
        location = UserLocation(
            user_id="user-1",
            coordinate=Coordinate(latitude=40.0, longitude=-74.0),
            accuracy_meters=10.0,
            timestamp=datetime.utcnow(),
        )

        alerts = service.update_user_location(location)

        assert len(alerts) == 1
        assert alerts[0].event_type == "enter"
        assert alerts[0].geofence_id == "zone-1"

    def test_update_location_exit_alert(self, service, sample_geofence):
        """Test that exiting a geofence generates an alert."""
        service.add_geofence(sample_geofence)

        # User enters the zone first
        enter_location = UserLocation(
            user_id="user-1",
            coordinate=Coordinate(latitude=40.0, longitude=-74.0),
            accuracy_meters=10.0,
            timestamp=datetime.utcnow(),
        )
        service.update_user_location(enter_location)

        # User exits the zone
        exit_location = UserLocation(
            user_id="user-1",
            coordinate=Coordinate(latitude=41.0, longitude=-74.0),  # Far away
            accuracy_meters=10.0,
            timestamp=datetime.utcnow(),
        )

        alerts = service.update_user_location(exit_location)

        assert len(alerts) == 1
        assert alerts[0].event_type == "exit"

    def test_get_user_threat_level(self, service):
        """Test getting user's current threat level."""
        # Add multiple geofences
        safe_zone = CircleGeofence(
            id="safe-1",
            name="Safe Zone",
            center=Coordinate(latitude=40.0, longitude=-74.0),
            radius_km=20.0,
            threat_level=ThreatZoneLevel.CAUTION,
        )
        danger_zone = CircleGeofence(
            id="danger-1",
            name="Danger Zone",
            center=Coordinate(latitude=40.0, longitude=-74.0),
            radius_km=5.0,
            threat_level=ThreatZoneLevel.DANGER,
        )

        service.add_geofence(safe_zone)
        service.add_geofence(danger_zone)

        # User in both zones
        location = UserLocation(
            user_id="user-1",
            coordinate=Coordinate(latitude=40.0, longitude=-74.0),
            accuracy_meters=10.0,
            timestamp=datetime.utcnow(),
        )
        service.update_user_location(location)

        # Should return highest threat level
        threat = service.get_user_threat_level("user-1")
        assert threat == ThreatZoneLevel.DANGER

    def test_get_nearby_threats(self, service, sample_geofence):
        """Test getting nearby threats."""
        service.add_geofence(sample_geofence)

        # Point near the geofence
        location = Coordinate(latitude=40.15, longitude=-74.0)

        nearby = service.get_nearby_threats(location, radius_km=50)

        assert len(nearby) == 1
        assert nearby[0][0].id == "zone-1"

    def test_create_geofence_from_event(self, service):
        """Test creating a geofence from an event."""
        event = {
            "title": "Armed Conflict in Region",
            "threat_level": "critical",
            "geocode": {
                "lat": 40.0,
                "lon": -74.0,
            },
            "summary": "Ongoing armed conflict reported.",
        }

        geofence = service.create_geofence_from_event(event, radius_km=15)

        assert geofence is not None
        assert geofence.threat_level == ThreatZoneLevel.NO_GO
        assert geofence.radius_km == 15
        assert geofence.center.latitude == 40.0

    def test_expired_geofence_not_listed(self, service):
        """Test that expired geofences are not listed."""
        expired_fence = CircleGeofence(
            id="expired-1",
            name="Expired Zone",
            center=Coordinate(latitude=40.0, longitude=-74.0),
            radius_km=10.0,
            threat_level=ThreatZoneLevel.WARNING,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        service.add_geofence(expired_fence)

        # Should not appear in active list
        active = service.list_geofences(active_only=True)
        assert len(active) == 0

        # Should appear in full list
        all_fences = service.list_geofences(active_only=False)
        assert len(all_fences) == 1
