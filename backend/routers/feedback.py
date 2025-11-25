"""
Event feedback API endpoints for collecting user feedback on event quality and relevance.
This data can be used to tune the enrichment and scoring algorithms.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.models.event import Event
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])


class EventFeedbackCreate(BaseModel):
    """Schema for creating event feedback."""
    event_id: UUID
    feedback_type: str  # "relevant", "irrelevant", "misclassified", "important"
    comment: str | None = None


@router.post("/event")
def submit_event_feedback(
    feedback: EventFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on an event's relevance, classification, or importance.

    This endpoint logs feedback for future use in tuning enrichment algorithms.
    For now, feedback is logged only; future versions may update event scores
    or trigger re-classification.

    Args:
        feedback: Feedback data (event_id, type, optional comment)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If event not found
    """
    # Verify event exists
    event = db.query(Event).filter(Event.id == feedback.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Log feedback (structured logging for future analysis)
    logger.info(
        "event_feedback_submitted",
        event_id=str(feedback.event_id),
        feedback_type=feedback.feedback_type,
        user_id=str(current_user.id),
        user_email=current_user.email,
        comment=feedback.comment,
        event_category=event.category.value if event.category else None,
        event_sentiment=event.sentiment.value if event.sentiment else None,
        event_relevance_score=event.relevance_score,
        timestamp=datetime.utcnow().isoformat(),
    )

    # TODO: Future enhancement - store in dedicated feedback table
    # TODO: Future enhancement - trigger re-classification if "misclassified"
    # TODO: Future enhancement - adjust event scores based on feedback

    return {
        "message": "Feedback submitted successfully",
        "event_id": str(feedback.event_id),
        "feedback_type": feedback.feedback_type,
    }


@router.get("/stats")
def get_feedback_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get feedback statistics (future enhancement).

    Currently returns placeholder data.
    Future: Return aggregate stats from feedback table.

    Args:
        current_user: Current authenticated user

    Returns:
        Feedback statistics
    """
    # Placeholder for future implementation
    return {
        "total_feedback": 0,
        "feedback_by_type": {
            "relevant": 0,
            "irrelevant": 0,
            "misclassified": 0,
            "important": 0,
        },
        "message": "Feedback statistics will be available in future version",
    }
