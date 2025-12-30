"""
Event/Incident model for storing intelligence events.
Extended for World Situational Awareness with verification workflow.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Float, Text, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum

# Try to import geoalchemy2, but it's optional for dev
try:
    from geoalchemy2 import Geometry
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

from backend.core.database import Base


class EventCategory(str, enum.Enum):
    """Category taxonomy for events/incidents."""
    SECURITY = "security"            # Security threats, violence
    MIGRATION = "migration"          # Migration-related events
    POLITICAL = "political"          # Political events
    DISASTER = "disaster"            # Natural disasters, emergencies
    INFRASTRUCTURE = "infrastructure" # Infrastructure disruptions
    HEALTH = "health"                # Health alerts, outbreaks
    # Legacy categories (kept for backward compatibility)
    PROTEST = "protest"
    CRIME = "crime"
    RELIGIOUS_FREEDOM = "religious_freedom"
    CULTURAL_TENSION = "cultural_tension"
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


class IncidentStatus(str, enum.Enum):
    """Verification status of an incident."""
    UNVERIFIED = "unverified"      # < 30 confidence
    DEVELOPING = "developing"       # 30-59 confidence
    CORROBORATED = "corroborated"  # 60-84 confidence  
    CONFIRMED = "confirmed"        # 85+ confidence
    DEBUNKED = "debunked"          # Proven false


class IncidentSeverity(str, enum.Enum):
    """Severity level of an incident."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Event(Base):
    """
    Event/Incident model representing an intelligence event.
    
    Extended for World Situational Awareness:
    - Status workflow (unverified -> confirmed)
    - Severity classification
    - Admin override with audit trail
    - Region linkage
    - Domain tagging
    
    Note: Table name remains 'events' for backward compatibility,
    but conceptually these are now 'Incidents' in the system.
    """
    __tablename__ = "events"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, name="event_id")

    # Title (new for incidents)
    title = Column(String(300), nullable=True, index=True)

    # Temporal
    timestamp = Column(DateTime, nullable=False, index=True)  # When collected
    occurred_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="When the incident actually occurred (vs when collected)"
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Content
    summary = Column(String(500), nullable=False)
    full_text = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Geospatial - location_point column removed for dev (PostGIS optional)
    # NOTE: In production with PostGIS, this column would be added by migration
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True, index=True)
    
    # Region reference
    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey('regions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Classification
    category = Column(SQLEnum(EventCategory), nullable=False, index=True)
    sub_category = Column(String(100), nullable=True)
    
    # Verification status workflow
    status = Column(
        SQLEnum(IncidentStatus),
        nullable=False,
        default=IncidentStatus.UNVERIFIED,
        index=True
    )
    severity = Column(
        SQLEnum(IncidentSeverity),
        nullable=False,
        default=IncidentSeverity.MEDIUM
    )

    # Analysis scores
    sentiment = Column(SQLEnum(SentimentEnum), nullable=True)
    relevance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    stability_trend = Column(SQLEnum(StabilityTrend), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0 (now 0-100 internally)

    # Sources and entities (stored as JSON arrays)
    source_list = Column(JSON, nullable=True)  # List of source metadata dicts
    entity_list = Column(JSON, nullable=True)  # List of entity dicts
    
    # Domain tags for multi-dimensional tracking
    tags = Column(
        JSON,
        nullable=True,
        comment="Domain tags: geopolitical, migration, security, economic, infrastructure"
    )

    # Clustering
    cluster_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Admin override fields
    admin_override_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    admin_override_at = Column(DateTime, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Report inclusion
    pinned_to_reports = Column(
        JSON,
        nullable=True,
        comment="List of report IDs this incident is pinned to"
    )
    
    # Relationships
    region = relationship("Region", backref="incidents", foreign_keys=[region_id])
    admin_override_user = relationship("User", backref="overridden_incidents", foreign_keys=[admin_override_by])

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, category={self.category}, status={self.status}, location={self.location_name})>"

    @property
    def coordinates(self) -> Optional[tuple]:
        """Get coordinates as (lat, lon) tuple."""
        if self.location_lat is not None and self.location_lon is not None:
            return (self.location_lat, self.location_lon)
        return None
    
    @property
    def confidence_percent(self) -> int:
        """Get confidence as a 0-100 percentage."""
        if self.confidence_score is None:
            return 0
        return int(self.confidence_score * 100)
    
    def compute_status_from_confidence(self) -> IncidentStatus:
        """
        Compute verification status from confidence score.
        
        Thresholds set high because lives depend on accuracy:
        - < 40%: UNVERIFIED (unsubstantiated)
        - 40-74%: DEVELOPING (working to verify)
        - 75%+: CORROBORATED (strong multi-source evidence)
        - CONFIRMED: Admin verification only
        
        Returns:
            IncidentStatus based on confidence thresholds
        """
        conf = self.confidence_percent
        if conf < 40:
            return IncidentStatus.UNVERIFIED
        elif conf < 75:
            return IncidentStatus.DEVELOPING
        else:
            # Max algorithmic status - CONFIRMED requires admin action
            return IncidentStatus.CORROBORATED
    
    @property
    def is_verified(self) -> bool:
        """Check if incident is at least corroborated."""
        return self.status in [IncidentStatus.CORROBORATED, IncidentStatus.CONFIRMED]
    
    @property  
    def is_critical(self) -> bool:
        """Check if incident is critical severity."""
        return self.severity == IncidentSeverity.CRITICAL


# Alias for clarity in new code
Incident = Event

