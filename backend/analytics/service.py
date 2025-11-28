"""Analytics service for dashboard metrics and trends."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EventRecord
from backend.database.session import session_scope

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsSummary:
    """Summary analytics data."""
    total_events: int
    events_change: float
    critical_count: int
    critical_change: float
    verified_count: int
    verified_change: float
    pending_count: int
    pending_change: float
    active_regions: int
    active_sources: int
    by_threat_level: list
    by_category: list


@dataclass
class TrendPoint:
    """Single point in a trend."""
    date: str
    total: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


@dataclass
class RegionStats:
    """Statistics for a region."""
    name: str
    event_count: int
    dominant_threat: str
    trend: float


class AnalyticsService:
    """Service for computing analytics and metrics."""

    async def get_summary(
        self,
        period: str = "7d",
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Get analytics summary for the specified period."""
        days = self._period_to_days(period)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)

        async def _compute(sess: AsyncSession) -> dict:
            # Current period counts
            current_query = select(EventRecord).where(
                EventRecord.fetched_at >= start_date
            )
            current_result = await sess.execute(current_query)
            current_events = current_result.scalars().all()

            # Previous period counts for comparison
            prev_query = select(EventRecord).where(
                and_(
                    EventRecord.fetched_at >= prev_start,
                    EventRecord.fetched_at < start_date,
                )
            )
            prev_result = await sess.execute(prev_query)
            prev_events = prev_result.scalars().all()

            # Compute metrics
            total_events = len(current_events)
            prev_total = len(prev_events)
            events_change = self._compute_change(total_events, prev_total)

            # Threat level counts
            threat_counts = {}
            category_counts = {}
            verified_count = 0
            pending_count = 0
            regions = set()
            sources = set()

            for event in current_events:
                # Threat levels
                level = event.threat_level or "minimal"
                threat_counts[level] = threat_counts.get(level, 0) + 1

                # Categories
                cat = event.category or "unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1

                # Verification status
                if event.verification_status == "verified":
                    verified_count += 1
                elif event.verification_status in ["pending", "unverified"]:
                    pending_count += 1

                # Regions and sources
                if event.region:
                    regions.add(event.region)
                if event.source_url:
                    sources.add(event.source_url.split("/")[2] if "/" in event.source_url else event.source_url)

            # Previous period counts for changes
            prev_critical = sum(1 for e in prev_events if e.threat_level == "critical")
            prev_verified = sum(1 for e in prev_events if e.verification_status == "verified")
            prev_pending = sum(1 for e in prev_events if e.verification_status in ["pending", "unverified"])

            critical_count = threat_counts.get("critical", 0)

            return {
                "total_events": total_events,
                "events_change": events_change,
                "critical_count": critical_count,
                "critical_change": self._compute_change(critical_count, prev_critical),
                "verified_count": verified_count,
                "verified_change": self._compute_change(verified_count, prev_verified),
                "pending_count": pending_count,
                "pending_change": self._compute_change(pending_count, prev_pending),
                "active_regions": len(regions),
                "active_sources": len(sources),
                "by_threat_level": [
                    {"label": level, "value": count}
                    for level, count in sorted(threat_counts.items(), key=lambda x: -x[1])
                ],
                "by_category": [
                    {"label": cat, "value": count}
                    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])
                ],
            }

        if session:
            return await _compute(session)
        else:
            async with session_scope() as sess:
                return await _compute(sess)

    async def get_trends(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "day",
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Get event trends over time."""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        async def _compute(sess: AsyncSession) -> dict:
            query = select(EventRecord).where(
                and_(
                    EventRecord.fetched_at >= start,
                    EventRecord.fetched_at <= end,
                )
            )
            result = await sess.execute(query)
            events = result.scalars().all()

            # Group by date
            trends = {}
            for event in events:
                if granularity == "hour":
                    key = event.fetched_at.strftime("%Y-%m-%d %H:00")
                else:
                    key = event.fetched_at.strftime("%Y-%m-%d")

                if key not in trends:
                    trends[key] = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}

                trends[key]["total"] += 1
                level = event.threat_level or "minimal"
                if level in trends[key]:
                    trends[key][level] += 1

            # Convert to list
            trend_list = [
                {
                    "date": date,
                    **counts,
                }
                for date, counts in sorted(trends.items())
            ]

            return {"trends": trend_list}

        if session:
            return await _compute(session)
        else:
            async with session_scope() as sess:
                return await _compute(sess)

    async def get_regional_breakdown(
        self,
        period: str = "7d",
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Get breakdown by region."""
        days = self._period_to_days(period)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)

        async def _compute(sess: AsyncSession) -> dict:
            # Current period
            current_query = select(EventRecord).where(
                EventRecord.fetched_at >= start_date
            )
            current_result = await sess.execute(current_query)
            current_events = current_result.scalars().all()

            # Previous period
            prev_query = select(EventRecord).where(
                and_(
                    EventRecord.fetched_at >= prev_start,
                    EventRecord.fetched_at < start_date,
                )
            )
            prev_result = await sess.execute(prev_query)
            prev_events = prev_result.scalars().all()

            # Group by region
            current_regions = {}
            for event in current_events:
                region = event.region or "Unknown"
                if region not in current_regions:
                    current_regions[region] = {"count": 0, "threats": {}}
                current_regions[region]["count"] += 1
                level = event.threat_level or "minimal"
                current_regions[region]["threats"][level] = current_regions[region]["threats"].get(level, 0) + 1

            prev_regions = {}
            for event in prev_events:
                region = event.region or "Unknown"
                prev_regions[region] = prev_regions.get(region, 0) + 1

            # Build region stats
            regions = []
            for region, data in sorted(current_regions.items(), key=lambda x: -x[1]["count"]):
                # Find dominant threat
                dominant = max(data["threats"].items(), key=lambda x: x[1])[0] if data["threats"] else "minimal"
                prev_count = prev_regions.get(region, 0)
                trend = self._compute_change(data["count"], prev_count)

                regions.append({
                    "name": region,
                    "event_count": data["count"],
                    "dominant_threat": dominant,
                    "trend": trend,
                })

            return {"regions": regions[:20]}  # Top 20 regions

        if session:
            return await _compute(session)
        else:
            async with session_scope() as sess:
                return await _compute(sess)

    async def get_timeline_events(
        self,
        start_date: str,
        end_date: str,
        category: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 200,
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Get events for timeline visualization."""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) + timedelta(days=1)  # Include end date

        async def _compute(sess: AsyncSession) -> dict:
            conditions = [
                EventRecord.fetched_at >= start,
                EventRecord.fetched_at < end,
            ]
            if category:
                conditions.append(EventRecord.category == category)
            if region:
                conditions.append(EventRecord.region.ilike(f"%{region}%"))

            query = (
                select(EventRecord)
                .where(and_(*conditions))
                .order_by(EventRecord.fetched_at.desc())
                .limit(limit)
            )
            result = await sess.execute(query)
            events = result.scalars().all()

            return {
                "events": [
                    {
                        "id": str(event.id),
                        "title": event.title,
                        "summary": event.summary,
                        "category": event.category,
                        "threat_level": event.threat_level,
                        "region": event.region,
                        "published_at": event.published_at.isoformat() if event.published_at else None,
                        "fetched_at": event.fetched_at.isoformat() if event.fetched_at else None,
                        "source_url": event.source_url,
                        "link": event.link,
                        "credibility_score": event.credibility_score,
                        "verification_status": event.verification_status,
                        "geocode": event.geocode,
                    }
                    for event in events
                ],
                "total": len(events),
            }

        if session:
            return await _compute(session)
        else:
            async with session_scope() as sess:
                return await _compute(sess)

    async def get_review_queue(
        self,
        status: str = "pending",
        priority: Optional[str] = None,
        limit: int = 50,
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Get events for analyst review queue."""
        async def _compute(sess: AsyncSession) -> dict:
            conditions = []

            # Status filter
            if status == "pending":
                conditions.append(
                    EventRecord.verification_status.in_(["pending", "unverified", None])
                )
            elif status == "flagged":
                conditions.append(EventRecord.verification_status == "flagged")
            elif status == "verified":
                conditions.append(EventRecord.verification_status == "verified")

            # Priority filter (based on threat level)
            if priority == "urgent":
                conditions.append(EventRecord.threat_level == "critical")
            elif priority == "high":
                conditions.append(EventRecord.threat_level.in_(["critical", "high"]))

            query = (
                select(EventRecord)
                .where(and_(*conditions) if conditions else True)
                .order_by(
                    # Order by threat level priority
                    func.case(
                        (EventRecord.threat_level == "critical", 1),
                        (EventRecord.threat_level == "high", 2),
                        (EventRecord.threat_level == "medium", 3),
                        (EventRecord.threat_level == "low", 4),
                        else_=5,
                    ),
                    EventRecord.fetched_at.desc(),
                )
                .limit(limit)
            )
            result = await sess.execute(query)
            events = result.scalars().all()

            # Compute stats
            all_pending = await sess.execute(
                select(func.count(EventRecord.id)).where(
                    EventRecord.verification_status.in_(["pending", "unverified", None])
                )
            )
            pending_count = all_pending.scalar() or 0

            urgent_count = await sess.execute(
                select(func.count(EventRecord.id)).where(
                    and_(
                        EventRecord.verification_status.in_(["pending", "unverified", None]),
                        EventRecord.threat_level == "critical",
                    )
                )
            )
            urgent = urgent_count.scalar() or 0

            return {
                "items": [
                    {
                        "id": str(event.id),
                        "title": event.title,
                        "summary": event.summary,
                        "category": event.category,
                        "threat_level": event.threat_level,
                        "priority": "urgent" if event.threat_level == "critical" else (
                            "high" if event.threat_level == "high" else "normal"
                        ),
                        "region": event.region,
                        "fetched_at": event.fetched_at.isoformat() if event.fetched_at else None,
                        "source_url": event.source_url,
                        "link": event.link,
                        "credibility_score": event.credibility_score,
                        "verification_status": event.verification_status,
                        "ml_analysis": self._extract_ml_analysis(event.raw),
                    }
                    for event in events
                ],
                "stats": {
                    "pending": pending_count,
                    "urgent": urgent,
                    "verified_today": 0,  # Would need additional query
                    "flagged": 0,
                },
            }

        if session:
            return await _compute(session)
        else:
            async with session_scope() as sess:
                return await _compute(sess)

    def _period_to_days(self, period: str) -> int:
        """Convert period string to days."""
        mapping = {
            "24h": 1,
            "7d": 7,
            "30d": 30,
            "90d": 90,
        }
        return mapping.get(period, 7)

    def _compute_change(self, current: int, previous: int) -> float:
        """Compute percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    def _extract_ml_analysis(self, raw: Optional[str]) -> Optional[dict]:
        """Extract ML analysis from raw JSON."""
        if not raw:
            return None
        try:
            import json
            data = json.loads(raw)
            return data.get("ml_analysis")
        except (json.JSONDecodeError, TypeError):
            return None


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
