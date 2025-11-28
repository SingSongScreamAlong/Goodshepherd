"""ACLED (Armed Conflict Location & Event Data) source.

ACLED provides real-time data on political violence and protest events.
https://acleddata.com/
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ACLEDEvent:
    """Represents an ACLED conflict event."""

    event_id: str
    event_date: datetime
    event_type: str  # Battles, Explosions/Remote violence, Violence against civilians, etc.
    sub_event_type: str
    actor1: str
    actor2: Optional[str]
    country: str
    region: str
    admin1: str  # First-level administrative division
    admin2: str  # Second-level administrative division
    location: str
    latitude: float
    longitude: float
    fatalities: int
    notes: str
    source: str

    def to_event_dict(self) -> dict:
        """Convert to standard event dictionary format."""
        # Map ACLED event types to threat levels
        threat_map = {
            "battles": "critical",
            "explosions/remote violence": "critical",
            "violence against civilians": "high",
            "riots": "high",
            "protests": "medium",
            "strategic developments": "low",
        }

        threat_level = threat_map.get(self.event_type.lower(), "medium")

        # Increase threat level if fatalities
        if self.fatalities > 10:
            threat_level = "critical"
        elif self.fatalities > 0:
            threat_level = "high" if threat_level != "critical" else threat_level

        # Build title
        title = f"{self.event_type}: {self.location}, {self.country}"
        if self.fatalities > 0:
            title += f" ({self.fatalities} fatalities)"

        return {
            "title": title,
            "summary": self.notes[:500] if self.notes else f"{self.sub_event_type} involving {self.actor1}",
            "category": f"conflict:{self.event_type.lower().replace(' ', '_')}",
            "region": self.country,
            "source_url": "https://acleddata.com",
            "link": f"https://acleddata.com/data-export-tool/?event_id={self.event_id}",
            "confidence": 0.9,  # ACLED data is well-verified
            "geocode": {
                "lat": self.latitude,
                "lon": self.longitude,
                "display_name": f"{self.location}, {self.admin1}, {self.country}",
            },
            "published_at": self.event_date.isoformat(),
            "threat_level": threat_level,
            "raw": f"ACLED:{self.event_id}",
        }


@dataclass
class ACLEDConfig:
    """Configuration for ACLED data source."""

    api_key: str = ""
    email: str = ""
    base_url: str = "https://api.acleddata.com/acled/read"
    timeout: float = 60.0
    lookback_days: int = 7
    regions: list[str] = field(default_factory=list)  # Filter by region
    countries: list[str] = field(default_factory=list)  # Filter by country
    event_types: list[str] = field(default_factory=list)  # Filter by event type
    limit: int = 500

    @classmethod
    def from_env(cls) -> "ACLEDConfig":
        """Load configuration from environment variables."""
        return cls(
            api_key=os.getenv("ACLED_API_KEY", ""),
            email=os.getenv("ACLED_EMAIL", ""),
            regions=os.getenv("ACLED_REGIONS", "").split(",") if os.getenv("ACLED_REGIONS") else [],
            countries=os.getenv("ACLED_COUNTRIES", "").split(",") if os.getenv("ACLED_COUNTRIES") else [],
        )

    @property
    def is_configured(self) -> bool:
        """Check if ACLED API is properly configured."""
        return bool(self.api_key and self.email)


class ACLEDSource:
    """ACLED API data source."""

    def __init__(self, config: Optional[ACLEDConfig] = None):
        self.config = config or ACLEDConfig.from_env()
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

    async def fetch_events(self) -> AsyncIterator[ACLEDEvent]:
        """Fetch and parse ACLED events."""
        if not self.config.is_configured:
            logger.warning("ACLED API not configured, skipping")
            return

        client = await self._get_client()

        # Build query parameters
        params = {
            "key": self.config.api_key,
            "email": self.config.email,
            "limit": self.config.limit,
        }

        # Date filter
        start_date = datetime.utcnow() - timedelta(days=self.config.lookback_days)
        params["event_date"] = start_date.strftime("%Y-%m-%d")
        params["event_date_where"] = ">="

        # Region/country filters
        if self.config.regions:
            params["region"] = "|".join(self.config.regions)
        if self.config.countries:
            params["country"] = "|".join(self.config.countries)
        if self.config.event_types:
            params["event_type"] = "|".join(self.config.event_types)

        try:
            response = await client.get(self.config.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                logger.error(f"ACLED API error: {data.get('error', 'Unknown error')}")
                return

            for item in data.get("data", []):
                try:
                    event = self._parse_item(item)
                    if event:
                        yield event
                except Exception as e:
                    logger.warning(f"Failed to parse ACLED item: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch ACLED data: {e}")

    def _parse_item(self, item: dict) -> Optional[ACLEDEvent]:
        """Parse a single ACLED data item."""

        event_id = item.get("event_id_cnty") or item.get("data_id")
        if not event_id:
            return None

        # Parse date
        event_date_str = item.get("event_date", "")
        try:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            event_date = datetime.utcnow()

        # Parse coordinates
        try:
            latitude = float(item.get("latitude", 0))
            longitude = float(item.get("longitude", 0))
        except (ValueError, TypeError):
            latitude = 0.0
            longitude = 0.0

        # Parse fatalities
        try:
            fatalities = int(item.get("fatalities", 0))
        except (ValueError, TypeError):
            fatalities = 0

        return ACLEDEvent(
            event_id=str(event_id),
            event_date=event_date,
            event_type=item.get("event_type", "Unknown"),
            sub_event_type=item.get("sub_event_type", ""),
            actor1=item.get("actor1", "Unknown"),
            actor2=item.get("actor2"),
            country=item.get("country", ""),
            region=item.get("region", ""),
            admin1=item.get("admin1", ""),
            admin2=item.get("admin2", ""),
            location=item.get("location", ""),
            latitude=latitude,
            longitude=longitude,
            fatalities=fatalities,
            notes=item.get("notes", ""),
            source=item.get("source", ""),
        )

    async def get_events_as_dicts(self) -> list[dict]:
        """Fetch events and return as list of dictionaries."""
        events = []
        async for event in self.fetch_events():
            events.append(event.to_event_dict())
        return events
