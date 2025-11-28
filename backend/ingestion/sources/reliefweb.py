"""ReliefWeb API data source for humanitarian crisis information.

ReliefWeb is the leading humanitarian information source on global crises and disasters.
https://reliefweb.int/
API: https://api.reliefweb.int/v1/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ReliefWebReport:
    """Represents a ReliefWeb report/update."""

    id: str
    title: str
    body: str
    source: str
    url: str
    date: datetime
    country: str
    countries: list[str]
    disaster_types: list[str]
    themes: list[str]
    format: str  # News, Situation Report, etc.
    language: str

    def to_event_dict(self) -> dict:
        """Convert to standard event dictionary format."""
        # Map disaster types to categories
        category = "humanitarian"
        if self.disaster_types:
            dtype = self.disaster_types[0].lower()
            if "flood" in dtype:
                category = "disaster:flood"
            elif "earthquake" in dtype:
                category = "disaster:earthquake"
            elif "cyclone" in dtype or "storm" in dtype or "hurricane" in dtype:
                category = "disaster:storm"
            elif "drought" in dtype:
                category = "disaster:drought"
            elif "conflict" in dtype or "war" in dtype:
                category = "conflict"
            elif "epidemic" in dtype or "disease" in dtype:
                category = "health:outbreak"
            elif "volcano" in dtype:
                category = "disaster:volcano"
            elif "fire" in dtype:
                category = "disaster:wildfire"

        # Determine threat level based on format and themes
        threat_level = "medium"
        if "emergency" in " ".join(self.themes).lower():
            threat_level = "high"
        if self.format.lower() in ["flash update", "situation report"]:
            threat_level = "high"

        return {
            "title": self.title,
            "summary": self.body[:1000] if self.body else None,
            "category": category,
            "region": self.country,
            "source_url": "https://reliefweb.int",
            "link": self.url,
            "confidence": 0.9,  # ReliefWeb is highly reliable
            "published_at": self.date.isoformat(),
            "threat_level": threat_level,
            "raw": f"ReliefWeb:{self.id}",
        }


@dataclass
class ReliefWebConfig:
    """Configuration for ReliefWeb data source."""

    api_url: str = "https://api.reliefweb.int/v1"
    timeout: float = 30.0
    limit: int = 50  # Results per request
    
    # Filters
    countries: list[str] = field(default_factory=list)  # ISO3 codes
    disaster_types: list[str] = field(default_factory=list)
    formats: list[str] = field(default_factory=lambda: [
        "Situation Report",
        "Flash Update", 
        "News and Press Release",
    ])
    
    # Only get reports from last N days
    lookback_days: int = 7


class ReliefWebSource:
    """ReliefWeb API data source."""

    def __init__(self, config: Optional[ReliefWebConfig] = None):
        self.config = config or ReliefWebConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={
                    "User-Agent": "GoodShepherd/1.0 (humanitarian monitoring)",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_reports(self) -> AsyncIterator[ReliefWebReport]:
        """Fetch reports from ReliefWeb API."""
        client = await self._get_client()

        # Build query
        query = {
            "appname": "goodshepherd",
            "limit": self.config.limit,
            "preset": "latest",
            "profile": "full",
            "fields[include][]": [
                "id", "title", "body", "source", "url", "date",
                "country", "disaster_type", "theme", "format", "language",
            ],
        }

        # Add filters
        filters = []
        
        if self.config.countries:
            filters.append({
                "field": "country.iso3",
                "value": self.config.countries,
            })
        
        if self.config.disaster_types:
            filters.append({
                "field": "disaster_type.name",
                "value": self.config.disaster_types,
            })
        
        if self.config.formats:
            filters.append({
                "field": "format.name",
                "value": self.config.formats,
            })

        # Date filter
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=self.config.lookback_days)
        filters.append({
            "field": "date.created",
            "value": {"from": cutoff.strftime("%Y-%m-%dT%H:%M:%S+00:00")},
        })

        if filters:
            query["filter"] = {"conditions": filters, "operator": "AND"}

        try:
            response = await client.post(
                f"{self.config.api_url}/reports",
                json=query,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("data", []):
                try:
                    report = self._parse_report(item)
                    if report:
                        yield report
                except Exception as e:
                    logger.warning(f"Failed to parse ReliefWeb report: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch ReliefWeb reports: {e}")

    def _parse_report(self, item: dict) -> Optional[ReliefWebReport]:
        """Parse a single report from API response."""
        fields = item.get("fields", {})
        
        report_id = str(item.get("id", ""))
        if not report_id:
            return None

        # Parse date
        date_info = fields.get("date", {})
        date_str = date_info.get("created") or date_info.get("original")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.utcnow()
        except (ValueError, AttributeError):
            date = datetime.utcnow()

        # Extract countries
        countries = []
        primary_country = ""
        for country in fields.get("country", []):
            name = country.get("name", "")
            if name:
                countries.append(name)
                if not primary_country:
                    primary_country = name

        # Extract disaster types
        disaster_types = [
            dt.get("name", "") for dt in fields.get("disaster_type", [])
            if dt.get("name")
        ]

        # Extract themes
        themes = [
            t.get("name", "") for t in fields.get("theme", [])
            if t.get("name")
        ]

        # Get source
        sources = fields.get("source", [])
        source = sources[0].get("name", "Unknown") if sources else "Unknown"

        # Get format
        formats = fields.get("format", [])
        report_format = formats[0].get("name", "Report") if formats else "Report"

        # Get language
        languages = fields.get("language", [])
        language = languages[0].get("name", "English") if languages else "English"

        return ReliefWebReport(
            id=report_id,
            title=fields.get("title", "Untitled"),
            body=fields.get("body", "") or fields.get("body-html", ""),
            source=source,
            url=fields.get("url", ""),
            date=date,
            country=primary_country,
            countries=countries,
            disaster_types=disaster_types,
            themes=themes,
            format=report_format,
            language=language,
        )

    async def get_reports_as_dicts(self) -> list[dict]:
        """Fetch reports and return as list of dictionaries."""
        reports = []
        async for report in self.fetch_reports():
            reports.append(report.to_event_dict())
        return reports


# Convenience function
async def fetch_reliefweb_events(
    countries: Optional[list[str]] = None,
    lookback_days: int = 7,
) -> list[dict]:
    """Fetch ReliefWeb events with optional filters."""
    config = ReliefWebConfig(
        countries=countries or [],
        lookback_days=lookback_days,
    )
    source = ReliefWebSource(config)
    try:
        return await source.get_reports_as_dicts()
    finally:
        await source.close()
