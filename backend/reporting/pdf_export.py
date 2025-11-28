"""PDF report generation for Good Shepherd."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

logger = logging.getLogger(__name__)

# Note: In production, you'd use a library like reportlab, weasyprint, or fpdf
# This implementation provides the structure and can be extended with actual PDF generation


@dataclass
class PDFStyle:
    """PDF styling configuration."""

    title_font_size: int = 24
    heading_font_size: int = 16
    body_font_size: int = 11
    primary_color: str = "#16a34a"  # Green
    danger_color: str = "#ef4444"   # Red
    warning_color: str = "#f97316"  # Orange
    margin: int = 50
    page_width: int = 612   # Letter size
    page_height: int = 792


@dataclass
class ReportSection:
    """A section of the PDF report."""

    title: str
    content: str
    threat_level: Optional[str] = None
    items: Optional[list[dict]] = None


class PDFReportGenerator:
    """Generates PDF reports from situational data."""

    def __init__(self, style: Optional[PDFStyle] = None):
        self.style = style or PDFStyle()

    def generate_sitrep_pdf(
        self,
        title: str,
        summary: str,
        events: Sequence[dict],
        stats: dict,
        generated_at: datetime,
        region: Optional[str] = None,
    ) -> bytes:
        """Generate a situational report PDF.
        
        Returns PDF content as bytes.
        """
        # Build report structure
        sections = []

        # Executive Summary
        sections.append(ReportSection(
            title="Executive Summary",
            content=summary,
        ))

        # Statistics
        stats_content = self._format_stats(stats)
        sections.append(ReportSection(
            title="Key Statistics",
            content=stats_content,
        ))

        # Threat Overview by Level
        threat_sections = self._group_events_by_threat(events)
        for threat_level, threat_events in threat_sections.items():
            if threat_events:
                sections.append(ReportSection(
                    title=f"{threat_level.upper()} Threat Events",
                    content=f"{len(threat_events)} events at {threat_level} threat level",
                    threat_level=threat_level,
                    items=threat_events,
                ))

        # Generate PDF content
        pdf_content = self._render_pdf(
            title=title,
            sections=sections,
            generated_at=generated_at,
            region=region,
        )

        return pdf_content

    def generate_daily_digest_pdf(
        self,
        events: Sequence[dict],
        date: datetime,
        region: Optional[str] = None,
    ) -> bytes:
        """Generate a daily digest PDF."""
        title = f"Daily Security Digest - {date.strftime('%B %d, %Y')}"
        if region:
            title += f" ({region})"

        # Calculate stats
        stats = self._calculate_stats(events)

        # Generate summary
        summary = self._generate_summary(events, stats)

        return self.generate_sitrep_pdf(
            title=title,
            summary=summary,
            events=events,
            stats=stats,
            generated_at=datetime.utcnow(),
            region=region,
        )

    def _format_stats(self, stats: dict) -> str:
        """Format statistics as readable text."""
        lines = []

        if "total_events" in stats:
            lines.append(f"Total Events: {stats['total_events']}")

        if "by_threat_level" in stats:
            lines.append("\nBy Threat Level:")
            for level, count in stats["by_threat_level"].items():
                lines.append(f"  • {level.capitalize()}: {count}")

        if "by_category" in stats:
            lines.append("\nBy Category:")
            for category, count in list(stats["by_category"].items())[:5]:
                lines.append(f"  • {category}: {count}")

        if "by_region" in stats:
            lines.append("\nBy Region:")
            for region, count in list(stats["by_region"].items())[:5]:
                lines.append(f"  • {region}: {count}")

        return "\n".join(lines)

    def _group_events_by_threat(self, events: Sequence[dict]) -> dict[str, list[dict]]:
        """Group events by threat level."""
        groups = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        for event in events:
            level = (event.get("threat_level") or "low").lower()
            if level in groups:
                groups[level].append(event)

        return groups

    def _calculate_stats(self, events: Sequence[dict]) -> dict:
        """Calculate statistics from events."""
        stats = {
            "total_events": len(events),
            "by_threat_level": {},
            "by_category": {},
            "by_region": {},
        }

        for event in events:
            # Count by threat level
            level = (event.get("threat_level") or "unknown").lower()
            stats["by_threat_level"][level] = stats["by_threat_level"].get(level, 0) + 1

            # Count by category
            category = event.get("category") or "uncategorized"
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # Count by region
            region = event.get("region") or "unknown"
            stats["by_region"][region] = stats["by_region"].get(region, 0) + 1

        return stats

    def _generate_summary(self, events: Sequence[dict], stats: dict) -> str:
        """Generate an executive summary."""
        total = stats.get("total_events", 0)
        critical = stats.get("by_threat_level", {}).get("critical", 0)
        high = stats.get("by_threat_level", {}).get("high", 0)

        summary_parts = [
            f"This report covers {total} security events.",
        ]

        if critical > 0:
            summary_parts.append(f"⚠️ {critical} CRITICAL threat events require immediate attention.")

        if high > 0:
            summary_parts.append(f"{high} high-priority events are being monitored.")

        # Top regions
        top_regions = sorted(
            stats.get("by_region", {}).items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        if top_regions:
            regions_str = ", ".join(f"{r[0]} ({r[1]})" for r in top_regions)
            summary_parts.append(f"Most affected regions: {regions_str}")

        return " ".join(summary_parts)

    def _render_pdf(
        self,
        title: str,
        sections: list[ReportSection],
        generated_at: datetime,
        region: Optional[str] = None,
    ) -> bytes:
        """Render the PDF content.
        
        This is a placeholder that generates a text-based representation.
        In production, replace with actual PDF library (reportlab, weasyprint, etc.)
        """
        # For now, generate a formatted text document
        # In production, this would use reportlab or similar

        output = io.StringIO()

        # Header
        output.write("=" * 60 + "\n")
        output.write(f"{title}\n")
        output.write("=" * 60 + "\n\n")

        output.write(f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M UTC')}\n")
        if region:
            output.write(f"Region: {region}\n")
        output.write("\n")

        # Sections
        for section in sections:
            output.write("-" * 40 + "\n")
            output.write(f"{section.title}\n")
            output.write("-" * 40 + "\n\n")

            output.write(f"{section.content}\n\n")

            if section.items:
                for i, item in enumerate(section.items[:10], 1):
                    output.write(f"{i}. {item.get('title', 'Untitled')}\n")
                    if item.get("region"):
                        output.write(f"   Region: {item['region']}\n")
                    if item.get("summary"):
                        summary = item["summary"][:150]
                        output.write(f"   {summary}...\n")
                    output.write("\n")

                if len(section.items) > 10:
                    output.write(f"   ... and {len(section.items) - 10} more events\n\n")

        # Footer
        output.write("\n" + "=" * 60 + "\n")
        output.write("Good Shepherd - Threat Intelligence Platform\n")
        output.write("CONFIDENTIAL - For authorized personnel only\n")
        output.write("=" * 60 + "\n")

        # Convert to bytes (in production, this would be actual PDF bytes)
        content = output.getvalue()
        return content.encode("utf-8")


def generate_pdf_report(
    title: str,
    events: Sequence[dict],
    region: Optional[str] = None,
) -> bytes:
    """Convenience function to generate a PDF report."""
    generator = PDFReportGenerator()

    stats = generator._calculate_stats(events)
    summary = generator._generate_summary(events, stats)

    return generator.generate_sitrep_pdf(
        title=title,
        summary=summary,
        events=events,
        stats=stats,
        generated_at=datetime.utcnow(),
        region=region,
    )
