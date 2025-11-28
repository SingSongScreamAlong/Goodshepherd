"""SQLAlchemy models for Good Shepherd."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Use JSON for SQLite compatibility, JSONB for PostgreSQL
from sqlalchemy import JSON as JSONType  # type: ignore[misc]


class Base(DeclarativeBase):
    """Base class for declarative models."""


class EventRecord(Base):
    """Persisted representation of a normalized event."""

    __tablename__ = "events"
    __table_args__ = {"comment": "Normalized open-source intelligence events"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    geocode: Mapped[Optional[dict[str, object]]] = mapped_column(JSONType, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="pending")
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    threat_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    duplicate_of: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<EventRecord id={self.id!r} title={self.title!r}>"


class ReportRecord(Base):
    """Persisted situational report synthesized from events."""

    __tablename__ = "reports"
    __table_args__ = {"comment": "Synthesized situational reports and briefs"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(256))
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_type: Mapped[str] = mapped_column(String(64), default="daily_sitrep")
    region: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    generated_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stats: Mapped[Optional[dict[str, object]]] = mapped_column(JSONType, nullable=True)
    source_event_ids: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ReportRecord id={self.id!r} title={self.title!r}>"


class AlertRuleRecord(Base):
    """Stored alert rule configuration."""

    __tablename__ = "alert_rules"
    __table_args__ = {"comment": "Alert rules for automated notifications"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    regions: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)
    categories: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)
    minimum_threat: Mapped[str] = mapped_column(String(16), default="medium")
    minimum_credibility: Mapped[float] = mapped_column(Float, default=0.6)
    lookback_minutes: Mapped[int] = mapped_column(default=60)
    priority: Mapped[str] = mapped_column(String(16), default="high")
    auto_ack: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AlertRuleRecord id={self.id!r} name={self.name!r}>"


class UserRecord(Base):
    """User account for authentication."""

    __tablename__ = "users"
    __table_args__ = {"comment": "User accounts for authentication"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256))
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    roles: Mapped[list[str]] = mapped_column(JSONType, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<UserRecord id={self.id!r} email={self.email!r}>"
