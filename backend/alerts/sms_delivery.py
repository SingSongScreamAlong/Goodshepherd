"""SMS and WhatsApp alert delivery via Twilio."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import httpx

from .rules import AlertCandidate, AlertSink

logger = logging.getLogger(__name__)


class DeliveryChannel(str, Enum):
    """Supported delivery channels."""
    SMS = "sms"
    WHATSAPP = "whatsapp"


@dataclass
class TwilioConfig:
    """Twilio configuration settings."""

    account_sid: str
    auth_token: str
    from_number: str  # For SMS
    whatsapp_number: str  # For WhatsApp (format: whatsapp:+1234567890)

    @classmethod
    def from_env(cls) -> "TwilioConfig":
        """Load configuration from environment variables."""
        return cls(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            from_number=os.getenv("TWILIO_FROM_NUMBER", ""),
            whatsapp_number=os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
        )

    @property
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return bool(self.account_sid and self.auth_token and self.from_number)


@dataclass
class SMSRecipient:
    """Represents an SMS/WhatsApp recipient."""

    phone_number: str
    name: str = ""
    preferred_channel: DeliveryChannel = DeliveryChannel.SMS
    regions: set[str] = field(default_factory=set)  # Filter by region
    min_threat_level: str = "high"  # Minimum threat level to notify
    enabled: bool = True


@dataclass
class DeliveryResult:
    """Result of a delivery attempt."""

    success: bool
    recipient: str
    channel: DeliveryChannel
    message_sid: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TwilioClient:
    """Async Twilio API client."""

    BASE_URL = "https://api.twilio.com/2010-04-01"

    def __init__(self, config: TwilioConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                auth=(self.config.account_sid, self.config.auth_token),
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send_sms(
        self,
        to: str,
        body: str,
        from_number: Optional[str] = None,
    ) -> DeliveryResult:
        """Send an SMS message."""
        if not self.config.is_configured:
            return DeliveryResult(
                success=False,
                recipient=to,
                channel=DeliveryChannel.SMS,
                error="Twilio not configured",
            )

        client = await self._get_client()
        url = f"{self.BASE_URL}/Accounts/{self.config.account_sid}/Messages.json"

        try:
            response = await client.post(
                url,
                data={
                    "To": to,
                    "From": from_number or self.config.from_number,
                    "Body": body,
                },
            )

            if response.status_code == 201:
                data = response.json()
                return DeliveryResult(
                    success=True,
                    recipient=to,
                    channel=DeliveryChannel.SMS,
                    message_sid=data.get("sid"),
                )
            else:
                error_data = response.json()
                return DeliveryResult(
                    success=False,
                    recipient=to,
                    channel=DeliveryChannel.SMS,
                    error=error_data.get("message", f"HTTP {response.status_code}"),
                )

        except Exception as e:
            logger.error(f"SMS delivery failed to {to}: {e}")
            return DeliveryResult(
                success=False,
                recipient=to,
                channel=DeliveryChannel.SMS,
                error=str(e),
            )

    async def send_whatsapp(
        self,
        to: str,
        body: str,
    ) -> DeliveryResult:
        """Send a WhatsApp message."""
        if not self.config.is_configured or not self.config.whatsapp_number:
            return DeliveryResult(
                success=False,
                recipient=to,
                channel=DeliveryChannel.WHATSAPP,
                error="WhatsApp not configured",
            )

        # Format numbers for WhatsApp
        whatsapp_to = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        whatsapp_from = self.config.whatsapp_number
        if not whatsapp_from.startswith("whatsapp:"):
            whatsapp_from = f"whatsapp:{whatsapp_from}"

        client = await self._get_client()
        url = f"{self.BASE_URL}/Accounts/{self.config.account_sid}/Messages.json"

        try:
            response = await client.post(
                url,
                data={
                    "To": whatsapp_to,
                    "From": whatsapp_from,
                    "Body": body,
                },
            )

            if response.status_code == 201:
                data = response.json()
                return DeliveryResult(
                    success=True,
                    recipient=to,
                    channel=DeliveryChannel.WHATSAPP,
                    message_sid=data.get("sid"),
                )
            else:
                error_data = response.json()
                return DeliveryResult(
                    success=False,
                    recipient=to,
                    channel=DeliveryChannel.WHATSAPP,
                    error=error_data.get("message", f"HTTP {response.status_code}"),
                )

        except Exception as e:
            logger.error(f"WhatsApp delivery failed to {to}: {e}")
            return DeliveryResult(
                success=False,
                recipient=to,
                channel=DeliveryChannel.WHATSAPP,
                error=str(e),
            )


def format_alert_message(candidate: AlertCandidate, max_length: int = 160) -> str:
    """Format an alert for SMS/WhatsApp delivery."""
    event = candidate.event
    rule = candidate.rule

    # Priority indicator
    priority_emoji = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "📢",
        "low": "ℹ️",
    }.get(rule.priority.value.lower(), "📢")

    # Build message
    parts = [
        f"{priority_emoji} ALERT: {rule.name}",
        f"📍 {event.region}" if event.region else "",
        f"📰 {event.title[:80]}..." if len(event.title or "") > 80 else event.title,
    ]

    message = "\n".join(p for p in parts if p)

    # Add link if space permits
    if event.link and len(message) + len(event.link) + 10 < max_length:
        message += f"\n🔗 {event.link}"

    # Truncate if needed
    if len(message) > max_length:
        message = message[:max_length - 3] + "..."

    return message


@dataclass(slots=True)
class TwilioSMSSink(AlertSink):
    """Alert sink that delivers via Twilio SMS."""

    recipients: list[SMSRecipient]
    config: TwilioConfig = field(default_factory=TwilioConfig.from_env)
    _client: TwilioClient | None = field(default=None, init=False)

    async def _get_client(self) -> TwilioClient:
        if self._client is None:
            self._client = TwilioClient(self.config)
        return self._client

    async def send(self, candidate: AlertCandidate) -> None:
        """Send alert to all matching recipients."""
        if not self.config.is_configured:
            logger.warning("Twilio SMS sink not configured, skipping delivery")
            return

        client = await self._get_client()
        message = format_alert_message(candidate)

        # Filter recipients
        matching_recipients = [
            r for r in self.recipients
            if r.enabled and self._should_notify(r, candidate)
        ]

        # Send to all matching recipients
        tasks = []
        for recipient in matching_recipients:
            if recipient.preferred_channel == DeliveryChannel.SMS:
                tasks.append(client.send_sms(recipient.phone_number, message))
            else:
                tasks.append(client.send_whatsapp(recipient.phone_number, message))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(
                1 for r in results
                if isinstance(r, DeliveryResult) and r.success
            )
            logger.info(
                f"SMS/WhatsApp delivery: {success_count}/{len(results)} successful "
                f"for alert '{candidate.rule.name}'"
            )

    def _should_notify(self, recipient: SMSRecipient, candidate: AlertCandidate) -> bool:
        """Check if recipient should receive this alert."""
        event = candidate.event

        # Check region filter
        if recipient.regions:
            event_region = (event.region or "").lower()
            if not any(r.lower() in event_region for r in recipient.regions):
                return False

        # Check threat level
        threat_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        event_threat = threat_order.get((event.threat_level or "").lower(), 0)
        min_threat = threat_order.get(recipient.min_threat_level.lower(), 2)

        if event_threat < min_threat:
            return False

        return True

    async def close(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()


@dataclass(slots=True)
class TwilioWhatsAppSink(AlertSink):
    """Alert sink that delivers via Twilio WhatsApp."""

    recipients: list[SMSRecipient]
    config: TwilioConfig = field(default_factory=TwilioConfig.from_env)
    _client: TwilioClient | None = field(default=None, init=False)

    async def _get_client(self) -> TwilioClient:
        if self._client is None:
            self._client = TwilioClient(self.config)
        return self._client

    async def send(self, candidate: AlertCandidate) -> None:
        """Send WhatsApp alert to all matching recipients."""
        if not self.config.is_configured:
            logger.warning("Twilio WhatsApp sink not configured, skipping delivery")
            return

        client = await self._get_client()
        # WhatsApp allows longer messages
        message = format_alert_message(candidate, max_length=1600)

        matching_recipients = [
            r for r in self.recipients
            if r.enabled and r.preferred_channel == DeliveryChannel.WHATSAPP
        ]

        tasks = [
            client.send_whatsapp(r.phone_number, message)
            for r in matching_recipients
        ]

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(
                1 for r in results
                if isinstance(r, DeliveryResult) and r.success
            )
            logger.info(
                f"WhatsApp delivery: {success_count}/{len(results)} successful"
            )

    async def close(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()


# Singleton client instance
_twilio_client: TwilioClient | None = None


async def get_twilio_client() -> TwilioClient:
    """Get the global Twilio client instance."""
    global _twilio_client
    if _twilio_client is None:
        config = TwilioConfig.from_env()
        _twilio_client = TwilioClient(config)
    return _twilio_client
