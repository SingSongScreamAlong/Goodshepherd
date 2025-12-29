"""
Admin router for verification workflows and incident management.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models.event import Event, IncidentStatus, IncidentSeverity
from backend.models.incident_evidence import IncidentEvidence
from backend.services.verification_service import verification_service

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic schemas
class IncidentQueueItem(BaseModel):
    id: UUID
    title: Optional[str]
    summary: str
    category: str
    status: str
    severity: str
    confidence_score: Optional[float]
    location_name: Optional[str]
    occurred_at: Optional[datetime]
    timestamp: datetime
    source_count: int
    evidence_count: int
    
    class Config:
        from_attributes = True


class VerificationQueueResponse(BaseModel):
    queue: List[IncidentQueueItem]
    total: int
    stats: dict


class BulkActionRequest(BaseModel):
    incident_ids: List[UUID]
    action: str  # confirm, debunk, downgrade
    notes: Optional[str] = None


class MergeIncidentsRequest(BaseModel):
    primary_id: UUID
    merge_ids: List[UUID]
    notes: Optional[str] = None


class AnalystCommentRequest(BaseModel):
    comment: str


class PinToReportRequest(BaseModel):
    report_ids: List[UUID]


@router.get("/verification-queue", response_model=VerificationQueueResponse)
async def get_verification_queue(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get incidents requiring admin verification.
    
    Default: unverified and developing incidents sorted by priority.
    """
    query = db.query(Event)
    
    # Filter by status
    if status:
        try:
            query = query.filter(Event.status == IncidentStatus(status))
        except ValueError:
            pass
    else:
        # Default: unverified and developing only
        query = query.filter(
            Event.status.in_([IncidentStatus.UNVERIFIED, IncidentStatus.DEVELOPING])
        )
    
    # Filter by severity
    if severity:
        try:
            query = query.filter(Event.severity == IncidentSeverity(severity))
        except ValueError:
            pass
    
    # Filter by confidence range
    if min_confidence is not None:
        query = query.filter(Event.confidence_score >= min_confidence)
    if max_confidence is not None:
        query = query.filter(Event.confidence_score <= max_confidence)
    
    # Order by severity (critical first) then by timestamp
    incidents = query.order_by(
        Event.severity.desc(),
        Event.timestamp.desc()
    ).limit(limit).all()
    
    # Calculate queue stats
    all_unverified = db.query(Event).filter(
        Event.status.in_([IncidentStatus.UNVERIFIED, IncidentStatus.DEVELOPING])
    ).count()
    
    stats = {
        "total_pending": all_unverified,
        "critical": sum(1 for i in incidents if i.severity == IncidentSeverity.CRITICAL),
        "high": sum(1 for i in incidents if i.severity == IncidentSeverity.HIGH),
        "by_status": {
            "unverified": sum(1 for i in incidents if i.status == IncidentStatus.UNVERIFIED),
            "developing": sum(1 for i in incidents if i.status == IncidentStatus.DEVELOPING)
        }
    }
    
    queue_items = []
    for incident in incidents:
        # Count sources and evidence
        source_count = len(incident.source_list or [])
        evidence_count = db.query(IncidentEvidence).filter(
            IncidentEvidence.incident_id == incident.id
        ).count()
        
        queue_items.append(IncidentQueueItem(
            id=incident.id,
            title=incident.title,
            summary=incident.summary,
            category=incident.category.value,
            status=incident.status.value,
            severity=incident.severity.value,
            confidence_score=incident.confidence_score,
            location_name=incident.location_name,
            occurred_at=incident.occurred_at,
            timestamp=incident.timestamp,
            source_count=source_count,
            evidence_count=evidence_count
        ))
    
    return VerificationQueueResponse(
        queue=queue_items,
        total=len(queue_items),
        stats=stats
    )


@router.post("/bulk-action")
async def bulk_action(
    request: BulkActionRequest,
    db: Session = Depends(get_db)
):
    """
    Perform bulk action on multiple incidents.
    
    Actions: confirm, debunk, downgrade
    """
    admin_id = UUID('00000000-0000-0000-0000-000000000000')  # TODO: from auth
    
    valid_actions = ["confirm", "debunk", "downgrade"]
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {valid_actions}"
        )
    
    results = {"success": [], "failed": []}
    
    for incident_id in request.incident_ids:
        incident = db.query(Event).filter(Event.id == incident_id).first()
        
        if not incident:
            results["failed"].append({"id": str(incident_id), "reason": "not found"})
            continue
        
        try:
            if request.action == "confirm":
                verification_service.confirm_incident(incident, admin_id, request.notes)
            elif request.action == "debunk":
                verification_service.debunk_incident(incident, admin_id, request.notes or "Bulk debunk")
            elif request.action == "downgrade":
                # Downgrade to unverified
                verification_service.admin_override(
                    incident,
                    IncidentStatus.UNVERIFIED,
                    admin_id,
                    request.notes or "Downgraded for re-review"
                )
            
            results["success"].append(str(incident_id))
        except Exception as e:
            results["failed"].append({"id": str(incident_id), "reason": str(e)})
    
    db.commit()
    
    return {
        "action": request.action,
        "results": results,
        "success_count": len(results["success"]),
        "failed_count": len(results["failed"])
    }


@router.post("/merge-incidents")
async def merge_incidents(
    request: MergeIncidentsRequest,
    db: Session = Depends(get_db)
):
    """
    Merge duplicate incidents into a primary incident.
    
    - Evidence from merged incidents is linked to primary
    - Confidence is recalculated based on corroboration
    - Merged incidents are marked as debunked with merge note
    """
    admin_id = UUID('00000000-0000-0000-0000-000000000000')
    
    # Get primary incident
    primary = db.query(Event).filter(Event.id == request.primary_id).first()
    if not primary:
        raise HTTPException(status_code=404, detail="Primary incident not found")
    
    merged_count = 0
    
    for merge_id in request.merge_ids:
        if merge_id == request.primary_id:
            continue
        
        merge_incident = db.query(Event).filter(Event.id == merge_id).first()
        if not merge_incident:
            continue
        
        # Transfer evidence links
        evidence_items = db.query(IncidentEvidence).filter(
            IncidentEvidence.incident_id == merge_id
        ).all()
        
        for evidence in evidence_items:
            evidence.incident_id = primary.id
        
        # Merge source lists
        if merge_incident.source_list:
            primary_sources = primary.source_list or []
            for source in merge_incident.source_list:
                if source not in primary_sources:
                    primary_sources.append(source)
            primary.source_list = primary_sources
        
        # Mark merged incident as debunked
        verification_service.debunk_incident(
            merge_incident,
            admin_id,
            f"Merged into incident {request.primary_id}"
        )
        
        merged_count += 1
    
    # Apply corroboration boost to primary
    if merged_count > 0:
        current_confidence = primary.confidence_score or 0.5
        boost = min(0.25, merged_count * 0.08)  # Cap boost at 25%
        primary.confidence_score = min(1.0, current_confidence + boost)
        
        # Update status based on new confidence
        verification_service.update_incident_verification(primary)
        
        # Add merge note
        primary.admin_notes = (primary.admin_notes or "") + f"\n[Merged {merged_count} duplicate(s)]"
        if request.notes:
            primary.admin_notes += f" - {request.notes}"
    
    db.commit()
    
    return {
        "primary_id": str(request.primary_id),
        "merged_count": merged_count,
        "new_confidence": primary.confidence_score,
        "new_status": primary.status.value
    }


@router.post("/{incident_id}/comment")
async def add_analyst_comment(
    incident_id: UUID,
    request: AnalystCommentRequest,
    db: Session = Depends(get_db)
):
    """Add analyst commentary to incident."""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    timestamp = datetime.utcnow().isoformat()
    comment = f"\n[{timestamp}] {request.comment}"
    
    incident.admin_notes = (incident.admin_notes or "") + comment
    db.commit()
    
    return {"incident_id": str(incident_id), "comment_added": True}


@router.post("/{incident_id}/pin-to-reports")
async def pin_to_reports(
    incident_id: UUID,
    request: PinToReportRequest,
    db: Session = Depends(get_db)
):
    """Pin an incident to one or more reports."""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    current_pins = incident.pinned_to_reports or []
    
    for report_id in request.report_ids:
        report_str = str(report_id)
        if report_str not in current_pins:
            current_pins.append(report_str)
    
    incident.pinned_to_reports = current_pins
    db.commit()
    
    return {
        "incident_id": str(incident_id),
        "pinned_to": current_pins
    }


@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Get admin dashboard statistics."""
    # Incident counts by status
    status_counts = {}
    for status in IncidentStatus:
        count = db.query(Event).filter(Event.status == status).count()
        status_counts[status.value] = count
    
    # Recent admin actions
    recent_overrides = db.query(Event).filter(
        Event.admin_override_at.isnot(None)
    ).order_by(Event.admin_override_at.desc()).limit(10).all()
    
    # High priority queue
    high_priority = db.query(Event).filter(
        Event.status.in_([IncidentStatus.UNVERIFIED, IncidentStatus.DEVELOPING]),
        Event.severity.in_([IncidentSeverity.CRITICAL, IncidentSeverity.HIGH])
    ).count()
    
    return {
        "incidents_by_status": status_counts,
        "total_pending": status_counts.get("unverified", 0) + status_counts.get("developing", 0),
        "high_priority_pending": high_priority,
        "recent_actions": [
            {
                "incident_id": str(i.id),
                "action_at": i.admin_override_at.isoformat() if i.admin_override_at else None,
                "new_status": i.status.value
            }
            for i in recent_overrides
        ]
    }
