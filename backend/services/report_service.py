"""
Report Service for generating Daily SITREP and Weekly Brief reports.
Provides leadership-ready situational awareness summaries.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json

from backend.core.logging import get_logger
from backend.core.database import SessionLocal
from backend.models.event import Event, EventCategory, IncidentStatus, IncidentSeverity
from backend.models.indicator import Indicator
from backend.models.region import Region, RegionStatus
from backend.models.report import Report, ReportType, ReportStatus

logger = get_logger(__name__)


class ReportService:
    """
    Service for generating leadership-ready reports.
    
    Supports:
    - Daily SITREP (situation report)
    - Weekly Brief
    - Ad-hoc reports
    
    Each report includes:
    - Executive summary (auto-generated)
    - Key incidents
    - Region status changes
    - Trend analysis
    - Forward outlook
    """
    
    def __init__(self):
        """Initialize report service."""
        pass
    
    def generate_daily_sitrep(
        self,
        author_id: UUID,
        region_scope: Optional[List[UUID]] = None,
        title: Optional[str] = None
    ) -> Report:
        """
        Generate a Daily SITREP.
        
        Args:
            author_id: ID of report author
            region_scope: Optional list of region IDs (None = global)
            title: Optional custom title
            
        Returns:
            Generated Report object
        """
        db = SessionLocal()
        
        try:
            # Get date range (last 24 hours)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=24)
            
            # Get incidents from last 24 hours
            incidents = self._get_incidents_in_range(
                db, start_date, end_date, region_scope
            )
            
            # Get top incidents by severity/priority
            top_incidents = self._select_top_incidents(incidents, limit=10)
            
            # Get regions with status changes
            regions_changed = self._get_regions_status_changed(
                db, start_date, region_scope
            )
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                incidents=incidents,
                top_incidents=top_incidents,
                regions_changed=regions_changed,
                period="24 hours"
            )
            
            # Generate narrative
            narrative = self._generate_daily_narrative(
                incidents=incidents,
                top_incidents=top_incidents,
                regions_changed=regions_changed
            )
            
            # Get areas to watch
            areas_to_watch = self._identify_areas_to_watch(db, incidents)
            
            # Create report
            report = Report(
                report_type=ReportType.DAILY,
                title=title or f"Daily SITREP - {end_date.strftime('%Y-%m-%d')}",
                region_scope={"regions": [str(r) for r in region_scope]} if region_scope else {"scope": "global"},
                period_start=start_date,
                period_end=end_date,
                status=ReportStatus.DRAFT,
                created_by=author_id,
                executive_summary=executive_summary,
                narrative_markdown=narrative,
                key_developments=self._format_key_developments(top_incidents),
                areas_to_watch=areas_to_watch,
                included_incident_ids=[str(i.id) for i in top_incidents],
                confidence_notes=self._generate_confidence_notes(incidents)
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            logger.info(
                "Daily SITREP generated",
                report_id=str(report.id),
                incidents_included=len(top_incidents)
            )
            
            return report
            
        finally:
            db.close()
    
    def generate_weekly_brief(
        self,
        author_id: UUID,
        region_scope: Optional[List[UUID]] = None,
        title: Optional[str] = None
    ) -> Report:
        """
        Generate a Weekly Brief.
        
        Args:
            author_id: ID of report author
            region_scope: Optional list of region IDs
            title: Optional custom title
            
        Returns:
            Generated Report object
        """
        db = SessionLocal()
        
        try:
            # Get date range (last 7 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            # Get incidents from last week
            incidents = self._get_incidents_in_range(
                db, start_date, end_date, region_scope
            )
            
            # Get major incidents
            major_incidents = self._select_top_incidents(incidents, limit=20)
            
            # Get trend data
            trend_data = self._calculate_weekly_trends(db, start_date, end_date)
            
            # Get forward outlook
            forward_outlook = self._generate_forward_outlook(
                db, incidents, trend_data
            )
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                incidents=incidents,
                top_incidents=major_incidents,
                regions_changed=[],
                period="7 days"
            )
            
            # Generate narrative
            narrative = self._generate_weekly_narrative(
                incidents=incidents,
                major_incidents=major_incidents,
                trends=trend_data
            )
            
            # Create report
            report = Report(
                report_type=ReportType.WEEKLY,
                title=title or f"Weekly Brief - Week of {start_date.strftime('%Y-%m-%d')}",
                region_scope={"regions": [str(r) for r in region_scope]} if region_scope else {"scope": "global"},
                period_start=start_date,
                period_end=end_date,
                status=ReportStatus.DRAFT,
                created_by=author_id,
                executive_summary=executive_summary,
                narrative_markdown=narrative,
                key_developments=self._format_key_developments(major_incidents),
                forward_outlook=forward_outlook,
                included_incident_ids=[str(i.id) for i in major_incidents],
                confidence_notes=self._generate_confidence_notes(incidents)
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            logger.info(
                "Weekly Brief generated",
                report_id=str(report.id),
                incidents_included=len(major_incidents)
            )
            
            return report
            
        finally:
            db.close()
    
    def _get_incidents_in_range(
        self,
        db,
        start: datetime,
        end: datetime,
        region_ids: Optional[List[UUID]] = None
    ) -> List[Event]:
        """Get incidents within date range."""
        query = db.query(Event).filter(
            Event.timestamp >= start,
            Event.timestamp <= end,
            Event.status != IncidentStatus.DEBUNKED
        )
        
        if region_ids:
            query = query.filter(Event.region_id.in_(region_ids))
        
        return query.order_by(Event.timestamp.desc()).all()
    
    def _select_top_incidents(
        self,
        incidents: List[Event],
        limit: int = 10
    ) -> List[Event]:
        """Select top incidents by severity and confidence."""
        # Score incidents
        def score_incident(inc: Event) -> float:
            severity_scores = {
                IncidentSeverity.CRITICAL: 4,
                IncidentSeverity.HIGH: 3,
                IncidentSeverity.MEDIUM: 2,
                IncidentSeverity.LOW: 1
            }
            status_scores = {
                IncidentStatus.CONFIRMED: 1.0,
                IncidentStatus.CORROBORATED: 0.8,
                IncidentStatus.DEVELOPING: 0.5,
                IncidentStatus.UNVERIFIED: 0.2
            }
            
            sev = severity_scores.get(inc.severity, 2)
            stat = status_scores.get(inc.status, 0.5)
            conf = inc.confidence_score or 0.5
            
            return sev * stat * conf
        
        scored = sorted(incidents, key=score_incident, reverse=True)
        return scored[:limit]
    
    def _get_regions_status_changed(
        self,
        db,
        since: datetime,
        region_ids: Optional[List[UUID]] = None
    ) -> List[Dict]:
        """Get regions that changed status."""
        query = db.query(Region).filter(
            Region.status_updated_at >= since
        )
        
        if region_ids:
            query = query.filter(Region.id.in_(region_ids))
        
        regions = query.all()
        
        return [
            {
                "region_id": str(r.id),
                "name": r.name,
                "status": r.status.value,
                "reason": r.status_reason
            }
            for r in regions
        ]
    
    def _generate_executive_summary(
        self,
        incidents: List[Event],
        top_incidents: List[Event],
        regions_changed: List[Dict],
        period: str
    ) -> str:
        """Generate executive summary paragraph."""
        # Count by severity
        critical = sum(1 for i in incidents if i.severity == IncidentSeverity.CRITICAL)
        high = sum(1 for i in incidents if i.severity == IncidentSeverity.HIGH)
        
        # Count by category
        categories = {}
        for inc in incidents:
            cat = inc.category.value
            categories[cat] = categories.get(cat, 0) + 1
        
        top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "various"
        
        summary_parts = [
            f"**Period Coverage:** Last {period}",
            f"**Total Incidents:** {len(incidents)}",
        ]
        
        if critical > 0:
            summary_parts.append(f"**Critical Incidents:** {critical}")
        if high > 0:
            summary_parts.append(f"**High-Priority Incidents:** {high}")
        
        summary_parts.append(f"**Primary Category:** {top_category.replace('_', ' ').title()}")
        
        if regions_changed:
            summary_parts.append(f"**Regions with Status Changes:** {len(regions_changed)}")
        
        return "\n".join(summary_parts)
    
    def _generate_daily_narrative(
        self,
        incidents: List[Event],
        top_incidents: List[Event],
        regions_changed: List[Dict]
    ) -> str:
        """Generate daily narrative markdown."""
        sections = ["# Daily Situation Report\n"]
        
        # Top incidents section
        sections.append("## Key Developments\n")
        for i, inc in enumerate(top_incidents[:5], 1):
            status_emoji = {
                IncidentStatus.CONFIRMED: "✅",
                IncidentStatus.CORROBORATED: "🔵",
                IncidentStatus.DEVELOPING: "🟡",
                IncidentStatus.UNVERIFIED: "⚪"
            }.get(inc.status, "⚪")
            
            severity_marker = {
                IncidentSeverity.CRITICAL: "🔴",
                IncidentSeverity.HIGH: "🟠",
                IncidentSeverity.MEDIUM: "🟡",
                IncidentSeverity.LOW: "🟢"
            }.get(inc.severity, "⚪")
            
            sections.append(
                f"{i}. {severity_marker} **{inc.title or inc.summary[:80]}** "
                f"({inc.category.value.replace('_', ' ')}) {status_emoji}\n"
                f"   - Location: {inc.location_name or 'Unknown'}\n"
                f"   - Confidence: {int((inc.confidence_score or 0) * 100)}%\n"
            )
        
        # Region status section
        if regions_changed:
            sections.append("\n## Region Status Changes\n")
            for region in regions_changed:
                sections.append(
                    f"- **{region['name']}**: Now {region['status'].upper()}\n"
                )
        
        # Statistics section
        sections.append("\n## Statistics\n")
        sections.append(f"- Total incidents tracked: {len(incidents)}\n")
        
        return "\n".join(sections)
    
    def _generate_weekly_narrative(
        self,
        incidents: List[Event],
        major_incidents: List[Event],
        trends: Dict
    ) -> str:
        """Generate weekly narrative markdown."""
        sections = ["# Weekly Intelligence Brief\n"]
        
        sections.append("## Week in Review\n")
        sections.append(
            f"This week saw {len(incidents)} tracked incidents "
            f"across monitored regions.\n"
        )
        
        sections.append("\n## Major Incidents\n")
        for i, inc in enumerate(major_incidents[:10], 1):
            sections.append(
                f"{i}. **{inc.title or inc.summary[:80]}**\n"
                f"   - Category: {inc.category.value.replace('_', ' ')}\n"
                f"   - Severity: {inc.severity.value}\n"
            )
        
        sections.append("\n## Trend Analysis\n")
        sections.append(
            "See indicator dashboard for detailed trend breakdowns.\n"
        )
        
        return "\n".join(sections)
    
    def _calculate_weekly_trends(
        self,
        db,
        start: datetime,
        end: datetime
    ) -> Dict:
        """Calculate trend data for the week."""
        # Placeholder for trend calculations
        return {
            "incident_count_prev_week": 0,
            "incident_count_current": 0,
            "category_changes": {}
        }
    
    def _generate_forward_outlook(
        self,
        db,
        incidents: List[Event],
        trends: Dict
    ) -> str:
        """Generate 7-14 day forward outlook."""
        return (
            "## Forward Outlook (7-14 Days)\n\n"
            "Based on current trends and developing situations, "
            "analysts should monitor:\n\n"
            "- Regions with elevated status\n"
            "- Developing incidents requiring verification\n"
            "- Indicators showing significant delta changes\n"
        )
    
    def _identify_areas_to_watch(
        self,
        db,
        incidents: List[Event]
    ) -> List[Dict]:
        """Identify areas requiring attention."""
        areas = []
        
        # Find locations with multiple incidents
        location_counts = {}
        for inc in incidents:
            if inc.location_name:
                location_counts[inc.location_name] = location_counts.get(inc.location_name, 0) + 1
        
        for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            if count >= 2:
                areas.append({
                    "location": loc,
                    "incident_count": count,
                    "reason": "Multiple incidents in this area"
                })
        
        return areas
    
    def _format_key_developments(
        self,
        incidents: List[Event]
    ) -> List[Dict]:
        """Format key developments for JSON storage."""
        return [
            {
                "id": str(inc.id),
                "title": inc.title or inc.summary[:100],
                "category": inc.category.value,
                "severity": inc.severity.value,
                "location": inc.location_name
            }
            for inc in incidents
        ]
    
    def _generate_confidence_notes(
        self,
        incidents: List[Event]
    ) -> str:
        """Generate notes about overall confidence levels."""
        confirmed = sum(1 for i in incidents if i.status == IncidentStatus.CONFIRMED)
        corroborated = sum(1 for i in incidents if i.status == IncidentStatus.CORROBORATED)
        developing = sum(1 for i in incidents if i.status == IncidentStatus.DEVELOPING)
        unverified = sum(1 for i in incidents if i.status == IncidentStatus.UNVERIFIED)
        
        return (
            f"**Verification Status Summary:**\n"
            f"- Confirmed: {confirmed}\n"
            f"- Corroborated: {corroborated}\n"
            f"- Developing: {developing}\n"
            f"- Unverified: {unverified}\n\n"
            f"Note: Unverified and developing incidents should be treated as claims "
            f"pending additional verification."
        )


# Global service instance
report_service = ReportService()
