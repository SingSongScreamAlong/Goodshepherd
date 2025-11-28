"""Tests for intelligence data sources (GDACS, ACLED, State Dept)."""

import pytest
from unittest.mock import patch
from datetime import datetime

from backend.ingestion.sources.gdacs import (
    GDACSSource,
    GDACSConfig,
    GDACSEvent,
)
from backend.ingestion.sources.acled import (
    ACLEDSource,
    ACLEDConfig,
    ACLEDEvent,
)
from backend.ingestion.sources.travel_advisories import (
    StateDeptAdvisorySource,
    StateDeptConfig,
    TravelAdvisory,
)


class TestGDACSEvent:
    """Tests for GDACSEvent."""

    def test_to_event_dict_earthquake(self):
        """Test converting earthquake event to dict."""
        event = GDACSEvent(
            event_id="EQ123",
            event_type="EQ",
            title="Magnitude 6.5 Earthquake",
            description="Strong earthquake detected",
            severity="Orange",
            alert_level=2.5,
            country="Japan",
            region="Asia",
            latitude=35.6762,
            longitude=139.6503,
            event_date=datetime(2025, 1, 15, 10, 30),
            url="https://gdacs.org/event/EQ123",
            population_affected=1000000,
        )

        result = event.to_event_dict()

        assert result["title"] == "Magnitude 6.5 Earthquake"
        assert result["category"] == "disaster:eq"
        assert result["region"] == "Japan"
        assert result["threat_level"] == "high"  # Orange = high
        assert result["geocode"]["lat"] == 35.6762
        assert "GDACS:EQ123" in result["raw"]

    def test_to_event_dict_red_severity(self):
        """Test that red severity maps to critical."""
        event = GDACSEvent(
            event_id="TC456",
            event_type="TC",
            title="Category 5 Cyclone",
            description="Extremely dangerous cyclone",
            severity="Red",
            alert_level=3.0,
            country="Philippines",
            region="Asia",
            latitude=14.5995,
            longitude=120.9842,
            event_date=datetime(2025, 1, 15),
            url="https://gdacs.org/event/TC456",
        )

        result = event.to_event_dict()

        assert result["threat_level"] == "critical"

    def test_confidence_calculation(self):
        """Test confidence is calculated from alert level."""
        event = GDACSEvent(
            event_id="FL789",
            event_type="FL",
            title="Flood Warning",
            description="River flooding expected",
            severity="Green",
            alert_level=1.5,  # 50% of max (3.0)
            country="Germany",
            region="Europe",
            latitude=52.52,
            longitude=13.405,
            event_date=datetime(2025, 1, 15),
            url="https://gdacs.org/event/FL789",
        )

        result = event.to_event_dict()

        assert result["confidence"] == 0.5


class TestGDACSSource:
    """Tests for GDACSSource."""

    @pytest.fixture
    def source(self):
        """Create a GDACS source."""
        config = GDACSConfig(
            event_types={"EQ", "TC", "FL"},
            min_alert_level=1.0,
        )
        return GDACSSource(config)

    def test_should_include_matching_event(self, source):
        """Test that matching events are included."""
        event = GDACSEvent(
            event_id="EQ123",
            event_type="EQ",
            title="Test",
            description="Test",
            severity="Orange",
            alert_level=2.0,
            country="Test",
            region="Test",
            latitude=0,
            longitude=0,
            event_date=datetime.now(),
            url="",
        )

        assert source._should_include(event) is True

    def test_should_exclude_low_alert_level(self, source):
        """Test that low alert level events are excluded."""
        event = GDACSEvent(
            event_id="EQ123",
            event_type="EQ",
            title="Test",
            description="Test",
            severity="Green",
            alert_level=0.5,  # Below min_alert_level
            country="Test",
            region="Test",
            latitude=0,
            longitude=0,
            event_date=datetime.now(),
            url="",
        )

        assert source._should_include(event) is False

    def test_should_exclude_wrong_event_type(self, source):
        """Test that wrong event types are excluded."""
        event = GDACSEvent(
            event_id="DR123",
            event_type="DR",  # Drought - not in config
            title="Test",
            description="Test",
            severity="Orange",
            alert_level=2.0,
            country="Test",
            region="Test",
            latitude=0,
            longitude=0,
            event_date=datetime.now(),
            url="",
        )

        assert source._should_include(event) is False


class TestACLEDEvent:
    """Tests for ACLEDEvent."""

    def test_to_event_dict_battle(self):
        """Test converting battle event to dict."""
        event = ACLEDEvent(
            event_id="ACLED123",
            event_date=datetime(2025, 1, 15),
            event_type="Battles",
            sub_event_type="Armed clash",
            actor1="Group A",
            actor2="Group B",
            country="Sudan",
            region="Africa",
            admin1="Khartoum",
            admin2="",
            location="Khartoum City",
            latitude=15.5007,
            longitude=32.5599,
            fatalities=5,
            notes="Armed clash between groups",
            source="Local media",
        )

        result = event.to_event_dict()

        assert "Battles" in result["title"]
        assert "5 fatalities" in result["title"]
        assert result["category"] == "conflict:battles"
        assert result["region"] == "Sudan"
        assert result["threat_level"] == "critical"  # Battles with 5 fatalities escalates to critical
        assert result["confidence"] == 0.9  # ACLED is well-verified

    def test_threat_level_escalation_with_fatalities(self):
        """Test that high fatalities escalate threat level."""
        event = ACLEDEvent(
            event_id="ACLED456",
            event_date=datetime(2025, 1, 15),
            event_type="Protests",
            sub_event_type="Peaceful protest",
            actor1="Protesters",
            actor2=None,
            country="France",
            region="Europe",
            admin1="Paris",
            admin2="",
            location="Paris",
            latitude=48.8566,
            longitude=2.3522,
            fatalities=15,  # High fatalities
            notes="Protest turned violent",
            source="Reuters",
        )

        result = event.to_event_dict()

        # Protests normally medium, but 15 fatalities escalates to critical
        assert result["threat_level"] == "critical"

    def test_violence_against_civilians(self):
        """Test violence against civilians event."""
        event = ACLEDEvent(
            event_id="ACLED789",
            event_date=datetime(2025, 1, 15),
            event_type="Violence against civilians",
            sub_event_type="Attack",
            actor1="Unknown armed group",
            actor2=None,
            country="Nigeria",
            region="Africa",
            admin1="Borno",
            admin2="",
            location="Maiduguri",
            latitude=11.8333,
            longitude=13.15,
            fatalities=0,
            notes="Attack on village",
            source="Local sources",
        )

        result = event.to_event_dict()

        assert result["threat_level"] == "high"


class TestACLEDSource:
    """Tests for ACLEDSource."""

    def test_config_from_env_empty(self):
        """Test loading config from empty environment."""
        with patch.dict('os.environ', {}, clear=True):
            config = ACLEDConfig.from_env()
            assert config.is_configured is False

    def test_config_from_env_configured(self):
        """Test loading config from environment."""
        env = {
            "ACLED_API_KEY": "key123",
            "ACLED_EMAIL": "test@example.com",
            "ACLED_REGIONS": "Europe,Africa",
        }
        with patch.dict('os.environ', env, clear=True):
            config = ACLEDConfig.from_env()
            assert config.is_configured is True
            assert "Europe" in config.regions
            assert "Africa" in config.regions

    @pytest.mark.asyncio
    async def test_fetch_events_unconfigured(self):
        """Test that unconfigured source yields no events."""
        config = ACLEDConfig(api_key="", email="")
        source = ACLEDSource(config)

        events = []
        async for event in source.fetch_events():
            events.append(event)

        assert len(events) == 0


class TestTravelAdvisory:
    """Tests for TravelAdvisory."""

    def test_level_description(self):
        """Test level description property."""
        advisory = TravelAdvisory(
            country="Test",
            country_code="TST",
            advisory_level=4,
            advisory_text="Do not travel",
            date_updated=datetime.now(),
            url="",
        )

        assert advisory.level_description == "Do Not Travel"

    def test_to_event_dict_level_4(self):
        """Test converting level 4 advisory to dict."""
        advisory = TravelAdvisory(
            country="Syria",
            country_code="SYR",
            advisory_level=4,
            advisory_text="Do not travel due to ongoing conflict",
            date_updated=datetime(2025, 1, 15),
            url="https://travel.state.gov/syria",
            geo_coordinates=(34.8021, 38.9968),
        )

        result = advisory.to_event_dict()

        assert "Level 4" in result["title"]
        assert result["threat_level"] == "critical"
        assert result["confidence"] == 1.0  # Official source
        assert result["geocode"]["lat"] == 34.8021

    def test_to_event_dict_level_2(self):
        """Test converting level 2 advisory to dict."""
        advisory = TravelAdvisory(
            country="France",
            country_code="FRA",
            advisory_level=2,
            advisory_text="Exercise increased caution",
            date_updated=datetime(2025, 1, 15),
            url="https://travel.state.gov/france",
        )

        result = advisory.to_event_dict()

        assert result["threat_level"] == "medium"
        assert result["geocode"] is None  # No coordinates provided


class TestStateDeptAdvisorySource:
    """Tests for StateDeptAdvisorySource."""

    @pytest.fixture
    def source(self):
        """Create a State Dept source."""
        config = StateDeptConfig(min_level=2)
        return StateDeptAdvisorySource(config)

    def test_parse_advisory_title(self, source):
        """Test parsing advisory from title."""
        from xml.etree import ElementTree

        xml = """
        <item>
            <title>Syria - Level 4: Do Not Travel</title>
            <link>https://travel.state.gov/syria</link>
            <description>Do not travel to Syria.</description>
            <pubDate>Wed, 15 Jan 2025 10:00:00 +0000</pubDate>
        </item>
        """

        item = ElementTree.fromstring(xml)
        advisory = source._parse_item(item)

        assert advisory is not None
        assert advisory.country == "Syria"
        assert advisory.advisory_level == 4

    def test_parse_invalid_title(self, source):
        """Test parsing invalid title returns None."""
        from xml.etree import ElementTree

        xml = """
        <item>
            <title>Some Other Content</title>
            <link>https://example.com</link>
            <description>Not an advisory</description>
        </item>
        """

        item = ElementTree.fromstring(xml)
        advisory = source._parse_item(item)

        assert advisory is None
