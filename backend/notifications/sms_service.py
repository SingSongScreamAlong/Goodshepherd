"""SMS Notification Service.

Provides SMS fallback for alerts when push notifications fail
or when users are in low-connectivity areas.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SMSProvider(str, Enum):
    """Supported SMS providers."""
    TWILIO = "twilio"
    VONAGE = "vonage"
    AWS_SNS = "aws_sns"


@dataclass
class SMSMessage:
    """SMS message structure."""
    to: str
    body: str
    from_number: Optional[str] = None
    priority: str = "normal"  # normal, high, emergency


@dataclass
class SMSResult:
    """Result of SMS send attempt."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    timestamp: Optional[datetime] = None


class TwilioProvider:
    """Twilio SMS provider."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

    @property
    def is_configured(self) -> bool:
        return all([self.account_sid, self.auth_token, self.from_number])

    async def send(self, message: SMSMessage) -> SMSResult:
        """Send SMS via Twilio."""
        if not self.is_configured:
            return SMSResult(success=False, error="Twilio not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "To": message.to,
                        "From": message.from_number or self.from_number,
                        "Body": message.body,
                    },
                )

                if response.status_code == 201:
                    data = response.json()
                    return SMSResult(
                        success=True,
                        message_id=data.get("sid"),
                        provider="twilio",
                        timestamp=datetime.utcnow(),
                    )
                else:
                    return SMSResult(
                        success=False,
                        error=f"Twilio error: {response.status_code} - {response.text}",
                        provider="twilio",
                    )

        except Exception as e:
            logger.error(f"Twilio send failed: {e}")
            return SMSResult(success=False, error=str(e), provider="twilio")


class VonageProvider:
    """Vonage (Nexmo) SMS provider."""

    def __init__(self):
        self.api_key = os.getenv("VONAGE_API_KEY")
        self.api_secret = os.getenv("VONAGE_API_SECRET")
        self.from_number = os.getenv("VONAGE_FROM_NUMBER", "GoodShepherd")
        self.base_url = "https://rest.nexmo.com/sms/json"

    @property
    def is_configured(self) -> bool:
        return all([self.api_key, self.api_secret])

    async def send(self, message: SMSMessage) -> SMSResult:
        """Send SMS via Vonage."""
        if not self.is_configured:
            return SMSResult(success=False, error="Vonage not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    data={
                        "api_key": self.api_key,
                        "api_secret": self.api_secret,
                        "to": message.to,
                        "from": message.from_number or self.from_number,
                        "text": message.body,
                    },
                )

                data = response.json()
                messages = data.get("messages", [])

                if messages and messages[0].get("status") == "0":
                    return SMSResult(
                        success=True,
                        message_id=messages[0].get("message-id"),
                        provider="vonage",
                        timestamp=datetime.utcnow(),
                    )
                else:
                    error = messages[0].get("error-text") if messages else "Unknown error"
                    return SMSResult(
                        success=False,
                        error=f"Vonage error: {error}",
                        provider="vonage",
                    )

        except Exception as e:
            logger.error(f"Vonage send failed: {e}")
            return SMSResult(success=False, error=str(e), provider="vonage")


class SMSService:
    """SMS notification service with provider fallback."""

    def __init__(self, primary_provider: SMSProvider = SMSProvider.TWILIO):
        self.providers = {
            SMSProvider.TWILIO: TwilioProvider(),
            SMSProvider.VONAGE: VonageProvider(),
        }
        self.primary_provider = primary_provider
        self._fallback_order = [SMSProvider.TWILIO, SMSProvider.VONAGE]

    async def send_sms(self, message: SMSMessage) -> SMSResult:
        """Send SMS with automatic provider fallback."""
        # Try primary provider first
        primary = self.providers.get(self.primary_provider)
        if primary and primary.is_configured:
            result = await primary.send(message)
            if result.success:
                return result
            logger.warning(f"Primary SMS provider failed: {result.error}")

        # Try fallback providers
        for provider_type in self._fallback_order:
            if provider_type == self.primary_provider:
                continue

            provider = self.providers.get(provider_type)
            if provider and provider.is_configured:
                result = await provider.send(message)
                if result.success:
                    return result
                logger.warning(f"Fallback SMS provider {provider_type} failed: {result.error}")

        return SMSResult(
            success=False,
            error="All SMS providers failed or not configured",
        )

    async def send_alert(
        self,
        phone_number: str,
        alert_title: str,
        alert_summary: str,
        threat_level: str = "medium",
        region: Optional[str] = None,
    ) -> SMSResult:
        """Send a formatted alert SMS."""
        # Format message for SMS (160 char limit consideration)
        threat_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "minimal": "⚪",
        }.get(threat_level, "⚠️")

        body_parts = [
            f"{threat_emoji} ALERT: {alert_title[:50]}",
        ]

        if region:
            body_parts.append(f"📍 {region[:20]}")

        # Add truncated summary
        remaining_chars = 160 - len("\n".join(body_parts)) - 20
        if remaining_chars > 30:
            summary = alert_summary[:remaining_chars] + "..." if len(alert_summary) > remaining_chars else alert_summary
            body_parts.append(summary)

        body_parts.append("Reply SAFE to check in")

        message = SMSMessage(
            to=phone_number,
            body="\n".join(body_parts),
            priority="high" if threat_level in ["critical", "high"] else "normal",
        )

        return await self.send_sms(message)

    async def send_checkin_reminder(
        self,
        phone_number: str,
        hours_since_checkin: int,
    ) -> SMSResult:
        """Send check-in reminder SMS."""
        message = SMSMessage(
            to=phone_number,
            body=f"🛡️ Good Shepherd: It's been {hours_since_checkin}h since your last check-in. Reply SAFE to confirm you're okay.",
            priority="normal",
        )
        return await self.send_sms(message)

    async def send_emergency_broadcast(
        self,
        phone_numbers: list[str],
        message_body: str,
    ) -> dict:
        """Send emergency broadcast to multiple numbers."""
        results = {
            "total": len(phone_numbers),
            "success": 0,
            "failed": 0,
            "errors": [],
        }

        for phone in phone_numbers:
            message = SMSMessage(
                to=phone,
                body=f"🆘 EMERGENCY: {message_body}",
                priority="emergency",
            )
            result = await self.send_sms(message)

            if result.success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "phone": phone[-4:],  # Last 4 digits only
                    "error": result.error,
                })

        return results

    def get_status(self) -> dict:
        """Get SMS service status."""
        return {
            "primary_provider": self.primary_provider.value,
            "providers": {
                provider.value: {
                    "configured": self.providers[provider].is_configured,
                }
                for provider in self.providers
            },
        }


# Singleton instance
_sms_service: Optional[SMSService] = None


def get_sms_service() -> SMSService:
    """Get or create SMS service singleton."""
    global _sms_service
    if _sms_service is None:
        primary = os.getenv("SMS_PRIMARY_PROVIDER", "twilio")
        _sms_service = SMSService(
            primary_provider=SMSProvider(primary) if primary in [p.value for p in SMSProvider] else SMSProvider.TWILIO
        )
    return _sms_service
