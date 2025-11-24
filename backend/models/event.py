"""
Event model for storing intelligence events.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Float, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from geoalchemy2 import Geometry
import enum

from backend.core.database import Base


class EventCategory(str, enum.Enum):
    """Category taxonomy for events."""
    PROTEST = "protest"
    CRIME = "crime"
    RELIGIOUS_FREEDOM = "religious_freedom"
    CULTURAL_TENSION = "cultural_tension"
    POLITICAL = "political"
    INFRASTRUCTURE = "infrastructure"
    HEALTH = "health"
    MIGRATION = "migration"
    ECONOMIC = "economic"
    WEATHER = "weather"
    COMMUNITY_EVENT = "community_event"
    OTHER = "other"


class SentimentEnum(str, enum.Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class StabilityTrend(str, enum.Enum):
    """Stability trend indicator."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    NEUTRAL = "neutral"


class Event(Base):
    """Event model representing an intelligence event."""
    __tablename__ = "events"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, name="event_id")

    # Temporal
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Content
    summary = Column(String(500), nullable=False)
    full_text = Column(Text, nullable=True)

    # Geospatial (using PostGIS)
    location_point = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=True,
        index=True
    )
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True, index=True)

    # Classification
    category = Column(SQLEnum(EventCategory), nullable=False, index=True)
    sub_category = Column(String(100), nullable=True)

    # Analysis
    sentiment = Column(SQLEnum(SentimentEnum), nullable=True)
    relevance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    stability_trend = Column(SQLEnum(StabilityTrend), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0

    # Sources and entities (stored as JSON arrays)
    source_list = Column(JSON, nullable=True)  # List of source metadata dicts
    entity_list = Column(JSON, nullable=True)  # List of entity dicts

    # Clustering
    cluster_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, category={self.category}, location={self.location_name})>"

    @property
    def coordinates(self) -> Optional[tuple]:
        """Get coordinates as (lat, lon) tuple."""
        if self.location_lat is not None and self.location_lon is not None:
            return (self.location_lat, self.location_lon)
        return None
