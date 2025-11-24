"""
Pydantic schemas for event endpoints.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from backend.models.event import EventCategory, SentimentEnum, StabilityTrend


class EventBase(BaseModel):
    """Base schema for event data."""
    timestamp: datetime
    summary: str = Field(..., max_length=500)
    full_text: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    location_name: Optional[str] = None
    category: EventCategory
    sub_category: Optional[str] = None
    sentiment: Optional[SentimentEnum] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    stability_trend: Optional[StabilityTrend] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    source_list: Optional[List[Dict[str, Any]]] = None
    entity_list: Optional[List[Dict[str, Any]]] = None
    cluster_id: Optional[UUID] = None


class EventCreate(EventBase):
    """Schema for creating an event."""
    pass


class EventResponse(EventBase):
    """Schema for event in responses."""
    id: UUID = Field(alias="event_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class EventListResponse(BaseModel):
    """Schema for paginated event list response."""
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


class EventFilters(BaseModel):
    """Schema for event filtering parameters."""
    category: Optional[EventCategory] = None
    sentiment: Optional[SentimentEnum] = None
    location_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_relevance: Optional[float] = Field(None, ge=0.0, le=1.0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
