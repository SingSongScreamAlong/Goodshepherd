"""
Audit logging utilities for tracking user actions.

Provides simple helpers for logging user actions throughout the application
for accountability, security, and compliance purposes.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Request

from backend.models.audit import AuditLog
from backend.models.user import User
from backend.core.logging import get_logger

logger = get_logger(__name__)


def log_audit_action(
    db: Session,
    user: User,
    organization_id: UUID,
    action_type: str,
    object_type: str,
    object_id: Optional[UUID] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """
    Log an audit action to the database.

    Args:
        db: Database session
        user: User performing the action
        organization_id: Organization context for the action
        action_type: Type of action (create, update, delete, view, export)
        object_type: Type of object being acted upon (dossier, watchlist, event, etc.)
        object_id: ID of the specific object (optional)
        description: Human-readable description (optional)
        metadata: Additional context data (optional, stored as action_metadata)
        request: FastAPI request object for extracting IP/user agent (optional)

    Returns:
        Created AuditLog entry
    """
    try:
        # Extract IP and user agent from request if available
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Create audit log entry
        audit_entry = AuditLog(
            user_id=user.id,
            organization_id=organization_id,
            action_type=action_type,
            object_type=object_type,
            object_id=object_id,
            description=description,
            action_metadata=metadata,  # Renamed to avoid SQLAlchemy conflict
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)

        # Also log to structured logger
        logger.info(
            "audit_action",
            audit_id=str(audit_entry.id),
            user_id=str(user.id),
            user_email=user.email,
            organization_id=str(organization_id),
            action_type=action_type,
            object_type=object_type,
            object_id=str(object_id) if object_id else None,
            description=description,
        )

        return audit_entry

    except Exception as e:
        logger.error(
            "audit_logging_failed",
            error=str(e),
            user_id=str(user.id),
            action_type=action_type,
            object_type=object_type,
        )
        # Don't fail the main operation if audit logging fails
        # Just log the error and continue
        db.rollback()
        raise


# Common action types (for consistency)
class AuditAction:
    """Standard audit action types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"


# Common object types (for consistency)
class AuditObjectType:
    """Standard audit object types."""
    DOSSIER = "dossier"
    WATCHLIST = "watchlist"
    EVENT = "event"
    USER = "user"
    ORGANIZATION = "organization"
    SETTINGS = "settings"
    SOURCE = "source"
    FEEDBACK = "feedback"
