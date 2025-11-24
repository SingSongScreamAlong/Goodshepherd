"""
Source model for tracking data sources.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.core.database import Base


class Source(Base):
    """Source model for tracking ingestion sources."""
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    source_type = Column(String(50), nullable=False)  # e.g., "rss", "api", "social"
    url = Column(String(1000), nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

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
        return f"<Source(id={self.id}, name={self.name}, type={self.source_type})>"
