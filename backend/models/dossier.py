"""
Dossier and Watchlist models for entity/location tracking.
"""
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, Table, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from core.database import Base


class DossierType(str, enum.Enum):
    """Type of dossier."""
    LOCATION = "location"
    ORGANIZATION = "organization"
    GROUP = "group"
    TOPIC = "topic"
    PERSON = "person"  # Only for public officials, never private individuals


class WatchlistPriority(str, enum.Enum):
    """Priority level for watchlist items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Association table for Watchlist many-to-many with Dossiers
watchlist_dossier = Table(
    'watchlist_dossier',
    Base.metadata,
    Column('watchlist_id', UUID(as_uuid=True), ForeignKey('watchlists.id', ondelete='CASCADE')),
    Column('dossier_id', UUID(as_uuid=True), ForeignKey('dossiers.id', ondelete='CASCADE'))
)


class Dossier(Base):
    """
    Living profile for entities, locations, or topics.
    Aggregates related events and provides historical context.

    OSINT Constraint: Only tracks public entities, never private individuals.
    """
    __tablename__ = "dossiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)

    # Core identification
    name = Column(String(255), nullable=False, index=True)
    dossier_type = Column(SQLEnum(DossierType), nullable=False, index=True)

    # Description and context
    description = Column(Text, nullable=True)
    aliases = Column(JSON, nullable=True)  # List of alternative names

    # Location data (for location-type dossiers)
    location_lat = Column(String(20), nullable=True)
    location_lon = Column(String(20), nullable=True)
    location_name = Column(String(255), nullable=True, index=True)

    # Metadata
    tags = Column(JSON, nullable=True)  # User-defined tags
    notes = Column(Text, nullable=True)  # User notes

    # Statistics (auto-updated)
    event_count = Column(Integer, default=0)  # Total related events
    last_event_timestamp = Column(DateTime, nullable=True)  # Most recent related event
    first_event_timestamp = Column(DateTime, nullable=True)  # Oldest related event

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="dossiers")
    watchlists = relationship("Watchlist", secondary=watchlist_dossier, back_populates="dossiers")


class Watchlist(Base):
    """
    User-defined collection of dossiers to monitor.
    Provides focused awareness on specific entities/locations.
    """
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    # Core data
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(WatchlistPriority), default=WatchlistPriority.MEDIUM, nullable=False)

    # Configuration
    is_active = Column(Integer, default=1, nullable=False)  # 1 = active, 0 = archived
    notification_enabled = Column(Integer, default=0, nullable=False)  # Future: email notifications

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="watchlists")
    user = relationship("User", back_populates="watchlists")
    dossiers = relationship("Dossier", secondary=watchlist_dossier, back_populates="watchlists")
