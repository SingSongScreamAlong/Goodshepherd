"""Tests for SMS/WhatsApp delivery via Twilio."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.alerts.sms_delivery import (
    TwilioConfig,
    TwilioClient,
    SMSRecipient,
    DeliveryChannel,
    TwilioSMSSink,
    format_alert_message,
)
from backend.alerts.rules import AlertCandidate, AlertPriority


class TestTwilioConfig:
    """Tests for TwilioConfig."""

    def test_from_env_empty(self):
        """Test loading config from empty environment."""
        with patch.dict('os.environ', {}, clear=True):
            config = TwilioConfig.from_env()
            assert config.account_sid == ""
            assert config.is_configured is False

    def test_from_env_configured(self):
        """Test loading config from environment."""
        env = {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token123",
            "TWILIO_FROM_NUMBER": "+1234567890",
            "TWILIO_WHATSAPP_NUMBER": "+0987654321",
        }
        with patch.dict('os.environ', env, clear=True):
            config = TwilioConfig.from_env()
            assert config.account_sid == "AC123"
            assert config.auth_token == "token123"
            assert config.is_configured is True

    def test_is_configured_partial(self):
        """Test that partial config is not considered configured."""
        config = TwilioConfig(
            account_sid="AC123",
            auth_token="",  # Missing
            from_number="+1234567890",
            whatsapp_number="",
        )
        assert config.is_configured is False


class TestSMSRecipient:
    """Tests for SMSRecipient."""

    def test_default_values(self):
        """Test default recipient values."""
        recipient = SMSRecipient(phone_number="+1234567890")

        assert recipient.preferred_channel == DeliveryChannel.SMS
        assert recipient.min_threat_level == "high"
        assert recipient.enabled is True
        assert len(recipient.regions) == 0

    def test_with_filters(self):
        """Test recipient with filters."""
        recipient = SMSRecipient(
            phone_number="+1234567890",
            name="John Doe",
            regions={"europe", "africa"},
            min_threat_level="critical",
            preferred_channel=DeliveryChannel.WHATSAPP,
        )

        assert "europe" in recipient.regions
        assert recipient.min_threat_level == "critical"


class TestFormatAlertMessage:
    """Tests for alert message formatting."""

    def test_format_basic_message(self):
        """Test basic message formatting."""
        # Create mock event and rule
        event = MagicMock()
        event.title = "Armed Conflict in Region X"
        event.region = "Europe"
        event.link = "https://example.com/event/1"

        rule = MagicMock()
        rule.name = "High Threat Alert"
        rule.priority = AlertPriority.HIGH

        candidate = AlertCandidate(event=event, rule=rule)

        message = format_alert_message(candidate)

        assert "ALERT" in message
        assert "High Threat Alert" in message
        assert "Europe" in message

    def test_format_truncates_long_title(self):
        """Test that long titles are truncated."""
        event = MagicMock()
        event.title = "A" * 200  # Very long title
        event.region = "Europe"
        event.link = None

        rule = MagicMock()
        rule.name = "Alert"
        rule.priority = AlertPriority.MEDIUM

        candidate = AlertCandidate(event=event, rule=rule)

        message = format_alert_message(candidate, max_length=160)

        assert len(message) <= 160

    def test_format_priority_emoji(self):
        """Test that priority emoji is included."""
        event = MagicMock()
        event.title = "Test Event"
        event.region = "Test"
        event.link = None

        for priority, emoji in [
            (AlertPriority.CRITICAL, "🚨"),
            (AlertPriority.HIGH, "⚠️"),
            (AlertPriority.MEDIUM, "📢"),
            (AlertPriority.LOW, "ℹ️"),
        ]:
            rule = MagicMock()
            rule.name = "Test"
            rule.priority = priority

            candidate = AlertCandidate(event=event, rule=rule)
            message = format_alert_message(candidate)

            assert emoji in message


class TestTwilioClient:
    """Tests for TwilioClient."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured Twilio client."""
        config = TwilioConfig(
            account_sid="AC123",
            auth_token="token123",
            from_number="+1234567890",
            whatsapp_number="+0987654321",
        )
        return TwilioClient(config)

    @pytest.fixture
    def unconfigured_client(self):
        """Create an unconfigured Twilio client."""
        config = TwilioConfig(
            account_sid="",
            auth_token="",
            from_number="",
            whatsapp_number="",
        )
        return TwilioClient(config)

    @pytest.mark.asyncio
    async def test_send_sms_unconfigured(self, unconfigured_client):
        """Test that unconfigured client returns error."""
        result = await unconfigured_client.send_sms("+1111111111", "Test message")

        assert result.success is False
        assert "not configured" in result.error.lower()

    @pytest.mark.asyncio
    async def test_send_sms_success(self, configured_client):
        """Test successful SMS send."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"sid": "SM123"}

        with patch.object(configured_client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get.return_value = mock_client

            result = await configured_client.send_sms("+1111111111", "Test message")

        assert result.success is True
        assert result.message_sid == "SM123"
        assert result.channel == DeliveryChannel.SMS

    @pytest.mark.asyncio
    async def test_send_sms_failure(self, configured_client):
        """Test SMS send failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid phone number"}

        with patch.object(configured_client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get.return_value = mock_client

            result = await configured_client.send_sms("+invalid", "Test message")

        assert result.success is False
        assert "Invalid phone number" in result.error

    @pytest.mark.asyncio
    async def test_send_whatsapp_formats_number(self, configured_client):
        """Test that WhatsApp properly formats numbers."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"sid": "WA123"}

        with patch.object(configured_client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get.return_value = mock_client

            result = await configured_client.send_whatsapp("+1111111111", "Test")

        # Verify the call was made with whatsapp: prefix
        call_args = mock_client.post.call_args
        assert "whatsapp:" in str(call_args)
        assert result.channel == DeliveryChannel.WHATSAPP


class TestTwilioSMSSink:
    """Tests for TwilioSMSSink alert sink."""

    @pytest.fixture
    def sink_with_recipients(self):
        """Create a sink with test recipients."""
        config = TwilioConfig(
            account_sid="AC123",
            auth_token="token123",
            from_number="+1234567890",
            whatsapp_number="+0987654321",
        )

        recipients = [
            SMSRecipient(
                phone_number="+1111111111",
                name="User 1",
                regions={"europe"},
                min_threat_level="high",
            ),
            SMSRecipient(
                phone_number="+2222222222",
                name="User 2",
                regions={"asia"},
                min_threat_level="medium",
            ),
        ]

        return TwilioSMSSink(recipients=recipients, config=config)

    def test_should_notify_region_match(self, sink_with_recipients):
        """Test recipient filtering by region."""
        event = MagicMock()
        event.region = "Europe"
        event.threat_level = "critical"

        rule = MagicMock()
        rule.priority = AlertPriority.CRITICAL

        candidate = AlertCandidate(event=event, rule=rule)

        # User 1 should match (Europe region)
        assert sink_with_recipients._should_notify(
            sink_with_recipients.recipients[0], candidate
        ) is True

        # User 2 should not match (Asia region)
        assert sink_with_recipients._should_notify(
            sink_with_recipients.recipients[1], candidate
        ) is False

    def test_should_notify_threat_level(self, sink_with_recipients):
        """Test recipient filtering by threat level."""
        event = MagicMock()
        event.region = "Asia"  # Matches User 2
        event.threat_level = "medium"

        rule = MagicMock()
        rule.priority = AlertPriority.MEDIUM

        candidate = AlertCandidate(event=event, rule=rule)

        # User 2 should match (medium threat, Asia region)
        assert sink_with_recipients._should_notify(
            sink_with_recipients.recipients[1], candidate
        ) is True

        # Change to low threat
        event.threat_level = "low"

        # User 2 should not match (below min_threat_level)
        assert sink_with_recipients._should_notify(
            sink_with_recipients.recipients[1], candidate
        ) is False
