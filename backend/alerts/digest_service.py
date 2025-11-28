"""Digest service for batched alert notifications."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EventRecord, AlertRuleRecord, UserRecord
from .notification_preferences import (
    NotificationPreferencesRecord,
    DigestFrequency,
    SentNotificationRecord,
)

logger = logging.getLogger(__name__)


@dataclass
class DigestEvent:
    """Event summary for digest."""
    id: str
    title: str
    summary: Optional[str]
    region: Optional[str]
    category: Optional[str]
    threat_level: Optional[str]
    credibility_score: float
    link: Optional[str]
    published_at: Optional[datetime]
    rule_name: str
    priority: str


@dataclass
class DigestContent:
    """Content for a digest email."""
    user_id: str
    user_email: str
    user_name: Optional[str]
    frequency: DigestFrequency
    events: list[DigestEvent]
    period_start: datetime
    period_end: datetime


class DigestService:
    """Service for generating and sending digest emails."""

    def __init__(self):
        import os
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "alerts@goodshepherd.org")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Good Shepherd Alerts")

    @property
    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    async def generate_hourly_digests(self, session: AsyncSession) -> int:
        """Generate and send hourly digests."""
        return await self._generate_digests(session, DigestFrequency.HOURLY, hours=1)

    async def generate_daily_digests(self, session: AsyncSession) -> int:
        """Generate and send daily digests."""
        return await self._generate_digests(session, DigestFrequency.DAILY, hours=24)

    async def generate_weekly_digests(self, session: AsyncSession) -> int:
        """Generate and send weekly digests."""
        return await self._generate_digests(session, DigestFrequency.WEEKLY, hours=168)

    async def _generate_digests(
        self,
        session: AsyncSession,
        frequency: DigestFrequency,
        hours: int,
    ) -> int:
        """Generate digests for users with the specified frequency."""
        if not self.is_configured:
            logger.warning("Digest service not configured (SMTP settings missing)")
            return 0

        # Get users with this digest frequency
        result = await session.execute(
            select(NotificationPreferencesRecord)
            .where(NotificationPreferencesRecord.digest_frequency == frequency.value)
        )
        prefs_records = result.scalars().all()

        if not prefs_records:
            return 0

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(hours=hours)

        sent_count = 0

        for prefs_record in prefs_records:
            try:
                # Get user info
                user_result = await session.execute(
                    select(UserRecord).where(UserRecord.id == prefs_record.user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user or not user.is_active:
                    continue

                # Get events for this user's digest
                digest_content = await self._build_digest_content(
                    session,
                    user,
                    prefs_record,
                    period_start,
                    period_end,
                    frequency,
                )

                if digest_content.events:
                    await self._send_digest(digest_content)
                    sent_count += 1

            except Exception as e:
                logger.error(f"Failed to generate digest for user {prefs_record.user_id}: {e}")

        logger.info(f"Sent {sent_count} {frequency.value} digests")
        return sent_count

    async def _build_digest_content(
        self,
        session: AsyncSession,
        user: UserRecord,
        prefs: NotificationPreferencesRecord,
        period_start: datetime,
        period_end: datetime,
        frequency: DigestFrequency,
    ) -> DigestContent:
        """Build digest content for a user."""
        # Get sent notifications for this period
        result = await session.execute(
            select(SentNotificationRecord)
            .where(and_(
                SentNotificationRecord.user_id == user.id,
                SentNotificationRecord.created_at >= period_start,
                SentNotificationRecord.created_at <= period_end,
                SentNotificationRecord.status == "sent",
            ))
        )
        notifications = result.scalars().all()

        # Get unique events
        event_ids = list(set(n.event_id for n in notifications))
        
        events = []
        for event_id in event_ids:
            event_result = await session.execute(
                select(EventRecord).where(EventRecord.id == event_id)
            )
            event = event_result.scalar_one_or_none()
            
            if event:
                # Get the rule that triggered this
                notification = next(n for n in notifications if n.event_id == event_id)
                rule_name = "Unknown"
                priority = "medium"
                
                if notification.rule_id:
                    rule_result = await session.execute(
                        select(AlertRuleRecord).where(AlertRuleRecord.id == notification.rule_id)
                    )
                    rule = rule_result.scalar_one_or_none()
                    if rule:
                        rule_name = rule.name
                        priority = rule.priority

                events.append(DigestEvent(
                    id=event.id,
                    title=event.title or "Untitled",
                    summary=event.summary,
                    region=event.region,
                    category=event.category,
                    threat_level=event.threat_level,
                    credibility_score=event.credibility_score,
                    link=event.link,
                    published_at=event.published_at,
                    rule_name=rule_name,
                    priority=priority,
                ))

        # Sort by priority and time
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        events.sort(key=lambda e: (priority_order.get(e.priority, 2), e.published_at or datetime.min), reverse=True)

        return DigestContent(
            user_id=user.id,
            user_email=user.email,
            user_name=user.name,
            frequency=frequency,
            events=events,
            period_start=period_start,
            period_end=period_end,
        )

    async def _send_digest(self, content: DigestContent) -> bool:
        """Send a digest email."""
        try:
            msg = self._build_digest_email(content)
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Sent {content.frequency.value} digest to {content.user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send digest to {content.user_email}: {e}")
            return False

    def _build_digest_email(self, content: DigestContent) -> MIMEMultipart:
        """Build the digest email message."""
        frequency_label = {
            DigestFrequency.HOURLY: "Hourly",
            DigestFrequency.DAILY: "Daily",
            DigestFrequency.WEEKLY: "Weekly",
        }.get(content.frequency, "")

        subject = f"📋 {frequency_label} Alert Digest - {len(content.events)} events"

        # Group events by priority
        critical = [e for e in content.events if e.priority == "critical"]
        high = [e for e in content.events if e.priority == "high"]
        medium = [e for e in content.events if e.priority == "medium"]
        low = [e for e in content.events if e.priority == "low"]

        # Build HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: #f8fafc; }}
                .header {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 20px; border: 1px solid #e2e8f0; }}
                .section {{ margin-bottom: 25px; }}
                .section-title {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; padding: 8px 12px; border-radius: 4px; }}
                .critical {{ background: #fef2f2; color: #dc2626; }}
                .high {{ background: #fffbeb; color: #d97706; }}
                .medium {{ background: #eff6ff; color: #2563eb; }}
                .low {{ background: #f0fdf4; color: #16a34a; }}
                .event {{ padding: 15px; margin-bottom: 10px; border-left: 4px solid #e2e8f0; background: #f8fafc; }}
                .event-title {{ font-weight: bold; margin-bottom: 5px; }}
                .event-meta {{ font-size: 12px; color: #64748b; }}
                .footer {{ background: #f1f5f9; padding: 15px; border-radius: 0 0 8px 8px; font-size: 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin: 0;">📋 {frequency_label} Alert Digest</h1>
                <p style="margin: 10px 0 0; opacity: 0.9;">
                    {content.period_start.strftime('%b %d, %H:%M')} - {content.period_end.strftime('%b %d, %H:%M')} UTC
                </p>
                <p style="margin: 5px 0 0; opacity: 0.8;">
                    {len(content.events)} events triggered alerts
                </p>
            </div>
            
            <div class="content">
        """

        def render_events(events: list[DigestEvent], priority_class: str, emoji: str) -> str:
            if not events:
                return ""
            
            html = f'<div class="section"><div class="section-title {priority_class}">{emoji} {priority_class.upper()} ({len(events)})</div>'
            
            for event in events[:10]:  # Limit to 10 per section
                html += f"""
                <div class="event" style="border-left-color: {'#dc2626' if priority_class == 'critical' else '#d97706' if priority_class == 'high' else '#2563eb' if priority_class == 'medium' else '#16a34a'};">
                    <div class="event-title">{event.title}</div>
                    <div class="event-meta">
                        📍 {event.region or 'Unknown'} | 
                        📁 {event.category or 'Unknown'} | 
                        ⚠️ {event.threat_level or 'Unknown'} |
                        📊 {event.credibility_score:.0%} credibility
                    </div>
                    {f'<p style="margin: 10px 0 5px; font-size: 14px;">{event.summary[:200]}...</p>' if event.summary and len(event.summary) > 200 else f'<p style="margin: 10px 0 5px; font-size: 14px;">{event.summary}</p>' if event.summary else ''}
                    {f'<a href="{event.link}" style="color: #3b82f6; font-size: 13px;">Read more →</a>' if event.link else ''}
                </div>
                """
            
            if len(events) > 10:
                html += f'<p style="color: #64748b; font-size: 13px;">...and {len(events) - 10} more {priority_class} events</p>'
            
            html += '</div>'
            return html

        html += render_events(critical, "critical", "🚨")
        html += render_events(high, "high", "⚠️")
        html += render_events(medium, "medium", "📢")
        html += render_events(low, "low", "ℹ️")

        html += f"""
            </div>
            
            <div class="footer">
                <p style="margin: 0;">You're receiving this because you subscribed to {frequency_label.lower()} digests.</p>
                <p style="margin: 5px 0 0;">To change your notification preferences, visit your account settings.</p>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text = f"""
{frequency_label} Alert Digest
{content.period_start.strftime('%b %d, %H:%M')} - {content.period_end.strftime('%b %d, %H:%M')} UTC
{len(content.events)} events triggered alerts

"""
        for event in content.events[:20]:
            text += f"""
[{event.priority.upper()}] {event.title}
Region: {event.region or 'Unknown'} | Category: {event.category or 'Unknown'}
{event.link or ''}
---
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = content.user_email

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        return msg


# Global instance
digest_service = DigestService()
