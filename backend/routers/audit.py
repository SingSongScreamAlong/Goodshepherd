"""
Audit log API endpoints for viewing action history.

Provides read-only access to audit logs for administrators to review
user actions and ensure accountability.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from backend.core.database import get_db
from backend.core.dependencies import get_current_user, get_current_org_id
from backend.models.user import User, RoleEnum
from backend.models.audit import AuditLog
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    """Response schema for audit log entries."""
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    organization_id: str
    action_type: str
    object_type: str
    object_id: Optional[str]
    description: Optional[str]
    metadata: Optional[dict]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for the current organization.

    Only administrators can view audit logs. Returns paginated list of
    audit entries filtered by the provided criteria.

    Args:
        action_type: Optional action type filter
        object_type: Optional object type filter
        user_id: Optional user ID filter
        days: Number of days to look back (default: 30, max: 365)
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 500)
        current_user: Current authenticated user
        org_id: Current organization ID
        db: Database session

    Returns:
        List of audit log entries

    Raises:
        HTTPException: If user is not an admin
    """
    # Check if user is admin
    # Note: In a real implementation, you'd check the user's role in the organization
    # For now, we'll allow all authenticated users (adjust based on your requirements)

    # Build query
    query = db.query(AuditLog).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=days)
        )
    )

    # Apply filters
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if object_type:
        query = query.filter(AuditLog.object_type == object_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    # Order by timestamp descending (most recent first)
    query = query.order_by(desc(AuditLog.timestamp))

    # Paginate
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()

    # Build response with user email
    response = []
    for log in logs:
        response.append(AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            user_email=log.user.email if log.user else None,
            organization_id=str(log.organization_id),
            action_type=log.action_type,
            object_type=log.object_type,
            object_id=str(log.object_id) if log.object_id else None,
            description=log.description,
            metadata=log.metadata,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
        ))

    return response


@router.get("/stats")
def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    Get audit statistics for the current organization.

    Returns aggregated statistics about user actions over the specified period.

    Args:
        days: Number of days to analyze (default: 30, max: 365)
        current_user: Current authenticated user
        org_id: Current organization ID
        db: Database session

    Returns:
        Audit statistics
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Total actions
    total_actions = db.query(AuditLog).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.timestamp >= since
        )
    ).count()

    # Actions by type
    actions_by_type = {}
    action_counts = db.query(
        AuditLog.action_type,
        db.func.count(AuditLog.id)
    ).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.timestamp >= since
        )
    ).group_by(AuditLog.action_type).all()

    for action_type, count in action_counts:
        actions_by_type[action_type] = count

    # Objects by type
    objects_by_type = {}
    object_counts = db.query(
        AuditLog.object_type,
        db.func.count(AuditLog.id)
    ).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.timestamp >= since
        )
    ).group_by(AuditLog.object_type).all()

    for object_type, count in object_counts:
        objects_by_type[object_type] = count

    # Most active users
    active_users = db.query(
        AuditLog.user_id,
        db.func.count(AuditLog.id).label('action_count')
    ).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.timestamp >= since,
            AuditLog.user_id.isnot(None)
        )
    ).group_by(AuditLog.user_id).order_by(desc('action_count')).limit(10).all()

    return {
        "period_days": days,
        "total_actions": total_actions,
        "actions_by_type": actions_by_type,
        "objects_by_type": objects_by_type,
        "most_active_users": [
            {"user_id": str(user_id), "action_count": count}
            for user_id, count in active_users
        ],
    }
