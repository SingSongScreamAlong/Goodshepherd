"""WHO Disease Outbreak News data source.

World Health Organization disease outbreak news and emergency updates.
https://www.who.int/emergencies/disease-outbreak-news
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Optional
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)


@dataclass
class WHOOutbreak:
    """Represents a WHO disease outbreak news item."""

    id: str
    title: str
    description: str
    url: str
    published_date: datetime
    disease: Optional[str]
    country: Optional[str]
    region: Optional[str]

    def to_event_dict(self) -> dict:
        """Convert to standard event dictionary format."""
        # Extract disease from title if not set
        disease = self.disease
        if not disease:
            disease = self._extract_disease_from_title()

        # Determine threat level based on keywords
        threat_level = "medium"
        title_lower = self.title.lower()
        desc_lower = self.description.lower()
        
        high_threat_keywords = [
            "outbreak", "epidemic", "emergency", "surge",
            "spreading", "deaths", "fatalities", "critical",
        ]
        critical_keywords = [
            "pandemic", "pheic", "international concern",
            "global health emergency",
        ]

        for keyword in critical_keywords:
            if keyword in title_lower or keyword in desc_lower:
                threat_level = "critical"
                break
        
        if threat_level != "critical":
            for keyword in high_threat_keywords:
                if keyword in title_lower or keyword in desc_lower:
                    threat_level = "high"
                    break

        return {
            "title": self.title,
            "summary": self.description[:1000] if self.description else None,
            "category": f"health:outbreak:{disease.lower().replace(' ', '_')}" if disease else "health:outbreak",
            "region": self.country or self.region,
            "source_url": "https://www.who.int",
            "link": self.url,
            "confidence": 0.95,  # WHO is highly authoritative
            "published_at": self.published_date.isoformat(),
            "threat_level": threat_level,
            "raw": f"WHO:{self.id}",
        }

    def _extract_disease_from_title(self) -> Optional[str]:
        """Try to extract disease name from title."""
        known_diseases = [
            "COVID-19", "Ebola", "Cholera", "Measles", "Polio",
            "Yellow Fever", "Dengue", "Malaria", "Mpox", "Marburg",
            "Avian Influenza", "H5N1", "H7N9", "MERS", "Lassa Fever",
            "Plague", "Typhoid", "Hepatitis", "Meningitis", "Diphtheria",
            "Chikungunya", "Zika", "Nipah", "Rift Valley Fever",
        ]
        
        title_lower = self.title.lower()
        for disease in known_diseases:
            if disease.lower() in title_lower:
                return disease
        
        return None


@dataclass
class WHOConfig:
    """Configuration for WHO data source."""

    # WHO RSS feeds
    outbreak_news_url: str = "https://www.who.int/feeds/entity/don/en/rss.xml"
    emergencies_url: str = "https://www.who.int/feeds/entity/emergencies/en/rss.xml"
    
    timeout: float = 30.0
    
    # Filters
    regions: list[str] = field(default_factory=list)  # WHO regions: AFRO, AMRO, EMRO, EURO, SEARO, WPRO
    diseases: list[str] = field(default_factory=list)
    
    # Include emergency news in addition to outbreak news
    include_emergencies: bool = True


class WHOOutbreakSource:
    """WHO Disease Outbreak News data source."""

    def __init__(self, config: Optional[WHOConfig] = None):
        self.config = config or WHOConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"User-Agent": "GoodShepherd/1.0 (health monitoring)"},
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_outbreaks(self) -> AsyncIterator[WHOOutbreak]:
        """Fetch outbreak news from WHO RSS feeds."""
        client = await self._get_client()

        # Fetch outbreak news
        async for outbreak in self._fetch_feed(client, self.config.outbreak_news_url):
            if self._should_include(outbreak):
                yield outbreak

        # Optionally fetch emergency news
        if self.config.include_emergencies:
            async for outbreak in self._fetch_feed(client, self.config.emergencies_url):
                if self._should_include(outbreak):
                    yield outbreak

    async def _fetch_feed(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> AsyncIterator[WHOOutbreak]:
        """Fetch and parse a single RSS feed."""
        try:
            response = await client.get(url)
            response.raise_for_status()

            root = ElementTree.fromstring(response.content)

            for item in root.findall(".//item"):
                try:
                    outbreak = self._parse_item(item)
                    if outbreak:
                        yield outbreak
                except Exception as e:
                    logger.warning(f"Failed to parse WHO item: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch WHO feed {url}: {e}")
        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse WHO XML: {e}")

    def _parse_item(self, item: ElementTree.Element) -> Optional[WHOOutbreak]:
        """Parse a single RSS item into a WHOOutbreak."""

        def get_text(tag: str) -> str:
            elem = item.find(tag)
            return elem.text.strip() if elem is not None and elem.text else ""

        title = get_text("title")
        if not title:
            return None

        # Generate ID from link or title
        link = get_text("link")
        outbreak_id = link.split("/")[-1] if link else title[:50].replace(" ", "_")

        # Parse date
        pub_date_str = get_text("pubDate")
        try:
            # WHO uses RFC 822 format
            published_date = datetime.strptime(
                pub_date_str, "%a, %d %b %Y %H:%M:%S %z"
            )
        except (ValueError, TypeError):
            try:
                # Try alternative format
                published_date = datetime.strptime(
                    pub_date_str.split("+")[0].strip(), "%a, %d %b %Y %H:%M:%S"
                )
            except (ValueError, TypeError):
                published_date = datetime.utcnow()

        # Extract country and region from title
        country, region = self._extract_location(title)

        return WHOOutbreak(
            id=outbreak_id,
            title=title,
            description=get_text("description"),
            url=link,
            published_date=published_date,
            disease=None,  # Will be extracted from title
            country=country,
            region=region,
        )

    def _extract_location(self, title: str) -> tuple[Optional[str], Optional[str]]:
        """Extract country and region from title."""
        # Common patterns: "Disease - Country" or "Disease in Country"
        
        # Try pattern: "... - Country"
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                location = parts[-1].strip()
                # Check if it looks like a country name
                if len(location) < 50 and not any(c.isdigit() for c in location):
                    return location, None

        # Try pattern: "... in Country"
        match = re.search(r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
        if match:
            return match.group(1), None

        return None, None

    def _should_include(self, outbreak: WHOOutbreak) -> bool:
        """Check if outbreak meets filter criteria."""
        # Region filter
        if self.config.regions:
            # Would need to map country to WHO region
            pass

        # Disease filter
        if self.config.diseases:
            disease = outbreak.disease or outbreak._extract_disease_from_title()
            if disease:
                if not any(d.lower() in disease.lower() for d in self.config.diseases):
                    return False

        return True

    async def get_outbreaks_as_dicts(self) -> list[dict]:
        """Fetch outbreaks and return as list of dictionaries."""
        outbreaks = []
        async for outbreak in self.fetch_outbreaks():
            outbreaks.append(outbreak.to_event_dict())
        return outbreaks


# Convenience function
async def fetch_who_outbreaks(
    diseases: Optional[list[str]] = None,
    include_emergencies: bool = True,
) -> list[dict]:
    """Fetch WHO outbreak events with optional filters."""
    config = WHOConfig(
        diseases=diseases or [],
        include_emergencies=include_emergencies,
    )
    source = WHOOutbreakSource(config)
    try:
        return await source.get_outbreaks_as_dicts()
    finally:
        await source.close()
