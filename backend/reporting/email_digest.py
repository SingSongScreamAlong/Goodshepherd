"""Email digest service for scheduled report delivery."""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Sequence

from .pdf_export import PDFReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """SMTP server configuration."""

    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_address: str = ""
    from_name: str = "Good Shepherd Alerts"
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "SMTPConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("SMTP_HOST", ""),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            from_address=os.getenv("SMTP_FROM_ADDRESS", ""),
            from_name=os.getenv("SMTP_FROM_NAME", "Good Shepherd Alerts"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        )

    @property
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.host and self.username and self.password and self.from_address)


@dataclass
class DigestSubscription:
    """Email digest subscription configuration."""

    email: str
    name: str = ""
    frequency: str = "daily"  # daily, weekly, immediate
    regions: list[str] = field(default_factory=list)
    min_threat_level: str = "medium"
    include_pdf: bool = True
    enabled: bool = True
    last_sent: Optional[datetime] = None


@dataclass
class EmailResult:
    """Result of an email send attempt."""

    success: bool
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EmailDigestService:
    """Service for sending email digests and alerts."""

    def __init__(self, config: Optional[SMTPConfig] = None):
        self.config = config or SMTPConfig.from_env()
        self._subscriptions: dict[str, DigestSubscription] = {}
        self._pdf_generator = PDFReportGenerator()

    def add_subscription(self, subscription: DigestSubscription) -> None:
        """Add an email subscription."""
        self._subscriptions[subscription.email] = subscription
        logger.info(f"Added email subscription: {subscription.email}")

    def remove_subscription(self, email: str) -> bool:
        """Remove an email subscription."""
        if email in self._subscriptions:
            del self._subscriptions[email]
            return True
        return False

    def get_subscription(self, email: str) -> Optional[DigestSubscription]:
        """Get a subscription by email."""
        return self._subscriptions.get(email)

    def list_subscriptions(self) -> list[DigestSubscription]:
        """List all subscriptions."""
        return list(self._subscriptions.values())

    async def send_digest(
        self,
        subscription: DigestSubscription,
        events: Sequence[dict],
        period_start: datetime,
        period_end: datetime,
    ) -> EmailResult:
        """Send a digest email to a subscriber."""
        if not self.config.is_configured:
            return EmailResult(
                success=False,
                recipient=subscription.email,
                error="SMTP not configured",
            )

        # Filter events for this subscription
        filtered_events = self._filter_events(events, subscription)

        if not filtered_events:
            logger.debug(f"No events to send to {subscription.email}")
            return EmailResult(
                success=True,
                recipient=subscription.email,
                message_id="skipped-no-events",
            )

        # Build email
        subject = self._build_subject(filtered_events, period_start, period_end)
        html_body = self._build_html_body(filtered_events, period_start, period_end, subscription)
        text_body = self._build_text_body(filtered_events, period_start, period_end)

        # Generate PDF attachment if requested
        pdf_attachment = None
        if subscription.include_pdf:
            pdf_attachment = self._pdf_generator.generate_sitrep_pdf(
                title=subject,
                summary=self._generate_summary(filtered_events),
                events=filtered_events,
                stats=self._calculate_stats(filtered_events),
                generated_at=datetime.utcnow(),
                region=subscription.regions[0] if subscription.regions else None,
            )

        # Send email
        result = await self._send_email(
            to_address=subscription.email,
            to_name=subscription.name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            pdf_attachment=pdf_attachment,
        )

        if result.success:
            subscription.last_sent = datetime.utcnow()

        return result

    async def send_immediate_alert(
        self,
        event: dict,
        subscriptions: Optional[list[DigestSubscription]] = None,
    ) -> list[EmailResult]:
        """Send immediate alert for a critical event."""
        if subscriptions is None:
            subscriptions = [
                s for s in self._subscriptions.values()
                if s.enabled and s.frequency == "immediate"
            ]

        results = []
        for subscription in subscriptions:
            if self._should_notify(event, subscription):
                result = await self._send_alert_email(event, subscription)
                results.append(result)

        return results

    async def process_scheduled_digests(self, events: Sequence[dict]) -> list[EmailResult]:
        """Process all scheduled digest subscriptions."""
        now = datetime.utcnow()
        results = []

        for subscription in self._subscriptions.values():
            if not subscription.enabled:
                continue

            should_send = False
            period_start = now

            if subscription.frequency == "daily":
                if subscription.last_sent is None or (now - subscription.last_sent) >= timedelta(hours=24):
                    should_send = True
                    period_start = now - timedelta(hours=24)

            elif subscription.frequency == "weekly":
                if subscription.last_sent is None or (now - subscription.last_sent) >= timedelta(days=7):
                    should_send = True
                    period_start = now - timedelta(days=7)

            if should_send:
                result = await self.send_digest(
                    subscription=subscription,
                    events=events,
                    period_start=period_start,
                    period_end=now,
                )
                results.append(result)

        return results

    def _filter_events(
        self,
        events: Sequence[dict],
        subscription: DigestSubscription,
    ) -> list[dict]:
        """Filter events based on subscription preferences."""
        threat_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_threat = threat_order.get(subscription.min_threat_level.lower(), 1)

        filtered = []
        for event in events:
            # Check threat level
            event_threat = threat_order.get((event.get("threat_level") or "").lower(), 0)
            if event_threat < min_threat:
                continue

            # Check region filter
            if subscription.regions:
                event_region = (event.get("region") or "").lower()
                if not any(r.lower() in event_region for r in subscription.regions):
                    continue

            filtered.append(event)

        return filtered

    def _should_notify(self, event: dict, subscription: DigestSubscription) -> bool:
        """Check if subscription should receive this event."""
        filtered = self._filter_events([event], subscription)
        return len(filtered) > 0

    def _build_subject(
        self,
        events: Sequence[dict],
        period_start: datetime,
        period_end: datetime,
    ) -> str:
        """Build email subject line."""
        critical_count = sum(
            1 for e in events
            if (e.get("threat_level") or "").lower() == "critical"
        )

        if critical_count > 0:
            return f"🚨 Good Shepherd Alert: {critical_count} Critical Events"

        return f"Good Shepherd Digest: {len(events)} Events ({period_start.strftime('%b %d')} - {period_end.strftime('%b %d')})"

    def _build_html_body(
        self,
        events: Sequence[dict],
        period_start: datetime,
        period_end: datetime,
        subscription: DigestSubscription,
    ) -> str:
        """Build HTML email body."""
        threat_colors = {
            "critical": "#ef4444",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#22c55e",
        }

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f3f4f6; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
                .header {{ background: #16a34a; color: white; padding: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 20px; }}
                .summary {{ background: #f9fafb; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
                .event {{ border-left: 4px solid #e5e7eb; padding: 10px 15px; margin-bottom: 15px; }}
                .event-critical {{ border-color: #ef4444; background: #fef2f2; }}
                .event-high {{ border-color: #f97316; background: #fff7ed; }}
                .event-medium {{ border-color: #eab308; background: #fefce8; }}
                .event-low {{ border-color: #22c55e; background: #f0fdf4; }}
                .event-title {{ font-weight: 600; margin-bottom: 5px; }}
                .event-meta {{ font-size: 12px; color: #6b7280; }}
                .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; color: white; }}
                .footer {{ background: #f9fafb; padding: 15px 20px; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Good Shepherd Security Digest</h1>
                    <p style="margin: 5px 0 0; opacity: 0.9;">
                        {period_start.strftime('%B %d')} - {period_end.strftime('%B %d, %Y')}
                    </p>
                </div>
                <div class="content">
                    <div class="summary">
                        <strong>{len(events)} events</strong> in this period
                        {self._get_threat_summary_html(events)}
                    </div>
        """

        # Add events
        for event in events[:20]:
            threat = (event.get("threat_level") or "low").lower()
            color = threat_colors.get(threat, "#6b7280")

            html += f"""
                    <div class="event event-{threat}">
                        <div class="event-title">
                            <span class="badge" style="background: {color};">{threat.upper()}</span>
                            {event.get('title', 'Untitled Event')}
                        </div>
                        <div class="event-meta">
                            📍 {event.get('region', 'Unknown region')} • 
                            {self._format_date(event.get('published_at') or event.get('fetched_at'))}
                        </div>
                    </div>
            """

        if len(events) > 20:
            html += f"""
                    <p style="text-align: center; color: #6b7280;">
                        ... and {len(events) - 20} more events
                    </p>
            """

        html += """
                </div>
                <div class="footer">
                    <p>You're receiving this because you subscribed to Good Shepherd alerts.</p>
                    <p>Good Shepherd - Threat Intelligence for Global Missions</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _build_text_body(
        self,
        events: Sequence[dict],
        period_start: datetime,
        period_end: datetime,
    ) -> str:
        """Build plain text email body."""
        lines = [
            "GOOD SHEPHERD SECURITY DIGEST",
            f"Period: {period_start.strftime('%B %d')} - {period_end.strftime('%B %d, %Y')}",
            "",
            f"Total Events: {len(events)}",
            "",
            "=" * 50,
            "",
        ]

        for event in events[:20]:
            threat = (event.get("threat_level") or "low").upper()
            lines.append(f"[{threat}] {event.get('title', 'Untitled')}")
            lines.append(f"  Region: {event.get('region', 'Unknown')}")
            lines.append("")

        if len(events) > 20:
            lines.append(f"... and {len(events) - 20} more events")

        lines.extend([
            "",
            "=" * 50,
            "Good Shepherd - Threat Intelligence for Global Missions",
        ])

        return "\n".join(lines)

    def _get_threat_summary_html(self, events: Sequence[dict]) -> str:
        """Get HTML summary of threat levels."""
        counts = {}
        for event in events:
            level = (event.get("threat_level") or "unknown").lower()
            counts[level] = counts.get(level, 0) + 1

        parts = []
        for level in ["critical", "high", "medium", "low"]:
            if counts.get(level, 0) > 0:
                parts.append(f"{counts[level]} {level}")

        if parts:
            return f" ({', '.join(parts)})"
        return ""

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format a date string for display."""
        if not date_str:
            return "Unknown date"
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%b %d, %H:%M")
        except (ValueError, AttributeError):
            return str(date_str)[:16]

    def _generate_summary(self, events: Sequence[dict]) -> str:
        """Generate a text summary of events."""
        return f"This digest covers {len(events)} security events."

    def _calculate_stats(self, events: Sequence[dict]) -> dict:
        """Calculate statistics from events."""
        stats = {"total_events": len(events), "by_threat_level": {}}
        for event in events:
            level = (event.get("threat_level") or "unknown").lower()
            stats["by_threat_level"][level] = stats["by_threat_level"].get(level, 0) + 1
        return stats

    async def _send_email(
        self,
        to_address: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str,
        pdf_attachment: Optional[bytes] = None,
    ) -> EmailResult:
        """Send an email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.config.from_name} <{self.config.from_address}>"
            msg["To"] = f"{to_name} <{to_address}>" if to_name else to_address

            # Add text and HTML parts
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Add PDF attachment
            if pdf_attachment:
                pdf_part = MIMEApplication(pdf_attachment, Name="security_digest.pdf")
                pdf_part["Content-Disposition"] = 'attachment; filename="security_digest.pdf"'
                msg.attach(pdf_part)

            # Send via SMTP
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, to_address)

            return EmailResult(
                success=True,
                recipient=to_address,
                message_id=msg.get("Message-ID"),
            )

        except Exception as e:
            logger.error(f"Failed to send email to {to_address}: {e}")
            return EmailResult(
                success=False,
                recipient=to_address,
                error=str(e),
            )

    def _send_smtp(self, msg: MIMEMultipart, to_address: str) -> None:
        """Send email via SMTP (blocking)."""
        with smtplib.SMTP(self.config.host, self.config.port) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.username, self.config.password)
            server.send_message(msg)

    async def _send_alert_email(
        self,
        event: dict,
        subscription: DigestSubscription,
    ) -> EmailResult:
        """Send an immediate alert email for a single event."""
        threat = (event.get("threat_level") or "medium").upper()
        subject = f"🚨 {threat} Alert: {event.get('title', 'Security Event')}"

        html_body = self._build_html_body([event], datetime.utcnow(), datetime.utcnow(), subscription)
        text_body = self._build_text_body([event], datetime.utcnow(), datetime.utcnow())

        return await self._send_email(
            to_address=subscription.email,
            to_name=subscription.name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )


# Global service instance
_email_service: EmailDigestService | None = None


def get_email_service() -> EmailDigestService:
    """Get the global email digest service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailDigestService()
    return _email_service
