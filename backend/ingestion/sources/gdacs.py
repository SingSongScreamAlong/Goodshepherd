"""GDACS (Global Disaster Alert and Coordination System) data source.

GDACS provides near real-time alerts about natural disasters around the world.
https://www.gdacs.org/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Optional
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GDACSEvent:
    """Represents a GDACS disaster event."""

    event_id: str
    event_type: str  # EQ, TC, FL, VO, DR, WF (earthquake, cyclone, flood, volcano, drought, wildfire)
    title: str
    description: str
    severity: str  # Green, Orange, Red
    alert_level: float  # 0-3 scale
    country: str
    region: str
    latitude: float
    longitude: float
    event_date: datetime
    url: str
    population_affected: Optional[int] = None

    def to_event_dict(self) -> dict:
        """Convert to standard event dictionary format."""
        # Map GDACS severity to threat level
        threat_map = {
            "red": "critical",
            "orange": "high",
            "green": "medium",
        }

        return {
            "title": self.title,
            "summary": self.description,
            "category": f"disaster:{self.event_type.lower()}",
            "region": self.country or self.region,
            "source_url": "https://www.gdacs.org",
            "link": self.url,
            "confidence": min(self.alert_level / 3.0, 1.0),
            "geocode": {
                "lat": self.latitude,
                "lon": self.longitude,
                "display_name": f"{self.country}, {self.region}",
            },
            "published_at": self.event_date.isoformat(),
            "threat_level": threat_map.get(self.severity.lower(), "medium"),
            "raw": f"GDACS:{self.event_id}",
        }


@dataclass
class GDACSConfig:
    """Configuration for GDACS data source."""

    feed_url: str = "https://www.gdacs.org/xml/rss.xml"
    timeout: float = 30.0
    event_types: set[str] = field(default_factory=lambda: {"EQ", "TC", "FL", "VO", "WF"})
    min_alert_level: float = 1.0  # Minimum alert level to include (0-3)


class GDACSSource:
    """GDACS RSS feed data source."""

    # GDACS RSS namespaces
    NAMESPACES = {
        "gdacs": "http://www.gdacs.org",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def __init__(self, config: Optional[GDACSConfig] = None):
        self.config = config or GDACSConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"User-Agent": "GoodShepherd/1.0"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_events(self) -> AsyncIterator[GDACSEvent]:
        """Fetch and parse GDACS events."""
        client = await self._get_client()

        try:
            response = await client.get(self.config.feed_url)
            response.raise_for_status()

            root = ElementTree.fromstring(response.content)

            for item in root.findall(".//item"):
                try:
                    event = self._parse_item(item)
                    if event and self._should_include(event):
                        yield event
                except Exception as e:
                    logger.warning(f"Failed to parse GDACS item: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch GDACS feed: {e}")
        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse GDACS XML: {e}")

    def _parse_item(self, item: ElementTree.Element) -> Optional[GDACSEvent]:
        """Parse a single RSS item into a GDACSEvent."""

        def get_text(path: str, ns: dict = None) -> str:
            elem = item.find(path, ns or self.NAMESPACES)
            return elem.text.strip() if elem is not None and elem.text else ""

        def get_float(path: str, default: float = 0.0) -> float:
            text = get_text(path)
            try:
                return float(text) if text else default
            except ValueError:
                return default

        event_id = get_text("gdacs:eventid", self.NAMESPACES)
        if not event_id:
            return None

        # Parse event type from category or eventtype
        event_type = get_text("gdacs:eventtype", self.NAMESPACES) or ""

        # Parse severity/alert level
        severity = get_text("gdacs:severity", self.NAMESPACES) or "Green"
        alert_level = get_float("gdacs:alertlevel", 0.0)

        # Parse location
        lat = get_float("geo:lat")
        lon = get_float("geo:long")

        # Parse date
        pub_date_str = get_text("pubDate")
        try:
            event_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        except (ValueError, TypeError):
            event_date = datetime.utcnow()

        return GDACSEvent(
            event_id=event_id,
            event_type=event_type.upper(),
            title=get_text("title"),
            description=get_text("description"),
            severity=severity,
            alert_level=alert_level,
            country=get_text("gdacs:country", self.NAMESPACES),
            region=get_text("gdacs:region", self.NAMESPACES),
            latitude=lat,
            longitude=lon,
            event_date=event_date,
            url=get_text("link"),
            population_affected=int(get_float("gdacs:population", 0)) or None,
        )

    def _should_include(self, event: GDACSEvent) -> bool:
        """Check if event meets inclusion criteria."""
        if event.event_type not in self.config.event_types:
            return False
        if event.alert_level < self.config.min_alert_level:
            return False
        return True

    async def get_events_as_dicts(self) -> list[dict]:
        """Fetch events and return as list of dictionaries."""
        events = []
        async for event in self.fetch_events():
            events.append(event.to_event_dict())
        return events
