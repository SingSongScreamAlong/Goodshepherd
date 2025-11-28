"""Tests for PDF export and email digest services."""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from backend.reporting.pdf_export import (
    PDFReportGenerator,
    PDFStyle,
    ReportSection,
    generate_pdf_report,
)
from backend.reporting.email_digest import (
    SMTPConfig,
    DigestSubscription,
    EmailDigestService,
)


class TestPDFStyle:
    """Tests for PDFStyle."""

    def test_default_values(self):
        """Test default style values."""
        style = PDFStyle()

        assert style.title_font_size == 24
        assert style.body_font_size == 11
        assert style.primary_color == "#16a34a"


class TestReportSection:
    """Tests for ReportSection."""

    def test_basic_section(self):
        """Test creating a basic section."""
        section = ReportSection(
            title="Executive Summary",
            content="This is the summary.",
        )

        assert section.title == "Executive Summary"
        assert section.threat_level is None
        assert section.items is None

    def test_section_with_items(self):
        """Test section with items."""
        section = ReportSection(
            title="Critical Events",
            content="3 critical events",
            threat_level="critical",
            items=[
                {"title": "Event 1"},
                {"title": "Event 2"},
            ],
        )

        assert len(section.items) == 2


class TestPDFReportGenerator:
    """Tests for PDFReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a PDF generator."""
        return PDFReportGenerator()

    @pytest.fixture
    def sample_events(self):
        """Create sample events."""
        return [
            {
                "title": "Armed Conflict in Region A",
                "summary": "Ongoing armed conflict reported.",
                "region": "Europe",
                "category": "conflict",
                "threat_level": "critical",
                "published_at": "2025-01-15T10:00:00Z",
            },
            {
                "title": "Protest in City B",
                "summary": "Large protest gathering.",
                "region": "Europe",
                "category": "civil_unrest",
                "threat_level": "medium",
                "published_at": "2025-01-15T11:00:00Z",
            },
            {
                "title": "Travel Advisory Update",
                "summary": "Updated travel advisory.",
                "region": "Asia",
                "category": "travel_advisory",
                "threat_level": "low",
                "published_at": "2025-01-15T12:00:00Z",
            },
        ]

    def test_calculate_stats(self, generator, sample_events):
        """Test statistics calculation."""
        stats = generator._calculate_stats(sample_events)

        assert stats["total_events"] == 3
        assert stats["by_threat_level"]["critical"] == 1
        assert stats["by_threat_level"]["medium"] == 1
        assert stats["by_threat_level"]["low"] == 1
        assert stats["by_region"]["Europe"] == 2
        assert stats["by_region"]["Asia"] == 1

    def test_group_events_by_threat(self, generator, sample_events):
        """Test grouping events by threat level."""
        groups = generator._group_events_by_threat(sample_events)

        assert len(groups["critical"]) == 1
        assert len(groups["medium"]) == 1
        assert len(groups["low"]) == 1
        assert len(groups["high"]) == 0

    def test_generate_summary(self, generator, sample_events):
        """Test summary generation."""
        stats = generator._calculate_stats(sample_events)
        summary = generator._generate_summary(sample_events, stats)

        assert "3" in summary  # Total events
        assert "CRITICAL" in summary or "critical" in summary.lower()

    def test_generate_sitrep_pdf(self, generator, sample_events):
        """Test generating a situational report PDF."""
        stats = generator._calculate_stats(sample_events)

        pdf_bytes = generator.generate_sitrep_pdf(
            title="Test Report",
            summary="Test summary",
            events=sample_events,
            stats=stats,
            generated_at=datetime.utcnow(),
            region="Europe",
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

        # Check content includes expected text
        content = pdf_bytes.decode("utf-8")
        assert "Test Report" in content
        assert "Europe" in content

    def test_generate_daily_digest_pdf(self, generator, sample_events):
        """Test generating a daily digest PDF."""
        pdf_bytes = generator.generate_daily_digest_pdf(
            events=sample_events,
            date=datetime(2025, 1, 15),
            region="Europe",
        )

        assert isinstance(pdf_bytes, bytes)
        content = pdf_bytes.decode("utf-8")
        assert "January 15, 2025" in content


class TestGeneratePDFReport:
    """Tests for generate_pdf_report convenience function."""

    def test_generate_pdf_report(self):
        """Test the convenience function."""
        events = [
            {"title": "Test Event", "region": "Test", "threat_level": "high"},
        ]

        pdf_bytes = generate_pdf_report(
            title="Quick Report",
            events=events,
            region="Test Region",
        )

        assert isinstance(pdf_bytes, bytes)


class TestSMTPConfig:
    """Tests for SMTPConfig."""

    def test_from_env_empty(self):
        """Test loading from empty environment."""
        with patch.dict('os.environ', {}, clear=True):
            config = SMTPConfig.from_env()
            assert config.is_configured is False

    def test_from_env_configured(self):
        """Test loading from configured environment."""
        env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "user",
            "SMTP_PASSWORD": "pass",
            "SMTP_FROM_ADDRESS": "alerts@example.com",
        }
        with patch.dict('os.environ', env, clear=True):
            config = SMTPConfig.from_env()
            assert config.is_configured is True
            assert config.host == "smtp.example.com"
            assert config.port == 587


class TestDigestSubscription:
    """Tests for DigestSubscription."""

    def test_default_values(self):
        """Test default subscription values."""
        sub = DigestSubscription(email="test@example.com")

        assert sub.frequency == "daily"
        assert sub.min_threat_level == "medium"
        assert sub.include_pdf is True
        assert sub.enabled is True

    def test_with_filters(self):
        """Test subscription with filters."""
        sub = DigestSubscription(
            email="test@example.com",
            name="Test User",
            frequency="weekly",
            regions=["europe", "africa"],
            min_threat_level="high",
        )

        assert sub.frequency == "weekly"
        assert "europe" in sub.regions


class TestEmailDigestService:
    """Tests for EmailDigestService."""

    @pytest.fixture
    def service(self):
        """Create an email digest service."""
        config = SMTPConfig(
            host="smtp.test.com",
            port=587,
            username="test",
            password="test",
            from_address="alerts@test.com",
        )
        return EmailDigestService(config)

    @pytest.fixture
    def sample_subscription(self):
        """Create a sample subscription."""
        return DigestSubscription(
            email="user@example.com",
            name="Test User",
            regions=["europe"],
            min_threat_level="medium",
        )

    @pytest.fixture
    def sample_events(self):
        """Create sample events."""
        return [
            {
                "title": "Event 1",
                "region": "Europe",
                "threat_level": "high",
                "published_at": "2025-01-15T10:00:00Z",
            },
            {
                "title": "Event 2",
                "region": "Asia",
                "threat_level": "critical",
                "published_at": "2025-01-15T11:00:00Z",
            },
        ]

    def test_add_subscription(self, service, sample_subscription):
        """Test adding a subscription."""
        service.add_subscription(sample_subscription)

        assert len(service.list_subscriptions()) == 1
        assert service.get_subscription("user@example.com") is not None

    def test_remove_subscription(self, service, sample_subscription):
        """Test removing a subscription."""
        service.add_subscription(sample_subscription)
        result = service.remove_subscription("user@example.com")

        assert result is True
        assert len(service.list_subscriptions()) == 0

    def test_filter_events(self, service, sample_subscription, sample_events):
        """Test filtering events for subscription."""
        filtered = service._filter_events(sample_events, sample_subscription)

        # Only Europe event should match
        assert len(filtered) == 1
        assert filtered[0]["region"] == "Europe"

    def test_filter_events_by_threat_level(self, service, sample_events):
        """Test filtering by threat level."""
        sub = DigestSubscription(
            email="test@example.com",
            min_threat_level="critical",
        )

        filtered = service._filter_events(sample_events, sub)

        # Only critical event should match
        assert len(filtered) == 1
        assert filtered[0]["threat_level"] == "critical"

    def test_build_subject_critical(self, service, sample_events):
        """Test subject line with critical events."""
        now = datetime.utcnow()
        subject = service._build_subject(sample_events, now - timedelta(days=1), now)

        assert "🚨" in subject
        assert "Critical" in subject

    def test_build_subject_no_critical(self, service):
        """Test subject line without critical events."""
        events = [{"threat_level": "medium"}]
        now = datetime.utcnow()
        subject = service._build_subject(events, now - timedelta(days=1), now)

        assert "Digest" in subject
        assert "1 Events" in subject

    def test_build_html_body(self, service, sample_subscription, sample_events):
        """Test HTML body generation."""
        now = datetime.utcnow()
        html = service._build_html_body(
            sample_events,
            now - timedelta(days=1),
            now,
            sample_subscription,
        )

        assert "<!DOCTYPE html>" in html
        assert "Good Shepherd" in html
        assert "Event 1" in html

    def test_build_text_body(self, service, sample_events):
        """Test plain text body generation."""
        now = datetime.utcnow()
        text = service._build_text_body(sample_events, now - timedelta(days=1), now)

        assert "GOOD SHEPHERD" in text
        assert "Event 1" in text

    @pytest.mark.asyncio
    async def test_send_digest_no_matching_events(self, service, sample_subscription):
        """Test sending digest with no matching events."""
        events = [{"region": "Asia", "threat_level": "low"}]  # Won't match

        result = await service.send_digest(
            sample_subscription,
            events,
            datetime.utcnow() - timedelta(days=1),
            datetime.utcnow(),
        )

        assert result.success is True
        assert result.message_id == "skipped-no-events"

    def test_format_date(self, service):
        """Test date formatting."""
        result = service._format_date("2025-01-15T10:30:00Z")
        assert "Jan 15" in result

        result = service._format_date(None)
        assert result == "Unknown date"

        result = service._format_date("invalid")
        assert "invalid" in result
