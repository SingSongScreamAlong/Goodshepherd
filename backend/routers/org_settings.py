"""
Organization settings API endpoints for tenant-level configuration.

Allows organization administrators to customize platform behavior,
alert thresholds, default filters, and other preferences.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.core.dependencies import get_current_user, get_current_org_id
from backend.models.user import User
from backend.models.org_settings import OrganizationSettings
from backend.core.logging import get_logger
from backend.core.audit import log_audit_action, AuditAction, AuditObjectType

logger = get_logger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])


class OrganizationSettingsResponse(BaseModel):
    """Response schema for organization settings."""
    id: str
    organization_id: str

    # Default Filters
    default_categories: Optional[list] = None
    default_sentiment_filter: Optional[str] = None
    default_min_relevance: Optional[float] = 0.5

    # Alert Thresholds
    high_priority_threshold: Optional[float] = 0.8
    alert_categories: Optional[list] = None
    alert_sentiment_types: Optional[list] = None

    # Feature Toggles
    enable_email_alerts: bool = False
    enable_clustering: bool = True
    enable_feedback_collection: bool = True
    enable_audit_logging: bool = True

    # Display Preferences
    default_map_zoom: Optional[int] = 5
    default_map_center_lat: Optional[float] = None
    default_map_center_lon: Optional[float] = None
    events_per_page: Optional[int] = 20

    # Data Retention
    event_retention_days: Optional[int] = None
    audit_log_retention_days: Optional[int] = 365

    # Regional Focus
    focus_regions: Optional[list] = None
    exclude_regions: Optional[list] = None

    # Custom Configuration
    custom_config: Optional[dict] = None

    class Config:
        from_attributes = True


class OrganizationSettingsUpdate(BaseModel):
    """Schema for updating organization settings."""
    # Default Filters
    default_categories: Optional[list] = None
    default_sentiment_filter: Optional[str] = None
    default_min_relevance: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Alert Thresholds
    high_priority_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    alert_categories: Optional[list] = None
    alert_sentiment_types: Optional[list] = None

    # Feature Toggles
    enable_email_alerts: Optional[bool] = None
    enable_clustering: Optional[bool] = None
    enable_feedback_collection: Optional[bool] = None
    enable_audit_logging: Optional[bool] = None

    # Display Preferences
    default_map_zoom: Optional[int] = Field(None, ge=1, le=20)
    default_map_center_lat: Optional[float] = Field(None, ge=-90, le=90)
    default_map_center_lon: Optional[float] = Field(None, ge=-180, le=180)
    events_per_page: Optional[int] = Field(None, ge=10, le=500)

    # Data Retention
    event_retention_days: Optional[int] = Field(None, ge=1)
    audit_log_retention_days: Optional[int] = Field(None, ge=1)

    # Regional Focus
    focus_regions: Optional[list] = None
    exclude_regions: Optional[list] = None

    # Custom Configuration
    custom_config: Optional[dict] = None


@router.get("", response_model=OrganizationSettingsResponse)
def get_organization_settings(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    Get settings for the current organization.

    Returns organization settings, creating default settings if none exist.

    Args:
        current_user: Current authenticated user
        org_id: Current organization ID
        db: Database session

    Returns:
        Organization settings
    """
    # Get or create settings
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == org_id
    ).first()

    if not settings:
        # Create default settings
        settings = OrganizationSettings(organization_id=org_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

        logger.info(
            "created_default_org_settings",
            organization_id=str(org_id),
            user_id=str(current_user.id)
        )

    return OrganizationSettingsResponse(
        id=str(settings.id),
        organization_id=str(settings.organization_id),
        default_categories=settings.default_categories,
        default_sentiment_filter=settings.default_sentiment_filter,
        default_min_relevance=settings.default_min_relevance,
        high_priority_threshold=settings.high_priority_threshold,
        alert_categories=settings.alert_categories,
        alert_sentiment_types=settings.alert_sentiment_types,
        enable_email_alerts=settings.enable_email_alerts,
        enable_clustering=settings.enable_clustering,
        enable_feedback_collection=settings.enable_feedback_collection,
        enable_audit_logging=settings.enable_audit_logging,
        default_map_zoom=settings.default_map_zoom,
        default_map_center_lat=settings.default_map_center_lat,
        default_map_center_lon=settings.default_map_center_lon,
        events_per_page=settings.events_per_page,
        event_retention_days=settings.event_retention_days,
        audit_log_retention_days=settings.audit_log_retention_days,
        focus_regions=settings.focus_regions,
        exclude_regions=settings.exclude_regions,
        custom_config=settings.custom_config,
    )


@router.put("", response_model=OrganizationSettingsResponse)
def update_organization_settings(
    settings_update: OrganizationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    Update settings for the current organization.

    Only updates fields that are provided (partial update).
    Requires organization admin role.

    Args:
        settings_update: Fields to update
        current_user: Current authenticated user
        org_id: Current organization ID
        db: Database session

    Returns:
        Updated organization settings
    """
    # Get or create settings
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == org_id
    ).first()

    if not settings:
        # Create new settings
        settings = OrganizationSettings(
            organization_id=org_id,
            updated_by_user_id=current_user.id
        )
        db.add(settings)

    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(settings)

    # Log audit action
    try:
        log_audit_action(
            db=db,
            user=current_user,
            organization_id=org_id,
            action_type=AuditAction.UPDATE,
            object_type=AuditObjectType.SETTINGS,
            object_id=settings.id,
            description=f"Updated organization settings",
            metadata=update_data
        )
    except Exception as e:
        logger.error("Failed to log audit action", error=str(e))

    logger.info(
        "updated_org_settings",
        organization_id=str(org_id),
        user_id=str(current_user.id),
        updated_fields=list(update_data.keys())
    )

    return OrganizationSettingsResponse(
        id=str(settings.id),
        organization_id=str(settings.organization_id),
        default_categories=settings.default_categories,
        default_sentiment_filter=settings.default_sentiment_filter,
        default_min_relevance=settings.default_min_relevance,
        high_priority_threshold=settings.high_priority_threshold,
        alert_categories=settings.alert_categories,
        alert_sentiment_types=settings.alert_sentiment_types,
        enable_email_alerts=settings.enable_email_alerts,
        enable_clustering=settings.enable_clustering,
        enable_feedback_collection=settings.enable_feedback_collection,
        enable_audit_logging=settings.enable_audit_logging,
        default_map_zoom=settings.default_map_zoom,
        default_map_center_lat=settings.default_map_center_lat,
        default_map_center_lon=settings.default_map_center_lon,
        events_per_page=settings.events_per_page,
        event_retention_days=settings.event_retention_days,
        audit_log_retention_days=settings.audit_log_retention_days,
        focus_regions=settings.focus_regions,
        exclude_regions=settings.exclude_regions,
        custom_config=settings.custom_config,
    )


@router.post("/reset")
def reset_organization_settings(
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    Reset organization settings to defaults.

    Deletes custom settings, which will cause defaults to be used.
    Requires organization admin role.

    Args:
        current_user: Current authenticated user
        org_id: Current organization ID
        db: Database session

    Returns:
        Success message
    """
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == org_id
    ).first()

    if settings:
        db.delete(settings)
        db.commit()

        # Log audit action
        try:
            log_audit_action(
                db=db,
                user=current_user,
                organization_id=org_id,
                action_type=AuditAction.DELETE,
                object_type=AuditObjectType.SETTINGS,
                object_id=settings.id,
                description="Reset organization settings to defaults"
            )
        except Exception as e:
            logger.error("Failed to log audit action", error=str(e))

        logger.info(
            "reset_org_settings",
            organization_id=str(org_id),
            user_id=str(current_user.id)
        )

    return {"message": "Organization settings reset to defaults"}
