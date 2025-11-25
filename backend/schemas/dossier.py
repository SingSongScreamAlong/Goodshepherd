"""
Pydantic schemas for Dossiers and Watchlists.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from backend.models.dossier import DossierType, WatchlistPriority


# ===== Dossier Schemas =====

class DossierBase(BaseModel):
    """Base dossier schema."""
    name: str = Field(..., min_length=1, max_length=255)
    dossier_type: DossierType
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    location_lat: Optional[str] = None
    location_lon: Optional[str] = None
    location_name: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class DossierCreate(DossierBase):
    """Schema for creating a dossier."""
    pass


class DossierUpdate(BaseModel):
    """Schema for updating a dossier."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    location_lat: Optional[str] = None
    location_lon: Optional[str] = None
    location_name: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class DossierResponse(DossierBase):
    """Schema for dossier response."""
    id: UUID
    organization_id: UUID
    event_count: int
    last_event_timestamp: Optional[datetime] = None
    first_event_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DossierStats(BaseModel):
    """Statistics for a dossier."""
    dossier_id: UUID
    name: str
    dossier_type: DossierType
    event_count: int
    recent_event_count_7d: int  # Events in last 7 days
    recent_event_count_30d: int  # Events in last 30 days
    last_event_timestamp: Optional[datetime] = None
    categories: dict  # Category distribution
    sentiment_distribution: dict  # Sentiment breakdown


# ===== Watchlist Schemas =====

class WatchlistBase(BaseModel):
    """Base watchlist schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: WatchlistPriority = WatchlistPriority.MEDIUM
    is_active: bool = True
    notification_enabled: bool = False


class WatchlistCreate(WatchlistBase):
    """Schema for creating a watchlist."""
    dossier_ids: Optional[List[UUID]] = []


class WatchlistUpdate(BaseModel):
    """Schema for updating a watchlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[WatchlistPriority] = None
    is_active: Optional[bool] = None
    notification_enabled: Optional[bool] = None
    dossier_ids: Optional[List[UUID]] = None


class WatchlistResponse(WatchlistBase):
    """Schema for watchlist response."""
    id: UUID
    organization_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    dossier_count: int = 0  # Number of dossiers in watchlist

    class Config:
        from_attributes = True


class WatchlistWithDossiers(WatchlistResponse):
    """Watchlist with full dossier details."""
    dossiers: List[DossierResponse] = []

    class Config:
        from_attributes = True
