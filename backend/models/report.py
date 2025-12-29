"""
Report model for leadership-ready situational reports.
Supports Daily SITREP and Weekly Brief formats.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from backend.core.database import Base


class ReportType(str, enum.Enum):
    """Type of report."""
    DAILY = "daily"      # Daily SITREP
    WEEKLY = "weekly"    # Weekly Brief
    AD_HOC = "ad_hoc"    # Special/ad-hoc report


class ReportStatus(str, enum.Enum):
    """Publication status of report."""
    DRAFT = "draft"          # Being edited
    PENDING = "pending"      # Ready for review
    PUBLISHED = "published"  # Published
    ARCHIVED = "archived"    # Archived


class Report(Base):
    """
    Leadership-ready situational report.
    
    Supports two main formats:
    
    Daily SITREP:
    - Executive summary (auto-generated)
    - Top incidents (admin-selected)
    - Map snapshot
    - Areas to watch
    - Confidence notes
    
    Weekly Brief:
    - Week-in-review
    - Major incidents
    - Trend deltas (migration, geopolitics, security)
    - Forward outlook (7-14 days)
    
    Reports can be exported as Markdown, PDF, or DOCX.
    """
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report identification
    report_type = Column(
        SQLEnum(ReportType),
        nullable=False,
        default=ReportType.DAILY
    )
    title = Column(String(300), nullable=False)
    
    # Scope
    region_scope = Column(
        JSON,
        nullable=True,
        comment="List of region IDs or 'global'"
    )
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Status
    status = Column(
        SQLEnum(ReportStatus),
        nullable=False,
        default=ReportStatus.DRAFT
    )
    
    # Authorship
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Content sections
    executive_summary = Column(
        Text,
        nullable=True,
        comment="Auto-generated or manually written executive summary"
    )
    narrative_markdown = Column(
        Text,
        nullable=True,
        comment="Full report narrative in Markdown"
    )
    
    # Key highlights
    key_developments = Column(
        JSON,
        nullable=True,
        comment="List of key development summaries"
    )
    areas_to_watch = Column(
        JSON,
        nullable=True,
        comment="List of areas requiring attention"
    )
    forward_outlook = Column(
        Text,
        nullable=True,
        comment="7-14 day outlook (for weekly reports)"
    )
    
    # Linked items
    included_incident_ids = Column(
        JSON,
        nullable=True,
        comment="List of incident IDs included in report"
    )
    included_indicator_ids = Column(
        JSON,
        nullable=True,
        comment="List of indicator IDs included in report"
    )
    
    # Map and visual assets
    map_snapshot_url = Column(String(500), nullable=True)
    chart_urls = Column(
        JSON,
        nullable=True,
        comment="List of chart/visualization URLs"
    )
    
    # Export files
    pdf_url = Column(String(500), nullable=True)
    docx_url = Column(String(500), nullable=True)
    
    # Metadata
    confidence_notes = Column(
        Text,
        nullable=True,
        comment="Notes on overall confidence and data limitations"
    )
    distribution_list = Column(
        JSON,
        nullable=True,
        comment="List of recipients/distribution groups"
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    author = relationship("User", backref="reports")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type={self.report_type}, title={self.title}, status={self.status})>"
    
    @property
    def is_published(self) -> bool:
        """Check if report is published."""
        return self.status == ReportStatus.PUBLISHED
    
    @property
    def incident_count(self) -> int:
        """Get count of included incidents."""
        return len(self.included_incident_ids or [])
    
    @property
    def indicator_count(self) -> int:
        """Get count of included indicators."""
        return len(self.included_indicator_ids or [])
    
    def publish(self) -> None:
        """Mark report as published."""
        self.status = ReportStatus.PUBLISHED
        self.published_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive the report."""
        self.status = ReportStatus.ARCHIVED
