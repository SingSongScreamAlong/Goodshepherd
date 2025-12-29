"""
RawObservation model for buffering collected data before processing.
Represents raw data from sources before normalization into incidents.
"""
import uuid
from datetime import datetime
import hashlib
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from backend.core.database import Base


class ContentType(str, enum.Enum):
    """Type of content in the observation."""
    TEXT = "text"          # Text content (articles, posts)
    IMAGE = "image"        # Image content
    VIDEO = "video"        # Video content
    DATASET = "dataset"    # Structured data (CSV, JSON)


class RawObservation(Base):
    """
    Raw observation from a data source.
    
    This is the first stage in the collection pipeline:
    Source -> RawObservation -> Normalization -> Incident
    
    Observations are buffered here before being processed into
    verified incidents. This allows for:
    - Deduplication via content hash
    - Batch processing
    - Audit trail of raw data
    - Re-processing if enrichment improves
    """
    __tablename__ = "raw_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sources.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Collection metadata
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Content
    content_type = Column(
        SQLEnum(ContentType),
        nullable=False,
        default=ContentType.TEXT
    )
    raw_text = Column(Text, nullable=True)
    title = Column(String(500), nullable=True)
    
    # Media references (for images/videos)
    media_refs = Column(
        JSON,
        nullable=True,
        comment="List of media URLs: [{url, type, size, thumbnail}]"
    )
    
    # Original source URL
    original_url = Column(String(2000), nullable=True, index=True)
    
    # Deduplication
    content_hash = Column(
        String(64),
        nullable=False,
        index=True,
        unique=True,
        comment="SHA-256 hash of content for deduplication"
    )
    
    # Processing state
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Extracted metadata (populated during normalization)
    extracted_locations = Column(
        JSON,
        nullable=True,
        comment="[{name, lat, lon, confidence}]"
    )
    extracted_timestamp = Column(
        DateTime,
        nullable=True,
        comment="Extracted event timestamp (vs collection time)"
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    source = relationship("Source", backref="observations")

    def __repr__(self) -> str:
        return f"<RawObservation(id={self.id}, source_id={self.source_id}, type={self.content_type}, processed={self.processed})>"
    
    @staticmethod
    def compute_hash(content: str, url: str = "") -> str:
        """
        Compute content hash for deduplication.
        
        Args:
            content: Text content to hash
            url: Original URL (included for uniqueness)
            
        Returns:
            SHA-256 hash string
        """
        combined = f"{content.strip().lower()}|{url.strip().lower()}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    @property
    def is_stale(self) -> bool:
        """Check if observation is older than 7 days and unprocessed."""
        if self.processed:
            return False
        age = datetime.utcnow() - self.collected_at
        return age.days > 7
