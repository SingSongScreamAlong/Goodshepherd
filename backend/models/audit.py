"""
Audit logging model for tracking user actions and governance.

Tracks who performed what action on which object for organizational accountability
and compliance. Essential for multi-tenant security and governance.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from backend.core.database import Base


class AuditLog(Base):
    """
    Audit log entry tracking user actions for accountability.

    Records all significant actions users take on organization-scoped and global
    resources. Provides full audit trail for compliance and security.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who performed the action
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # What action was performed
    action_type = Column(String(50), nullable=False, index=True)  # create, update, delete, view, export
    object_type = Column(String(50), nullable=False, index=True)  # dossier, watchlist, event, user, etc.
    object_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # ID of the affected object

    # Additional context
    metadata = Column(JSON, nullable=True)  # Flexible JSON field for action-specific data
    description = Column(Text, nullable=True)  # Human-readable description
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client info

    # When
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="audit_logs")
    organization = relationship("Organization", backref="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action_type}, object={self.object_type})>"
