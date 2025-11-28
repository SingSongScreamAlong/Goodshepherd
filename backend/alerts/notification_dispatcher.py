"""Multi-channel notification dispatcher."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Protocol

import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .rules import AlertCandidate, AlertPriority
from .notification_preferences import NotificationChannel, NotificationPreferences
from .sms_delivery import TwilioClient, TwilioConfig, format_alert_message

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification delivery attempt."""
    success: bool
    channel: NotificationChannel
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class NotificationSender(Protocol):
    """Protocol for notification channel senders."""
    
    async def send(
        self,
        candidate: AlertCandidate,
        recipient: str,
        preferences: NotificationPreferences,
    ) -> NotificationResult:
        ...


class EmailSender:
    """Send notifications via email using SMTP."""

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "alerts@goodshepherd.org")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Good Shepherd Alerts")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    async def send(
        self,
        candidate: AlertCandidate,
        recipient: str,
        preferences: NotificationPreferences,
    ) -> NotificationResult:
        if not self.is_configured:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.EMAIL,
                recipient=recipient,
                error="Email not configured",
            )

        try:
            msg = self._build_email(candidate, recipient)
            
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=self.use_tls,
            )

            return NotificationResult(
                success=True,
                channel=NotificationChannel.EMAIL,
                recipient=recipient,
                message_id=msg["Message-ID"],
            )

        except Exception as e:
            logger.error(f"Email delivery failed to {recipient}: {e}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.EMAIL,
                recipient=recipient,
                error=str(e),
            )

    def _build_email(self, candidate: AlertCandidate, recipient: str) -> MIMEMultipart:
        """Build email message."""
        event = candidate.event
        rule = candidate.rule

        priority_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "📢",
            "low": "ℹ️",
        }.get(rule.priority.value.lower(), "📢")

        subject = f"{priority_emoji} Alert: {rule.name} - {event.title[:50]}"

        # HTML body
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {'#dc2626' if rule.priority == AlertPriority.CRITICAL else '#f59e0b' if rule.priority == AlertPriority.HIGH else '#3b82f6'}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">{priority_emoji} {rule.name}</h2>
                <p style="margin: 5px 0 0; opacity: 0.9;">Priority: {rule.priority.value.upper()}</p>
            </div>
            
            <div style="background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0;">
                <h3 style="margin-top: 0;">{event.title}</h3>
                
                <p><strong>Region:</strong> {event.region or 'Unknown'}</p>
                <p><strong>Category:</strong> {event.category or 'Unknown'}</p>
                <p><strong>Threat Level:</strong> {event.threat_level or 'Unknown'}</p>
                <p><strong>Credibility:</strong> {event.credibility_score:.0%}</p>
                
                {f'<p>{event.summary[:500]}...</p>' if event.summary and len(event.summary) > 500 else f'<p>{event.summary}</p>' if event.summary else ''}
                
                {f'<p><a href="{event.link}" style="color: #3b82f6;">Read more →</a></p>' if event.link else ''}
            </div>
            
            <div style="background: #f1f5f9; padding: 15px; border-radius: 0 0 8px 8px; font-size: 12px; color: #64748b;">
                <p style="margin: 0;">This alert was triggered by rule: {rule.name}</p>
                <p style="margin: 5px 0 0;">Event ID: {event.id}</p>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        text = f"""
{priority_emoji} ALERT: {rule.name}
Priority: {rule.priority.value.upper()}

{event.title}

Region: {event.region or 'Unknown'}
Category: {event.category or 'Unknown'}
Threat Level: {event.threat_level or 'Unknown'}
Credibility: {event.credibility_score:.0%}

{event.summary or ''}

{f'Link: {event.link}' if event.link else ''}

---
Rule: {rule.name}
Event ID: {event.id}
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = recipient
        msg["X-Priority"] = "1" if rule.priority == AlertPriority.CRITICAL else "3"

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        return msg


class SMSSender:
    """Send notifications via SMS using Twilio."""

    def __init__(self):
        self.config = TwilioConfig.from_env()
        self._client: TwilioClient | None = None

    async def _get_client(self) -> TwilioClient:
        if self._client is None:
            self._client = TwilioClient(self.config)
        return self._client

    async def send(
        self,
        candidate: AlertCandidate,
        recipient: str,
        preferences: NotificationPreferences,
    ) -> NotificationResult:
        if not self.config.is_configured:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.SMS,
                recipient=recipient,
                error="SMS not configured",
            )

        client = await self._get_client()
        message = format_alert_message(candidate, max_length=160)
        
        result = await client.send_sms(recipient, message)

        return NotificationResult(
            success=result.success,
            channel=NotificationChannel.SMS,
            recipient=recipient,
            message_id=result.message_sid,
            error=result.error,
        )


class WhatsAppSender:
    """Send notifications via WhatsApp using Twilio."""

    def __init__(self):
        self.config = TwilioConfig.from_env()
        self._client: TwilioClient | None = None

    async def _get_client(self) -> TwilioClient:
        if self._client is None:
            self._client = TwilioClient(self.config)
        return self._client

    async def send(
        self,
        candidate: AlertCandidate,
        recipient: str,
        preferences: NotificationPreferences,
    ) -> NotificationResult:
        if not self.config.is_configured:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.WHATSAPP,
                recipient=recipient,
                error="WhatsApp not configured",
            )

        client = await self._get_client()
        message = format_alert_message(candidate, max_length=1600)
        
        result = await client.send_whatsapp(recipient, message)

        return NotificationResult(
            success=result.success,
            channel=NotificationChannel.WHATSAPP,
            recipient=recipient,
            message_id=result.message_sid,
            error=result.error,
        )


class WebhookSender:
    """Send notifications via webhook."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def send(
        self,
        candidate: AlertCandidate,
        recipient: str,  # webhook URL
        preferences: NotificationPreferences,
    ) -> NotificationResult:
        client = await self._get_client()
        event = candidate.event
        rule = candidate.rule

        payload = {
            "type": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "rule": {
                "name": rule.name,
                "priority": rule.priority.value,
            },
            "event": {
                "id": event.id,
                "title": event.title,
                "summary": event.summary,
                "category": event.category,
                "region": event.region,
                "threat_level": event.threat_level,
                "credibility_score": event.credibility_score,
                "link": event.link,
                "published_at": event.published_at.isoformat() if event.published_at else None,
            },
        }

        headers = {"Content-Type": "application/json"}

        # Add HMAC signature if secret is configured
        if preferences.webhook_secret:
            payload_bytes = json.dumps(payload, sort_keys=True).encode()
            signature = hmac.new(
                preferences.webhook_secret.encode(),
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            response = await client.post(recipient, json=payload, headers=headers)
            
            if response.status_code < 300:
                return NotificationResult(
                    success=True,
                    channel=NotificationChannel.WEBHOOK,
                    recipient=recipient,
                )
            else:
                return NotificationResult(
                    success=False,
                    channel=NotificationChannel.WEBHOOK,
                    recipient=recipient,
                    error=f"HTTP {response.status_code}",
                )

        except Exception as e:
            logger.error(f"Webhook delivery failed to {recipient}: {e}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.WEBHOOK,
                recipient=recipient,
                error=str(e),
            )


class PushSender:
    """Send web push notifications."""

    def __init__(self):
        # Web Push configuration (VAPID)
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "")
        self.vapid_email = os.getenv("VAPID_EMAIL", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.vapid_private_key and self.vapid_public_key)

    async def send(
        self,
        candidate: AlertCandidate,
        recipient: str,  # Push subscription JSON
        preferences: NotificationPreferences,
    ) -> NotificationResult:
        if not self.is_configured:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                recipient=recipient[:50],
                error="Push notifications not configured",
            )

        # TODO: Implement actual web push using pywebpush
        # For now, log the notification
        logger.info(f"Push notification would be sent: {candidate.rule.name}")
        
        return NotificationResult(
            success=True,
            channel=NotificationChannel.PUSH,
            recipient=recipient[:50],
        )


class NotificationDispatcher:
    """Dispatches notifications across multiple channels."""

    def __init__(self):
        self.email_sender = EmailSender()
        self.sms_sender = SMSSender()
        self.whatsapp_sender = WhatsAppSender()
        self.webhook_sender = WebhookSender()
        self.push_sender = PushSender()

    async def dispatch(
        self,
        candidate: AlertCandidate,
        user_email: str,
        preferences: NotificationPreferences,
        channels: Optional[list[NotificationChannel]] = None,
    ) -> list[NotificationResult]:
        """
        Dispatch notification to user across enabled channels.
        
        Args:
            candidate: The alert candidate to notify about
            user_email: User's email address
            preferences: User's notification preferences
            channels: Override channels (uses preferences if None)
        
        Returns:
            List of notification results for each channel
        """
        results = []
        
        # Determine which channels to use
        if channels is None:
            channels = preferences.get_enabled_channels()
        
        # Check if we should notify based on preferences
        if not preferences.should_notify(
            priority=candidate.rule.priority.value,
            region=candidate.event.region,
            category=candidate.event.category,
        ):
            logger.debug(f"Skipping notification for user {preferences.user_id} - filtered by preferences")
            return results

        # Check quiet hours
        current_time = datetime.utcnow().time()
        if preferences.is_quiet_hours(current_time, candidate.rule.priority.value):
            logger.debug(f"Skipping notification for user {preferences.user_id} - quiet hours")
            return results

        # Dispatch to each channel
        tasks = []
        
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                tasks.append(self.email_sender.send(candidate, user_email, preferences))
            
            elif channel == NotificationChannel.SMS and preferences.phone_number:
                tasks.append(self.sms_sender.send(candidate, preferences.phone_number, preferences))
            
            elif channel == NotificationChannel.WHATSAPP and preferences.phone_number:
                tasks.append(self.whatsapp_sender.send(candidate, preferences.phone_number, preferences))
            
            elif channel == NotificationChannel.WEBHOOK and preferences.webhook_url:
                tasks.append(self.webhook_sender.send(candidate, preferences.webhook_url, preferences))
            
            elif channel == NotificationChannel.PUSH:
                # Push requires subscription info - would need to fetch from DB
                pass

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to failed results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(NotificationResult(
                        success=False,
                        channel=channels[i] if i < len(channels) else NotificationChannel.EMAIL,
                        recipient="unknown",
                        error=str(result),
                    ))
                else:
                    processed_results.append(result)
            
            results = processed_results

        return results

    async def dispatch_to_multiple_users(
        self,
        candidate: AlertCandidate,
        user_preferences: list[tuple[str, NotificationPreferences]],  # (email, prefs)
    ) -> dict[str, list[NotificationResult]]:
        """
        Dispatch notification to multiple users.
        
        Returns dict mapping user_id to their notification results.
        """
        all_results = {}
        
        tasks = [
            self.dispatch(candidate, email, prefs)
            for email, prefs in user_preferences
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (email, prefs), result in zip(user_preferences, results):
            if isinstance(result, Exception):
                all_results[prefs.user_id] = [NotificationResult(
                    success=False,
                    channel=NotificationChannel.EMAIL,
                    recipient=email,
                    error=str(result),
                )]
            else:
                all_results[prefs.user_id] = result
        
        return all_results


# Global dispatcher instance
notification_dispatcher = NotificationDispatcher()
