"""Alert evaluation engine - processes events and triggers notifications."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EventRecord, AlertRuleRecord
from .rules import AlertRule, AlertCandidate, RuleEvaluator, AlertPriority
from .notification_preferences import (
    NotificationPreferences,
    NotificationPreferencesRecord,
    AlertSubscriptionRecord,
    SentNotificationRecord,
    AlertAcknowledgmentRecord,
    DigestFrequency,
)
from .notification_dispatcher import notification_dispatcher, NotificationResult

logger = logging.getLogger(__name__)


@dataclass
class AlertEngineConfig:
    """Configuration for the alert engine."""
    
    # How often to check for new events (seconds)
    poll_interval: int = 60
    
    # Maximum events to process per batch
    batch_size: int = 100
    
    # Deduplication window (don't re-alert for same event within this period)
    dedup_window_hours: int = 24
    
    # Enable digest mode (batch notifications)
    enable_digest: bool = True
    
    # Escalation settings
    escalation_enabled: bool = True
    escalation_timeout_minutes: int = 30  # Time before escalating unacknowledged critical alerts


@dataclass
class ProcessingStats:
    """Statistics from alert processing run."""
    
    events_processed: int = 0
    alerts_triggered: int = 0
    notifications_sent: int = 0
    notifications_failed: int = 0
    duplicates_skipped: int = 0
    processing_time_ms: float = 0


class AlertEngine:
    """
    Core alert engine that evaluates events against rules and dispatches notifications.
    
    This is the main orchestrator that:
    1. Fetches new/updated events from the database
    2. Loads active alert rules
    3. Evaluates events against rules
    4. Checks user subscriptions and preferences
    5. Dispatches notifications via appropriate channels
    6. Tracks sent notifications for deduplication
    7. Handles escalation for unacknowledged critical alerts
    """

    def __init__(self, config: Optional[AlertEngineConfig] = None):
        self.config = config or AlertEngineConfig()
        self._running = False
        self._last_check: Optional[datetime] = None

    async def process_new_events(self, session: AsyncSession) -> ProcessingStats:
        """
        Process new events and trigger alerts.
        
        This is the main entry point called periodically.
        """
        start_time = datetime.utcnow()
        stats = ProcessingStats()

        try:
            # 1. Load active alert rules
            rules = await self._load_rules(session)
            if not rules:
                logger.debug("No active alert rules configured")
                return stats

            # 2. Fetch recent events
            events = await self._fetch_recent_events(session)
            stats.events_processed = len(events)
            
            if not events:
                logger.debug("No new events to process")
                return stats

            # 3. Evaluate events against rules
            evaluator = RuleEvaluator(rules)
            candidates = evaluator.evaluate(events)
            
            if not candidates:
                logger.debug("No alerts triggered")
                return stats

            # 4. Process each alert candidate
            for candidate in candidates:
                result = await self._process_candidate(session, candidate, stats)
                if result:
                    stats.alerts_triggered += 1

            # Update last check time
            self._last_check = datetime.utcnow()

        except Exception as e:
            logger.error(f"Alert processing failed: {e}", exc_info=True)

        stats.processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Alert processing complete: {stats.events_processed} events, "
            f"{stats.alerts_triggered} alerts, {stats.notifications_sent} notifications sent"
        )

        return stats

    async def _load_rules(self, session: AsyncSession) -> list[AlertRule]:
        """Load active alert rules from database."""
        result = await session.execute(select(AlertRuleRecord))
        records = result.scalars().all()

        rules = []
        for record in records:
            rules.append(AlertRule(
                name=record.name,
                description=record.description or "",
                regions=set(record.regions) if record.regions else None,
                categories=set(record.categories) if record.categories else None,
                minimum_threat=record.minimum_threat,
                minimum_credibility=record.minimum_credibility,
                lookback_minutes=record.lookback_minutes,
                priority=AlertPriority(record.priority),
                auto_ack=record.auto_ack,
            ))

        return rules

    async def _fetch_recent_events(self, session: AsyncSession) -> list[EventRecord]:
        """Fetch events that need to be checked for alerts."""
        # Get events from the last lookback period (or since last check)
        if self._last_check:
            cutoff = self._last_check
        else:
            cutoff = datetime.utcnow() - timedelta(minutes=60)

        result = await session.execute(
            select(EventRecord)
            .where(EventRecord.fetched_at >= cutoff)
            .order_by(EventRecord.fetched_at.desc())
            .limit(self.config.batch_size)
        )

        return list(result.scalars().all())

    async def _process_candidate(
        self,
        session: AsyncSession,
        candidate: AlertCandidate,
        stats: ProcessingStats,
    ) -> bool:
        """Process a single alert candidate."""
        event = candidate.event
        rule = candidate.rule

        # Get users subscribed to this rule (or all users for global rules)
        user_preferences = await self._get_subscribed_users(session, rule.name)
        
        if not user_preferences:
            logger.debug(f"No subscribers for rule '{rule.name}'")
            return False

        # Filter out users who already received this alert
        filtered_prefs = []
        for email, prefs in user_preferences:
            if await self._should_notify_user(session, prefs.user_id, event.id, rule.name):
                filtered_prefs.append((email, prefs))
            else:
                stats.duplicates_skipped += 1

        if not filtered_prefs:
            return False

        # Dispatch notifications
        results = await notification_dispatcher.dispatch_to_multiple_users(
            candidate,
            filtered_prefs,
        )

        # Record sent notifications
        for user_id, notification_results in results.items():
            for result in notification_results:
                await self._record_notification(session, user_id, event.id, rule.name, result)
                
                if result.success:
                    stats.notifications_sent += 1
                else:
                    stats.notifications_failed += 1

        await session.commit()
        return True

    async def _get_subscribed_users(
        self,
        session: AsyncSession,
        rule_name: str,
    ) -> list[tuple[str, NotificationPreferences]]:
        """Get users subscribed to a rule with their preferences."""
        # For now, get all users with notification preferences
        # In production, would filter by rule subscriptions
        
        result = await session.execute(select(NotificationPreferencesRecord))
        records = result.scalars().all()

        user_prefs = []
        for record in records:
            # Get user email from users table
            from backend.database.models import UserRecord
            user_result = await session.execute(
                select(UserRecord).where(UserRecord.id == record.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user and user.is_active:
                prefs = NotificationPreferences.from_record(record)
                user_prefs.append((user.email, prefs))

        return user_prefs

    async def _should_notify_user(
        self,
        session: AsyncSession,
        user_id: str,
        event_id: str,
        rule_name: str,
    ) -> bool:
        """Check if user should be notified (deduplication)."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.dedup_window_hours)
        
        result = await session.execute(
            select(SentNotificationRecord)
            .where(and_(
                SentNotificationRecord.user_id == user_id,
                SentNotificationRecord.event_id == event_id,
                SentNotificationRecord.created_at >= cutoff,
                SentNotificationRecord.status == "sent",
            ))
            .limit(1)
        )

        existing = result.scalar_one_or_none()
        return existing is None

    async def _record_notification(
        self,
        session: AsyncSession,
        user_id: str,
        event_id: str,
        rule_name: str,
        result: NotificationResult,
    ) -> None:
        """Record a sent notification."""
        # Get rule ID
        rule_result = await session.execute(
            select(AlertRuleRecord.id).where(AlertRuleRecord.name == rule_name).limit(1)
        )
        rule_id = rule_result.scalar_one_or_none()

        record = SentNotificationRecord(
            user_id=user_id,
            event_id=event_id,
            rule_id=rule_id,
            channel=result.channel.value,
            status="sent" if result.success else "failed",
            recipient=result.recipient,
            message_id=result.message_id,
            error_message=result.error,
            sent_at=result.timestamp if result.success else None,
        )

        session.add(record)

    async def check_escalations(self, session: AsyncSession) -> int:
        """
        Check for unacknowledged critical alerts and escalate.
        
        Returns number of escalated alerts.
        """
        if not self.config.escalation_enabled:
            return 0

        escalation_cutoff = datetime.utcnow() - timedelta(
            minutes=self.config.escalation_timeout_minutes
        )

        # Find unacknowledged critical notifications
        result = await session.execute(
            select(SentNotificationRecord)
            .where(and_(
                SentNotificationRecord.status == "sent",
                SentNotificationRecord.created_at <= escalation_cutoff,
                SentNotificationRecord.acknowledged_at.is_(None),
            ))
        )

        unacked = result.scalars().all()
        escalated = 0

        for notification in unacked:
            # Check if this was a critical alert
            if notification.rule_id:
                rule_result = await session.execute(
                    select(AlertRuleRecord)
                    .where(AlertRuleRecord.id == notification.rule_id)
                )
                rule = rule_result.scalar_one_or_none()
                
                if rule and rule.priority == "critical":
                    # Escalate - could send to additional channels or supervisors
                    logger.warning(
                        f"Escalating unacknowledged critical alert: "
                        f"event={notification.event_id}, user={notification.user_id}"
                    )
                    escalated += 1

        return escalated

    async def acknowledge_alert(
        self,
        session: AsyncSession,
        user_id: str,
        event_id: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Acknowledge an alert for a user."""
        # Create acknowledgment record
        ack = AlertAcknowledgmentRecord(
            user_id=user_id,
            event_id=event_id,
            notes=notes,
        )
        session.add(ack)

        # Update sent notifications
        result = await session.execute(
            select(SentNotificationRecord)
            .where(and_(
                SentNotificationRecord.user_id == user_id,
                SentNotificationRecord.event_id == event_id,
                SentNotificationRecord.acknowledged_at.is_(None),
            ))
        )

        notifications = result.scalars().all()
        for notification in notifications:
            notification.acknowledged_at = datetime.utcnow()
            notification.status = "acknowledged"

        await session.commit()
        return True

    async def run_continuous(self, session_factory) -> None:
        """Run the alert engine continuously."""
        self._running = True
        logger.info(f"Alert engine started, polling every {self.config.poll_interval}s")

        while self._running:
            try:
                async with session_factory() as session:
                    await self.process_new_events(session)
                    await self.check_escalations(session)
            except Exception as e:
                logger.error(f"Alert engine error: {e}", exc_info=True)

            await asyncio.sleep(self.config.poll_interval)

    def stop(self) -> None:
        """Stop the continuous alert engine."""
        self._running = False
        logger.info("Alert engine stopping")


# Global engine instance
alert_engine = AlertEngine()
