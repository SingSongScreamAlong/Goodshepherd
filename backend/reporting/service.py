"""High-level reporting service orchestrations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repository import (
    ReportCreate,
    create_report,
    list_events_since,
)

from .sitrep_builder import ReportParameters, SituationReportBuilder


async def generate_sitrep(
    session: AsyncSession,
    *,
    lookback_hours: int = 24,
    region: str | None = None,
    title: str | None = None,
    generated_by: str = "system",
    report_type: str = "daily_sitrep",
) -> str:
    """Generate, persist, and return the ID of a situation report."""

    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
    events = await list_events_since(session, since=cutoff, region=region)

    params = ReportParameters(
        lookback_hours=lookback_hours,
        region=region,
        title=title or _default_title(report_type, region),
        report_type=report_type,
        generated_by=generated_by,
    )

    builder = SituationReportBuilder()
    synthesized = builder.build(events, params)

    record = await create_report(
        session,
        ReportCreate(
            title=synthesized.title,
            summary=synthesized.summary,
            report_type=synthesized.report_type,
            region=synthesized.region,
            generated_at=datetime.utcnow(),
            generated_by=synthesized.generated_by,
            content=synthesized.content,
            stats=synthesized.stats,
            source_event_ids=synthesized.source_event_ids,
        ),
    )
    return record.id


def _default_title(report_type: str, region: Optional[str]) -> str:
    base = {
        "daily_sitrep": "Daily Situation Report",
        "weekly_overview": "Weekly Security Overview",
    }.get(report_type, "Situation Report")
    if region:
        return f"{base} - {region.upper()}"
    return base
