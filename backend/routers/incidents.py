"""
Incidents router for managing incidents (events with verification workflow).
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models.event import Event, EventCategory, IncidentStatus, IncidentSeverity
from backend.services.verification_service import verification_service

router = APIRouter(prefix="/incidents", tags=["incidents"])


# Pydantic schemas
class IncidentResponse(BaseModel):
    id: UUID
    title: Optional[str]
    summary: str
    category: str
    status: str
    severity: str
    confidence_score: Optional[float]
    location_name: Optional[str]
    location_lat: Optional[float]
    location_lon: Optional[float]
    occurred_at: Optional[datetime]
    timestamp: datetime
    tags: Optional[List[str]]
    
    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int
    page: int
    page_size: int


class VerificationQueueResponse(BaseModel):
    queue: List[IncidentResponse]
    total: int


class AdminOverrideRequest(BaseModel):
    new_status: str
    notes: Optional[str] = None


class DebunkRequest(BaseModel):
    reason: str


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    region_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List incidents with filtering and pagination."""
    query = db.query(Event)
    
    # Apply filters
    if status:
        try:
            query = query.filter(Event.status == IncidentStatus(status))
        except ValueError:
            pass
    
    if severity:
        try:
            query = query.filter(Event.severity == IncidentSeverity(severity))
        except ValueError:
            pass
    
    if category:
        try:
            query = query.filter(Event.category == EventCategory(category))
        except ValueError:
            pass
    
    if region_id:
        query = query.filter(Event.region_id == region_id)
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    incidents = query.order_by(Event.timestamp.desc()).offset(offset).limit(page_size).all()
    
    return IncidentListResponse(
        incidents=[
            IncidentResponse(
                id=i.id,
                title=i.title,
                summary=i.summary,
                category=i.category.value,
                status=i.status.value,
                severity=i.severity.value,
                confidence_score=i.confidence_score,
                location_name=i.location_name,
                location_lat=i.location_lat,
                location_lon=i.location_lon,
                occurred_at=i.occurred_at,
                timestamp=i.timestamp,
                tags=i.tags
            )
            for i in incidents
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/verification-queue", response_model=VerificationQueueResponse)
async def get_verification_queue(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get incidents pending verification."""
    queue = db.query(Event).filter(
        Event.status.in_([IncidentStatus.UNVERIFIED, IncidentStatus.DEVELOPING])
    ).order_by(Event.timestamp.desc()).limit(limit).all()
    
    return VerificationQueueResponse(
        queue=[
            IncidentResponse(
                id=i.id,
                title=i.title,
                summary=i.summary,
                category=i.category.value,
                status=i.status.value,
                severity=i.severity.value,
                confidence_score=i.confidence_score,
                location_name=i.location_name,
                location_lat=i.location_lat,
                location_lon=i.location_lon,
                occurred_at=i.occurred_at,
                timestamp=i.timestamp,
                tags=i.tags
            )
            for i in queue
        ],
        total=len(queue)
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db)
):
    """Get single incident by ID."""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        summary=incident.summary,
        category=incident.category.value,
        status=incident.status.value,
        severity=incident.severity.value,
        confidence_score=incident.confidence_score,
        location_name=incident.location_name,
        location_lat=incident.location_lat,
        location_lon=incident.location_lon,
        occurred_at=incident.occurred_at,
        timestamp=incident.timestamp,
        tags=incident.tags
    )


@router.post("/{incident_id}/confirm")
async def confirm_incident(
    incident_id: UUID,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)  # Would be actual auth
):
    """Manually confirm an incident."""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # TODO: Get actual user ID from auth
    admin_id = UUID('00000000-0000-0000-0000-000000000000')
    
    verification_service.confirm_incident(incident, admin_id, notes)
    db.commit()
    
    return {"status": "confirmed", "incident_id": str(incident_id)}


@router.post("/{incident_id}/debunk")
async def debunk_incident(
    incident_id: UUID,
    request: DebunkRequest,
    db: Session = Depends(get_db)
):
    """Mark incident as debunked."""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    admin_id = UUID('00000000-0000-0000-0000-000000000000')
    
    verification_service.debunk_incident(incident, admin_id, request.reason)
    db.commit()
    
    return {"status": "debunked", "incident_id": str(incident_id)}


@router.post("/{incident_id}/override")
async def admin_override(
    incident_id: UUID,
    request: AdminOverrideRequest,
    db: Session = Depends(get_db)
):
    """Apply admin override to incident status."""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        new_status = IncidentStatus(request.new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    admin_id = UUID('00000000-0000-0000-0000-000000000000')
    
    verification_service.admin_override(incident, new_status, admin_id, request.notes)
    db.commit()
    
    return {"status": new_status.value, "incident_id": str(incident_id)}
