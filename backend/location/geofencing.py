"""Geofencing and location-based alerting service."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class GeofenceType(str, Enum):
    """Types of geofences."""
    CIRCLE = "circle"
    POLYGON = "polygon"


class ThreatZoneLevel(str, Enum):
    """Threat zone classification levels."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"
    NO_GO = "no_go"


@dataclass
class Coordinate:
    """Geographic coordinate."""
    latitude: float
    longitude: float

    def distance_to(self, other: "Coordinate") -> float:
        """Calculate distance to another coordinate in kilometers (Haversine formula)."""
        R = 6371  # Earth's radius in km

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c


@dataclass
class CircleGeofence:
    """Circular geofence defined by center and radius."""

    id: str
    name: str
    center: Coordinate
    radius_km: float
    threat_level: ThreatZoneLevel
    description: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def contains(self, point: Coordinate) -> bool:
        """Check if a point is within this geofence."""
        return self.center.distance_to(point) <= self.radius_km

    def distance_to_boundary(self, point: Coordinate) -> float:
        """Calculate distance from point to geofence boundary (negative if inside)."""
        return self.center.distance_to(point) - self.radius_km


@dataclass
class PolygonGeofence:
    """Polygon geofence defined by vertices."""

    id: str
    name: str
    vertices: list[Coordinate]
    threat_level: ThreatZoneLevel
    description: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def contains(self, point: Coordinate) -> bool:
        """Check if a point is within this polygon (ray casting algorithm)."""
        n = len(self.vertices)
        inside = False

        j = n - 1
        for i in range(n):
            vi = self.vertices[i]
            vj = self.vertices[j]

            if ((vi.latitude > point.latitude) != (vj.latitude > point.latitude) and
                point.longitude < (vj.longitude - vi.longitude) *
                (point.latitude - vi.latitude) / (vj.latitude - vi.latitude) + vi.longitude):
                inside = not inside
            j = i

        return inside


Geofence = CircleGeofence | PolygonGeofence


@dataclass
class UserLocation:
    """User's current location."""

    user_id: str
    coordinate: Coordinate
    accuracy_meters: float
    timestamp: datetime
    altitude_meters: Optional[float] = None
    speed_mps: Optional[float] = None
    heading: Optional[float] = None


@dataclass
class GeofenceAlert:
    """Alert generated when user enters/exits a geofence."""

    id: str
    user_id: str
    geofence_id: str
    geofence_name: str
    threat_level: ThreatZoneLevel
    event_type: str  # "enter" or "exit"
    location: Coordinate
    timestamp: datetime
    message: str
    acknowledged: bool = False


class GeofenceService:
    """Service for managing geofences and location-based alerts."""

    def __init__(self):
        self._geofences: dict[str, Geofence] = {}
        self._user_locations: dict[str, UserLocation] = {}
        self._user_geofence_state: dict[str, set[str]] = {}  # user_id -> set of geofence_ids they're in
        self._alerts: list[GeofenceAlert] = []

    def add_geofence(self, geofence: Geofence) -> None:
        """Add a geofence to the service."""
        self._geofences[geofence.id] = geofence
        logger.info(f"Added geofence: {geofence.name} ({geofence.id})")

    def remove_geofence(self, geofence_id: str) -> bool:
        """Remove a geofence."""
        if geofence_id in self._geofences:
            del self._geofences[geofence_id]
            logger.info(f"Removed geofence: {geofence_id}")
            return True
        return False

    def get_geofence(self, geofence_id: str) -> Optional[Geofence]:
        """Get a geofence by ID."""
        return self._geofences.get(geofence_id)

    def list_geofences(self, active_only: bool = True) -> list[Geofence]:
        """List all geofences."""
        geofences = list(self._geofences.values())
        if active_only:
            now = datetime.utcnow()
            geofences = [
                g for g in geofences
                if g.active and (g.expires_at is None or g.expires_at > now)
            ]
        return geofences

    def update_user_location(self, location: UserLocation) -> list[GeofenceAlert]:
        """Update a user's location and check for geofence events."""
        user_id = location.user_id
        alerts = []

        # Get user's previous geofence state
        previous_geofences = self._user_geofence_state.get(user_id, set())
        current_geofences = set()

        # Check all active geofences
        for geofence in self.list_geofences(active_only=True):
            if geofence.contains(location.coordinate):
                current_geofences.add(geofence.id)

                # Check for entry
                if geofence.id not in previous_geofences:
                    alert = self._create_alert(
                        user_id=user_id,
                        geofence=geofence,
                        event_type="enter",
                        location=location.coordinate,
                    )
                    alerts.append(alert)
                    self._alerts.append(alert)
            else:
                # Check for exit
                if geofence.id in previous_geofences:
                    alert = self._create_alert(
                        user_id=user_id,
                        geofence=geofence,
                        event_type="exit",
                        location=location.coordinate,
                    )
                    alerts.append(alert)
                    self._alerts.append(alert)

        # Update state
        self._user_locations[user_id] = location
        self._user_geofence_state[user_id] = current_geofences

        return alerts

    def get_user_threat_level(self, user_id: str) -> ThreatZoneLevel:
        """Get the highest threat level for a user's current location."""
        geofence_ids = self._user_geofence_state.get(user_id, set())

        if not geofence_ids:
            return ThreatZoneLevel.SAFE

        threat_order = [
            ThreatZoneLevel.SAFE,
            ThreatZoneLevel.CAUTION,
            ThreatZoneLevel.WARNING,
            ThreatZoneLevel.DANGER,
            ThreatZoneLevel.NO_GO,
        ]

        max_level = ThreatZoneLevel.SAFE
        for gf_id in geofence_ids:
            geofence = self._geofences.get(gf_id)
            if geofence:
                if threat_order.index(geofence.threat_level) > threat_order.index(max_level):
                    max_level = geofence.threat_level

        return max_level

    def get_nearby_threats(
        self,
        location: Coordinate,
        radius_km: float = 50,
    ) -> list[tuple[Geofence, float]]:
        """Get geofences within a radius of a location, with distances."""
        nearby = []

        for geofence in self.list_geofences(active_only=True):
            if isinstance(geofence, CircleGeofence):
                distance = geofence.distance_to_boundary(location)
                if distance < radius_km:
                    nearby.append((geofence, max(0, distance)))
            elif isinstance(geofence, PolygonGeofence):
                # For polygons, use centroid distance as approximation
                if geofence.vertices:
                    centroid = Coordinate(
                        latitude=sum(v.latitude for v in geofence.vertices) / len(geofence.vertices),
                        longitude=sum(v.longitude for v in geofence.vertices) / len(geofence.vertices),
                    )
                    distance = location.distance_to(centroid)
                    if distance < radius_km:
                        nearby.append((geofence, distance))

        # Sort by distance
        nearby.sort(key=lambda x: x[1])
        return nearby

    def get_user_alerts(self, user_id: str, unacknowledged_only: bool = True) -> list[GeofenceAlert]:
        """Get alerts for a specific user."""
        alerts = [a for a in self._alerts if a.user_id == user_id]
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]
        return alerts

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def _create_alert(
        self,
        user_id: str,
        geofence: Geofence,
        event_type: str,
        location: Coordinate,
    ) -> GeofenceAlert:
        """Create a geofence alert."""
        if event_type == "enter":
            message = f"⚠️ You have entered {geofence.name} - {geofence.threat_level.value.upper()} zone"
        else:
            message = f"✓ You have exited {geofence.name}"

        return GeofenceAlert(
            id=str(uuid4()),
            user_id=user_id,
            geofence_id=geofence.id,
            geofence_name=geofence.name,
            threat_level=geofence.threat_level,
            event_type=event_type,
            location=location,
            timestamp=datetime.utcnow(),
            message=message,
        )

    def create_geofence_from_event(
        self,
        event: dict,
        radius_km: float = 10,
    ) -> Optional[CircleGeofence]:
        """Create a geofence from an event with geocode data."""
        geocode = event.get("geocode")
        if not geocode:
            return None

        lat = geocode.get("lat") or geocode.get("latitude")
        lon = geocode.get("lon") or geocode.get("longitude")

        if lat is None or lon is None:
            return None

        # Map event threat level to zone level
        threat_map = {
            "critical": ThreatZoneLevel.NO_GO,
            "high": ThreatZoneLevel.DANGER,
            "medium": ThreatZoneLevel.WARNING,
            "low": ThreatZoneLevel.CAUTION,
        }

        threat_level = threat_map.get(
            (event.get("threat_level") or "").lower(),
            ThreatZoneLevel.CAUTION
        )

        geofence = CircleGeofence(
            id=str(uuid4()),
            name=event.get("title", "Event Zone")[:50],
            center=Coordinate(latitude=float(lat), longitude=float(lon)),
            radius_km=radius_km,
            threat_level=threat_level,
            description=event.get("summary", "")[:200],
        )

        return geofence


# Global service instance
_geofence_service: GeofenceService | None = None


def get_geofence_service() -> GeofenceService:
    """Get the global geofence service instance."""
    global _geofence_service
    if _geofence_service is None:
        _geofence_service = GeofenceService()
    return _geofence_service
