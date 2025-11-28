"""Utilities for synthesizing situational reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from backend.database.models import EventRecord


@dataclass(slots=True)
class ReportParameters:
    """Configuration used when building a report."""

    lookback_hours: int = 24
    region: str | None = None
    title: str = "Daily Situation Report"
    report_type: str = "daily_sitrep"
    generated_by: str = "system"


@dataclass(slots=True)
class ReportSection:
    """Structured section within a report."""

    heading: str
    body: str


@dataclass(slots=True)
class SynthesizedReport:
    """Structured report output ready to persist."""

    title: str
    summary: str
    content: str
    stats: dict[str, object]
    source_event_ids: list[str]
    report_type: str
    region: str | None
    generated_by: str


class SituationReportBuilder:
    """Generate situation reports from event records."""

    def __init__(self, now: datetime | None = None) -> None:
        self.now = now or datetime.utcnow()

    def build(
        self,
        events: Sequence[EventRecord],
        params: ReportParameters,
    ) -> SynthesizedReport:
        """Generate a synthesized report from events."""

        summary_section = self._build_summary(events, params)
        threat_section = self._build_threats(events)
        regional_section = self._build_regional_breakdown(events)

        sections = [summary_section, threat_section, regional_section]

        content = "\n\n".join(
            f"## {section.heading}\n\n{section.body}" for section in sections if section.body
        )

        stats = {
            "total_events": len(events),
            "regions": self._count_by(events, key="region"),
            "categories": self._count_by(events, key="category"),
        }

        summary = summary_section.body.split("\n", 1)[0] if summary_section.body else ""

        return SynthesizedReport(
            title=params.title,
            summary=summary,
            content=content,
            stats=stats,
            source_event_ids=[event.id for event in events],
            report_type=params.report_type,
            region=params.region,
            generated_by=params.generated_by,
        )

    def _build_summary(self, events: Sequence[EventRecord], params: ReportParameters) -> ReportSection:
        if not events:
            body = "No new events recorded in the last 24 hours."
        else:
            top_regions = self._top_items(self._count_by(events, key="region"))
            top_categories = self._top_items(self._count_by(events, key="category"))
            body_lines = [
                f"{len(events)} events recorded in the last {params.lookback_hours} hours.",
                f"Most affected regions: {', '.join(top_regions) if top_regions else 'N/A' }.",
                f"Primary categories: {', '.join(top_categories) if top_categories else 'N/A' }.",
            ]
            body = "\n".join(body_lines)
        return ReportSection(heading="Summary", body=body)

    def _build_threats(self, events: Sequence[EventRecord]) -> ReportSection:
        critical = [event for event in events if (event.category or "").lower() in {"attack", "conflict", "riot"}]
        if not critical:
            body = "No critical security incidents identified."
        else:
            lines = ["Critical incidents:"]
            for event in critical[:5]:
                lines.append(f"- {event.title or 'Untitled'} ({event.region or 'Unknown region'})")
            body = "\n".join(lines)
        return ReportSection(heading="Security Outlook", body=body)

    def _build_regional_breakdown(self, events: Sequence[EventRecord]) -> ReportSection:
        counts = self._count_by(events, key="region")
        if not counts:
            return ReportSection(heading="Regional Breakdown", body="No regional data available.")

        lines = ["Regional event counts:"]
        for region, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- {region or 'Unknown'}: {count}")
        return ReportSection(heading="Regional Breakdown", body="\n".join(lines))

    def _count_by(self, events: Sequence[EventRecord], key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in events:
            value = getattr(event, key, None)
            if not value:
                continue
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _top_items(self, counts: dict[str, int], limit: int = 3) -> list[str]:
        return [item for item, _ in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:limit]]
