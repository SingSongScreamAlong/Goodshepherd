"""Database repository helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AlertRuleRecord, EventRecord, ReportRecord


class EventCreate(BaseModel):
    """Schema representing a normalized event ready for persistence."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = None
    summary: str | None = None
    category: str | None = None
    region: str | None = None
    source_url: str | None = None
    link: str | None = None
    confidence: float = 0.0
    geocode: dict[str, object] | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    raw: str | None = None
    verification_status: str = "pending"
    credibility_score: float = 0.0
    threat_level: str | None = None
    duplicate_of: str | None = None


class ReportCreate(BaseModel):
    """Schema for creating a synthesized report."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str
    summary: str | None = None
    report_type: str = "daily_sitrep"
    region: str | None = None
    generated_at: datetime | None = None
    generated_by: str | None = None
    content: str | None = None
    stats: dict[str, object] | None = None
    source_event_ids: list[str] | None = None


class VerificationUpdate(BaseModel):
    """Schema for updating verification metadata on an event."""

    verification_status: str
    credibility_score: float
    threat_level: str | None = None
    duplicate_of: str | None = None


class AlertRuleCreate(BaseModel):
    """Schema for creating an alert rule."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    description: str | None = None
    regions: list[str] | None = None
    categories: list[str] | None = None
    minimum_threat: str = "medium"
    minimum_credibility: float = 0.6
    lookback_minutes: int = 60
    priority: str = "high"
    auto_ack: bool = False


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""

    name: str | None = None
    description: str | None = None
    regions: list[str] | None = None
    categories: list[str] | None = None
    minimum_threat: str | None = None
    minimum_credibility: float | None = None
    lookback_minutes: int | None = None
    priority: str | None = None
    auto_ack: bool | None = None


async def create_event(session: AsyncSession, event: EventCreate) -> EventRecord:
    """Persist a new event record."""

    record = EventRecord(**event.model_dump(exclude_none=True))
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise
    return record


async def list_recent_events(session: AsyncSession, limit: int = 25) -> Sequence[EventRecord]:
    """Fetch the most recent events ordered by `fetched_at` descending."""

    stmt = select(EventRecord).order_by(EventRecord.fetched_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_events_since(
    session: AsyncSession,
    since: datetime,
    region: str | None = None,
    limit: int = 500,
) -> Sequence[EventRecord]:
    """Return events since the provided timestamp."""

    stmt = select(EventRecord).where(EventRecord.fetched_at >= since)
    if region:
        stmt = stmt.where(EventRecord.region.ilike(region))

    stmt = stmt.order_by(EventRecord.fetched_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_report(session: AsyncSession, report: ReportCreate) -> ReportRecord:
    """Persist a synthesized report."""

    payload = report.model_dump(exclude_none=True)
    if "generated_at" not in payload:
        payload["generated_at"] = datetime.utcnow()
    record = ReportRecord(**payload)
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise
    return record


async def list_reports(session: AsyncSession, limit: int = 20) -> Sequence[ReportRecord]:
    """Fetch recently generated reports."""

    stmt = select(ReportRecord).order_by(ReportRecord.generated_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_report_by_id(session: AsyncSession, report_id: str) -> ReportRecord | None:
    """Fetch a report by identifier."""

    stmt = select(ReportRecord).where(ReportRecord.id == report_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def find_duplicate_candidate(
    session: AsyncSession,
    *,
    link: str | None = None,
    title: str | None = None,
) -> EventRecord | None:
    """Return an existing event that may be a duplicate based on link or title."""

    if not link and not title:
        return None

    stmt = select(EventRecord)
    if link:
        stmt = stmt.where(EventRecord.link == link)
    elif title:
        stmt = stmt.where(func.lower(EventRecord.title) == func.lower(title))

    stmt = stmt.order_by(EventRecord.fetched_at.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_event_verification(
    session: AsyncSession,
    event_id: str,
    update: VerificationUpdate,
) -> EventRecord:
    """Apply verification metadata to an existing event record."""

    record = await get_event_by_id(session, event_id)
    if not record:
        raise ValueError(f"Event {event_id} not found")

    data = update.model_dump()
    for key, value in data.items():
        setattr(record, key, value)

    await session.flush()
    return record


async def create_alert_rule(session: AsyncSession, rule: AlertRuleCreate) -> AlertRuleRecord:
    """Persist a new alert rule."""

    record = AlertRuleRecord(**rule.model_dump(exclude_none=True))
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise
    return record


async def list_alert_rules(session: AsyncSession) -> Sequence[AlertRuleRecord]:
    """Return all alert rules sorted by priority then name."""

    stmt = select(AlertRuleRecord).order_by(AlertRuleRecord.priority.desc(), AlertRuleRecord.name)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_alert_rule(session: AsyncSession, rule_id: str) -> AlertRuleRecord | None:
    """Fetch a single alert rule by identifier."""

    stmt = select(AlertRuleRecord).where(AlertRuleRecord.id == rule_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_alert_rule(
    session: AsyncSession,
    rule_id: str,
    update: AlertRuleUpdate,
) -> AlertRuleRecord:
    """Modify an existing alert rule."""

    record = await get_alert_rule(session, rule_id)
    if not record:
        raise ValueError(f"Alert rule {rule_id} not found")

    for key, value in update.model_dump(exclude_none=True).items():
        setattr(record, key, value)

    await session.flush()
    return record


async def delete_alert_rule(session: AsyncSession, rule_id: str) -> None:
    """Remove an alert rule from the database."""

    record = await get_alert_rule(session, rule_id)
    if not record:
        raise ValueError(f"Alert rule {rule_id} not found")

    await session.delete(record)
    await session.flush()


async def get_event_by_id(session: AsyncSession, event_id: str) -> EventRecord | None:
    """Fetch a single event record by database identifier."""

    stmt = select(EventRecord).where(EventRecord.id == event_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def search_events(
    session: AsyncSession,
    query: str | None = None,
    region: str | None = None,
    limit: int = 25,
) -> Sequence[EventRecord]:
    """Search events with simple text and region filters."""

    stmt = select(EventRecord)

    if query:
        like_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                EventRecord.title.ilike(like_pattern),
                EventRecord.summary.ilike(like_pattern),
                EventRecord.region.ilike(like_pattern),
            )
        )

    if region:
        stmt = stmt.where(EventRecord.region.ilike(region))

    stmt = stmt.order_by(EventRecord.fetched_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()
