"""
IncidentEvidence model for linking raw observations to incidents.
Provides traceable provenance for verification.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from backend.core.database import Base


class EvidenceType(str, enum.Enum):
    """Type of evidence linking observation to incident."""
    TEXT = "text"          # Text-based evidence
    IMAGE = "image"        # Image evidence
    VIDEO = "video"        # Video evidence
    DATASET = "dataset"    # Structured data evidence


class IncidentEvidence(Base):
    """
    Evidence linking a RawObservation to an Incident.
    
    Provides:
    - Traceable provenance (which observations support which incidents)
    - Evidence weighting for confidence calculation
    - Excerpts highlighting relevant portions
    - Audit trail for verification process
    """
    __tablename__ = "incident_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Incident reference (events table)
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey('events.event_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Observation reference
    observation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('raw_observations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Evidence details
    evidence_type = Column(
        SQLEnum(EvidenceType),
        nullable=False,
        default=EvidenceType.TEXT
    )
    
    excerpt = Column(
        Text,
        nullable=True,
        comment="Relevant excerpt from the observation"
    )
    
    weight = Column(
        Float,
        nullable=False,
        default=1.0,
        comment="Weight of this evidence in confidence calculation (0.0-2.0)"
    )
    
    # Verification metadata
    verified_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    incident = relationship("Event", backref="evidence_items")
    observation = relationship("RawObservation", backref="used_in_evidence")
    verifier = relationship("User", backref="verified_evidence")

    def __repr__(self) -> str:
        return f"<IncidentEvidence(id={self.id}, incident={self.incident_id}, type={self.evidence_type}, weight={self.weight})>"
    
    @property
    def is_verified(self) -> bool:
        """Check if this evidence has been manually verified."""
        return self.verified_at is not None
