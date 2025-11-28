"""US State Department Travel Advisories data source.

Provides official travel advisories and safety information.
https://travel.state.gov/
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TravelAdvisory:
    """Represents a US State Department travel advisory."""

    country: str
    country_code: str
    advisory_level: int  # 1-4
    advisory_text: str
    date_updated: datetime
    url: str
    geo_coordinates: Optional[tuple[float, float]] = None

    @property
    def level_description(self) -> str:
        """Get human-readable level description."""
        descriptions = {
            1: "Exercise Normal Precautions",
            2: "Exercise Increased Caution",
            3: "Reconsider Travel",
            4: "Do Not Travel",
        }
        return descriptions.get(self.advisory_level, "Unknown")

    def to_event_dict(self) -> dict:
        """Convert to standard event dictionary format."""
        # Map advisory levels to threat levels
        threat_map = {
            1: "low",
            2: "medium",
            3: "high",
            4: "critical",
        }

        geocode = None
        if self.geo_coordinates:
            geocode = {
                "lat": self.geo_coordinates[0],
                "lon": self.geo_coordinates[1],
                "display_name": self.country,
            }

        return {
            "title": f"Travel Advisory: {self.country} - Level {self.advisory_level}",
            "summary": f"{self.level_description}. {self.advisory_text[:300]}",
            "category": "travel_advisory",
            "region": self.country,
            "source_url": "https://travel.state.gov",
            "link": self.url,
            "confidence": 1.0,  # Official government source
            "geocode": geocode,
            "published_at": self.date_updated.isoformat(),
            "threat_level": threat_map.get(self.advisory_level, "medium"),
            "raw": f"STATE_DEPT:{self.country_code}",
        }


@dataclass
class StateDeptConfig:
    """Configuration for State Department data source."""

    api_url: str = "https://travel.state.gov/_res/rss/TAsTWs.xml"
    timeout: float = 30.0
    min_level: int = 2  # Minimum advisory level to include


# Country coordinates for geocoding (subset of common countries)
COUNTRY_COORDINATES = {
    "Afghanistan": (33.93911, 67.709953),
    "Albania": (41.153332, 20.168331),
    "Algeria": (28.033886, 1.659626),
    "Argentina": (-38.416097, -63.616672),
    "Australia": (-25.274398, 133.775136),
    "Austria": (47.516231, 14.550072),
    "Belgium": (50.503887, 4.469936),
    "Brazil": (-14.235004, -51.92528),
    "Canada": (56.130366, -106.346771),
    "China": (35.86166, 104.195397),
    "Colombia": (4.570868, -74.297333),
    "Cuba": (21.521757, -77.781167),
    "Egypt": (26.820553, 30.802498),
    "France": (46.227638, 2.213749),
    "Germany": (51.165691, 10.451526),
    "Greece": (39.074208, 21.824312),
    "India": (20.593684, 78.96288),
    "Indonesia": (-0.789275, 113.921327),
    "Iran": (32.427908, 53.688046),
    "Iraq": (33.223191, 43.679291),
    "Israel": (31.046051, 34.851612),
    "Italy": (41.87194, 12.56738),
    "Japan": (36.204824, 138.252924),
    "Kenya": (-0.023559, 37.906193),
    "Mexico": (23.634501, -102.552784),
    "Morocco": (31.791702, -7.09262),
    "Netherlands": (52.132633, 5.291266),
    "Nigeria": (9.081999, 8.675277),
    "North Korea": (40.339852, 127.510093),
    "Pakistan": (30.375321, 69.345116),
    "Philippines": (12.879721, 121.774017),
    "Poland": (51.919438, 19.145136),
    "Russia": (61.52401, 105.318756),
    "Saudi Arabia": (23.885942, 45.079162),
    "South Africa": (-30.559482, 22.937506),
    "South Korea": (35.907757, 127.766922),
    "Spain": (40.463667, -3.74922),
    "Sudan": (12.862807, 30.217636),
    "Sweden": (60.128161, 18.643501),
    "Switzerland": (46.818188, 8.227512),
    "Syria": (34.802075, 38.996815),
    "Thailand": (15.870032, 100.992541),
    "Turkey": (38.963745, 35.243322),
    "Ukraine": (48.379433, 31.16558),
    "United Kingdom": (55.378051, -3.435973),
    "Venezuela": (6.42375, -66.58973),
    "Vietnam": (14.058324, 108.277199),
    "Yemen": (15.552727, 48.516388),
}


class StateDeptAdvisorySource:
    """US State Department Travel Advisory data source."""

    def __init__(self, config: Optional[StateDeptConfig] = None):
        self.config = config or StateDeptConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"User-Agent": "GoodShepherd/1.0"},
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_advisories(self) -> AsyncIterator[TravelAdvisory]:
        """Fetch and parse travel advisories."""
        client = await self._get_client()

        try:
            response = await client.get(self.config.api_url)
            response.raise_for_status()

            # Parse RSS feed
            from xml.etree import ElementTree
            root = ElementTree.fromstring(response.content)

            for item in root.findall(".//item"):
                try:
                    advisory = self._parse_item(item)
                    if advisory and advisory.advisory_level >= self.config.min_level:
                        yield advisory
                except Exception as e:
                    logger.warning(f"Failed to parse advisory item: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch State Dept advisories: {e}")
        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse advisory XML: {e}")

    def _parse_item(self, item) -> Optional[TravelAdvisory]:
        """Parse a single RSS item into a TravelAdvisory."""

        def get_text(tag: str) -> str:
            elem = item.find(tag)
            return elem.text.strip() if elem is not None and elem.text else ""

        title = get_text("title")
        if not title:
            return None

        # Parse country and level from title
        # Format: "Country Name - Level X: Description"
        match = re.match(r"(.+?)\s*-\s*Level\s*(\d)", title)
        if not match:
            return None

        country = match.group(1).strip()
        level = int(match.group(2))

        # Parse date
        pub_date_str = get_text("pubDate")
        try:
            date_updated = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        except (ValueError, TypeError):
            date_updated = datetime.utcnow()

        # Get coordinates
        coords = COUNTRY_COORDINATES.get(country)

        # Generate country code (simplified)
        country_code = country[:3].upper()

        return TravelAdvisory(
            country=country,
            country_code=country_code,
            advisory_level=level,
            advisory_text=get_text("description"),
            date_updated=date_updated,
            url=get_text("link"),
            geo_coordinates=coords,
        )

    async def get_advisories_as_dicts(self) -> list[dict]:
        """Fetch advisories and return as list of dictionaries."""
        advisories = []
        async for advisory in self.fetch_advisories():
            advisories.append(advisory.to_event_dict())
        return advisories
