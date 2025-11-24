"""
Events router for querying intelligence events.
"""
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.core.database import get_db
from backend.core.logging import get_logger
from backend.models.event import Event, EventCategory, SentimentEnum
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.schemas.event import EventResponse, EventListResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def get_events(
    category: Optional[EventCategory] = Query(None, description="Filter by event category"),
    sentiment: Optional[SentimentEnum] = Query(None, description="Filter by sentiment"),
    location_name: Optional[str] = Query(None, description="Filter by location name (partial match)"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    min_relevance: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum relevance score"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of events with optional filtering.

    Args:
        category: Filter by event category
        sentiment: Filter by sentiment
        location_name: Filter by location (partial match)
        start_date: Events after this date
        end_date: Events before this date
        min_relevance: Minimum relevance score
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        Paginated list of events
    """
    logger.info(
        "Events query",
        user_id=str(current_user.id),
        category=category,
        page=page,
        page_size=page_size
    )

    # Build query with filters
    query = db.query(Event)

    filters = []

    if category:
        filters.append(Event.category == category)

    if sentiment:
        filters.append(Event.sentiment == sentiment)

    if location_name:
        filters.append(Event.location_name.ilike(f"%{location_name}%"))

    if start_date:
        filters.append(Event.timestamp >= start_date)

    if end_date:
        filters.append(Event.timestamp <= end_date)

    if min_relevance is not None:
        filters.append(Event.relevance_score >= min_relevance)

    if filters:
        query = query.filter(and_(*filters))

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    events = (
        query
        .order_by(Event.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    logger.info("Events retrieved", count=len(events), total=total)

    return {
        "events": events,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single event by ID.

    Args:
        event_id: Event UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Event data
    """
    from uuid import UUID

    try:
        event_uuid = UUID(event_id)
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event ID format"
        )

    event = db.query(Event).filter(Event.id == event_uuid).first()

    if not event:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return event
