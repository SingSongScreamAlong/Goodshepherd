"""
Event feedback model for collecting user feedback on event quality and relevance.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


class EventFeedback(Base):
    """Model for storing user feedback on events."""
    __tablename__ = "event_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Feedback data
    feedback_type = Column(String(50), nullable=False)  # "relevant", "irrelevant", "misclassified", "important"
    comment = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", backref="feedback")
    user = relationship("User", backref="event_feedback")

    def __repr__(self) -> str:
        return f"<EventFeedback(id={self.id}, event_id={self.event_id}, type={self.feedback_type})>"
