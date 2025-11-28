"""User notification preferences and channel management."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, JSONType


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class DigestFrequency(str, Enum):
    """Digest email frequency options."""
    REALTIME = "realtime"  # Immediate notifications
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NONE = "none"  # Disabled


class NotificationPreferencesRecord(Base):
    """User notification preferences stored in database."""

    __tablename__ = "notification_preferences"
    __table_args__ = {"comment": "User notification channel preferences"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # Channel enablement
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Contact info
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Digest settings
    digest_frequency: Mapped[str] = mapped_column(String(16), default="daily")
    digest_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)  # Preferred time for daily digest
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    
    # Filtering
    min_priority: Mapped[str] = mapped_column(String(16), default="medium")  # low, medium, high, critical
    watched_regions: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)
    watched_categories: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)
    muted_sources: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)
    
    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    quiet_hours_override_critical: Mapped[bool] = mapped_column(Boolean, default=True)  # Critical alerts bypass quiet hours
    
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


class AlertSubscriptionRecord(Base):
    """User subscription to specific alert rules."""

    __tablename__ = "alert_subscriptions"
    __table_args__ = {"comment": "User subscriptions to alert rules"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    rule_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # Override settings for this specific rule
    channels: Mapped[Optional[list[str]]] = mapped_column(JSONType, nullable=True)  # Override channels
    priority_override: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


class SentNotificationRecord(Base):
    """Record of sent notifications for deduplication and tracking."""

    __tablename__ = "sent_notifications"
    __table_args__ = {"comment": "History of sent notifications"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    event_id: Mapped[str] = mapped_column(String(36), index=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    channel: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending, sent, failed, acknowledged
    
    # Delivery details
    recipient: Mapped[str] = mapped_column(String(256))  # email, phone, webhook URL
    message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # External message ID
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AlertAcknowledgmentRecord(Base):
    """User acknowledgment of alerts."""

    __tablename__ = "alert_acknowledgments"
    __table_args__ = {"comment": "User acknowledgments of alerts"}

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    event_id: Mapped[str] = mapped_column(String(36), index=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


@dataclass
class NotificationPreferences:
    """Runtime notification preferences object."""
    
    user_id: str
    email_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    push_enabled: bool = True
    webhook_enabled: bool = False
    
    phone_number: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    digest_frequency: DigestFrequency = DigestFrequency.DAILY
    digest_time: Optional[time] = None
    timezone: str = "UTC"
    
    min_priority: str = "medium"
    watched_regions: set[str] = field(default_factory=set)
    watched_categories: set[str] = field(default_factory=set)
    muted_sources: set[str] = field(default_factory=set)
    
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    quiet_hours_override_critical: bool = True

    @classmethod
    def from_record(cls, record: NotificationPreferencesRecord) -> "NotificationPreferences":
        """Create from database record."""
        return cls(
            user_id=record.user_id,
            email_enabled=record.email_enabled,
            sms_enabled=record.sms_enabled,
            whatsapp_enabled=record.whatsapp_enabled,
            push_enabled=record.push_enabled,
            webhook_enabled=record.webhook_enabled,
            phone_number=record.phone_number,
            webhook_url=record.webhook_url,
            webhook_secret=record.webhook_secret,
            digest_frequency=DigestFrequency(record.digest_frequency),
            digest_time=record.digest_time,
            timezone=record.timezone,
            min_priority=record.min_priority,
            watched_regions=set(record.watched_regions or []),
            watched_categories=set(record.watched_categories or []),
            muted_sources=set(record.muted_sources or []),
            quiet_hours_enabled=record.quiet_hours_enabled,
            quiet_hours_start=record.quiet_hours_start,
            quiet_hours_end=record.quiet_hours_end,
            quiet_hours_override_critical=record.quiet_hours_override_critical,
        )

    def get_enabled_channels(self) -> list[NotificationChannel]:
        """Get list of enabled notification channels."""
        channels = []
        if self.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if self.sms_enabled and self.phone_number:
            channels.append(NotificationChannel.SMS)
        if self.whatsapp_enabled and self.phone_number:
            channels.append(NotificationChannel.WHATSAPP)
        if self.push_enabled:
            channels.append(NotificationChannel.PUSH)
        if self.webhook_enabled and self.webhook_url:
            channels.append(NotificationChannel.WEBHOOK)
        return channels

    def should_notify(self, priority: str, region: Optional[str] = None, category: Optional[str] = None) -> bool:
        """Check if notification should be sent based on preferences."""
        priority_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        
        # Check priority threshold
        if priority_order.get(priority.lower(), 0) < priority_order.get(self.min_priority.lower(), 1):
            return False
        
        # Check region filter (if set)
        if self.watched_regions and region:
            if region.lower() not in {r.lower() for r in self.watched_regions}:
                return False
        
        # Check category filter (if set)
        if self.watched_categories and category:
            if category.lower() not in {c.lower() for c in self.watched_categories}:
                return False
        
        return True

    def is_quiet_hours(self, current_time: time, priority: str = "medium") -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled:
            return False
        
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        # Critical alerts can bypass quiet hours
        if priority.lower() == "critical" and self.quiet_hours_override_critical:
            return False
        
        # Handle overnight quiet hours (e.g., 22:00 - 07:00)
        if self.quiet_hours_start > self.quiet_hours_end:
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
