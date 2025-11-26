"""
Organization settings model for tenant-level configuration.

Allows each organization to customize platform behavior, alert thresholds,
default filters, and other preferences without code changes.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from backend.core.database import Base


class OrganizationSettings(Base):
    """
    Per-organization configuration settings.

    Stores tenant-specific preferences for filtering, alerts, and UI behavior.
    Enables customization without code deployment.
    """
    __tablename__ = "organization_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,  # One settings record per organization
        index=True
    )

    # Default Filters
    default_categories = Column(JSON, nullable=True)  # List of category strings to show by default
    default_sentiment_filter = Column(String(50), nullable=True)  # "negative", "neutral", "positive", or null for all
    default_min_relevance = Column(Float, nullable=True, default=0.5)  # Minimum relevance score to display

    # Alert Thresholds
    high_priority_threshold = Column(Float, nullable=True, default=0.8)  # Relevance score for high priority
    alert_categories = Column(JSON, nullable=True)  # Categories that trigger alerts
    alert_sentiment_types = Column(JSON, nullable=True)  # Sentiments that trigger alerts

    # Feature Toggles
    enable_email_alerts = Column(Boolean, nullable=False, default=False)
    enable_clustering = Column(Boolean, nullable=False, default=True)
    enable_feedback_collection = Column(Boolean, nullable=False, default=True)
    enable_audit_logging = Column(Boolean, nullable=False, default=True)

    # Display Preferences
    default_map_zoom = Column(Integer, nullable=True, default=5)
    default_map_center_lat = Column(Float, nullable=True)  # Default map center latitude
    default_map_center_lon = Column(Float, nullable=True)  # Default map center longitude
    events_per_page = Column(Integer, nullable=True, default=20)

    # Data Retention
    event_retention_days = Column(Integer, nullable=True)  # Days to keep events (null = indefinite)
    audit_log_retention_days = Column(Integer, nullable=True, default=365)  # Days to keep audit logs

    # Regional Focus
    focus_regions = Column(JSON, nullable=True)  # List of region/country names to prioritize
    exclude_regions = Column(JSON, nullable=True)  # List of regions to completely filter out

    # Custom Configuration
    custom_config = Column(JSON, nullable=True)  # Flexible JSON for future settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    organization = relationship("Organization", backref="settings")
    updated_by_user = relationship("User")

    def __repr__(self) -> str:
        return f"<OrganizationSettings(id={self.id}, org_id={self.organization_id})>"
