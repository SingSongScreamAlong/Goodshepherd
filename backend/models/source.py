"""
Source model for tracking data sources.
Extended for World Situational Awareness with trust scoring and collection methods.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
import enum

from backend.core.database import Base


class SourceType(str, enum.Enum):
    """Type of data source for trust classification."""
    OFFICIAL = "official"    # Government, official agencies
    NEWS = "news"            # Reputable news outlets
    SOCIAL = "social"        # Social media (unverified claims)
    NGO = "ngo"              # Non-governmental organizations
    PARTNER = "partner"      # Trusted partner organizations


class CollectionMethod(str, enum.Enum):
    """Allowed method for collecting data from this source."""
    API = "api"              # Direct API access
    RSS = "rss"              # RSS/Atom feed
    HEADLESS = "headless"    # Headless browser (approved URLs only)


class Source(Base):
    """
    Source model for tracking ingestion sources.
    
    Extended to support World Situational Awareness requirements:
    - Trust baseline for confidence scoring
    - Source type classification
    - Collection method restrictions
    - URL pattern allowlists
    """
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    source_type = Column(
        SQLEnum(SourceType),
        nullable=False,
        default=SourceType.NEWS,
        index=True
    )
    url = Column(String(1000), nullable=True)

    # Trust and verification
    trust_baseline = Column(
        Integer,
        nullable=False,
        default=50,
        comment="Base trust score 0-100 for confidence calculation"
    )
    
    # Collection configuration
    allowed_collection_method = Column(
        SQLEnum(CollectionMethod),
        nullable=False,
        default=CollectionMethod.RSS,
        comment="Method allowed for collecting from this source"
    )
    url_patterns = Column(
        JSON,
        nullable=True,
        comment="List of allowed URL patterns for headless collection"
    )

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Region focus (optional)
    region_focus = Column(
        JSON,
        nullable=True,
        comment="List of region IDs this source primarily covers"
    )

    # Statistics
    last_fetch_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    fetch_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, type={self.source_type}, trust={self.trust_baseline})>"
    
    @property
    def is_high_trust(self) -> bool:
        """Check if this is a high-trust source (>=70)."""
        return self.trust_baseline >= 70
    
    @property
    def is_official_source(self) -> bool:
        """Check if this is an official government/agency source."""
        return self.source_type == SourceType.OFFICIAL

