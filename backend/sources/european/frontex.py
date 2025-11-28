"""Frontex (European Border and Coast Guard Agency) Connector.

Fetches border security and migration data for European borders.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class FrontexAlert:
    """Frontex border/migration alert."""
    id: str
    title: str
    summary: str
    alert_type: str  # migration, border_security, smuggling, trafficking
    threat_level: str
    border_region: str
    countries_involved: list[str]
    published_at: datetime
    url: str
    statistics: Optional[dict]


class FrontexConnector:
    """Connector for Frontex border and migration data.
    
    Provides access to:
    - Border crossing statistics
    - Migration flow data
    - Risk analysis reports
    - Situational awareness updates
    """

    # Frontex public data endpoints
    NEWS_URL = "https://frontex.europa.eu/rss/news/"
    
    # European border regions
    BORDER_REGIONS = {
        "eastern": ["Poland", "Lithuania", "Latvia", "Estonia", "Finland", "Romania", "Bulgaria"],
        "western_balkans": ["Croatia", "Slovenia", "Hungary", "Greece", "Bulgaria"],
        "central_mediterranean": ["Italy", "Malta"],
        "western_mediterranean": ["Spain"],
        "eastern_mediterranean": ["Greece", "Cyprus"],
        "western_african": ["Spain", "Canary Islands"],
    }

    def __init__(self):
        self.timeout = 30

    async def get_news_alerts(self) -> list[FrontexAlert]:
        """Fetch Frontex news and alerts."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.NEWS_URL,
                    headers={"User-Agent": "GoodShepherd/1.0"},
                )
                response.raise_for_status()

                return self._parse_rss(response.text)

        except httpx.HTTPError as e:
            logger.error(f"Frontex fetch failed: {e}")
            return []

    async def get_border_region_alerts(self, region: str) -> list[FrontexAlert]:
        """Get alerts for a specific border region."""
        alerts = await self.get_news_alerts()
        
        region_countries = self.BORDER_REGIONS.get(region.lower(), [])
        if not region_countries:
            return alerts
        
        return [
            a for a in alerts
            if any(c in a.countries_involved for c in region_countries)
            or region.lower() in a.border_region.lower()
        ]

    async def get_high_priority_alerts(self) -> list[FrontexAlert]:
        """Get high priority border alerts."""
        alerts = await self.get_news_alerts()
        return [a for a in alerts if a.threat_level in ["critical", "high"]]

    def to_event_format(self, alert: FrontexAlert) -> dict:
        """Convert Frontex alert to standard event format."""
        return {
            "source": "frontex",
            "source_id": alert.id,
            "title": alert.title,
            "summary": alert.summary,
            "category": "political",
            "subcategory": alert.alert_type,
            "threat_level": alert.threat_level,
            "region": alert.border_region,
            "countries": alert.countries_involved,
            "published_at": alert.published_at.isoformat(),
            "link": alert.url,
            "raw": {
                "alert_type": alert.alert_type,
                "statistics": alert.statistics,
            },
        }

    def _parse_rss(self, xml_content: str) -> list[FrontexAlert]:
        """Parse Frontex RSS feed."""
        import xml.etree.ElementTree as ET
        
        alerts = []

        try:
            root = ET.fromstring(xml_content)

            for item in root.findall(".//item"):
                try:
                    title = item.findtext("title", "")
                    description = item.findtext("description", "")
                    link = item.findtext("link", "")
                    guid = item.findtext("guid", "")
                    pub_date = item.findtext("pubDate", "")

                    # Classify alert type
                    alert_type = self._classify_alert(title, description)
                    
                    # Assess threat level
                    threat_level = self._assess_threat_level(title, description)
                    
                    # Extract border region
                    border_region = self._extract_border_region(title, description)
                    
                    # Extract countries
                    countries = self._extract_countries(title + " " + description)

                    alerts.append(FrontexAlert(
                        id=guid or f"frontex-{hash(title)}",
                        title=title,
                        summary=self._clean_html(description),
                        alert_type=alert_type,
                        threat_level=threat_level,
                        border_region=border_region,
                        countries_involved=countries,
                        published_at=self._parse_date(pub_date),
                        url=link,
                        statistics=self._extract_statistics(description),
                    ))

                except Exception as e:
                    logger.warning(f"Failed to parse Frontex item: {e}")
                    continue

        except ET.ParseError as e:
            logger.error(f"Failed to parse Frontex RSS: {e}")

        return alerts

    def _classify_alert(self, title: str, description: str) -> str:
        """Classify the type of border alert."""
        text = (title + " " + description).lower()
        
        if any(kw in text for kw in ["smuggling", "smuggler"]):
            return "smuggling"
        if any(kw in text for kw in ["trafficking", "trafficker"]):
            return "trafficking"
        if any(kw in text for kw in ["migration", "migrant", "asylum", "refugee"]):
            return "migration"
        if any(kw in text for kw in ["border", "crossing", "security"]):
            return "border_security"
        
        return "general"

    def _assess_threat_level(self, title: str, description: str) -> str:
        """Assess threat level based on content."""
        text = (title + " " + description).lower()
        
        critical_keywords = ["emergency", "crisis", "surge", "record", "unprecedented"]
        high_keywords = ["increase", "rise", "concern", "alert", "warning"]
        
        if any(kw in text for kw in critical_keywords):
            return "high"
        if any(kw in text for kw in high_keywords):
            return "medium"
        return "low"

    def _extract_border_region(self, title: str, description: str) -> str:
        """Extract border region from text."""
        text = (title + " " + description).lower()
        
        region_keywords = {
            "Eastern Border": ["eastern", "poland", "belarus", "ukraine", "russia"],
            "Western Balkans": ["balkans", "serbia", "bosnia", "albania", "kosovo"],
            "Central Mediterranean": ["central mediterranean", "libya", "tunisia", "italy", "malta"],
            "Western Mediterranean": ["western mediterranean", "morocco", "spain", "gibraltar"],
            "Eastern Mediterranean": ["eastern mediterranean", "turkey", "greece", "aegean"],
            "Western African": ["canary", "atlantic", "mauritania", "senegal"],
        }
        
        for region, keywords in region_keywords.items():
            if any(kw in text for kw in keywords):
                return region
        
        return "European Borders"

    def _extract_countries(self, text: str) -> list[str]:
        """Extract country names from text."""
        countries = [
            "Poland", "Germany", "France", "Spain", "Italy", "Greece",
            "Bulgaria", "Romania", "Hungary", "Croatia", "Slovenia",
            "Austria", "Czech Republic", "Slovakia", "Lithuania", "Latvia",
            "Estonia", "Finland", "Sweden", "Denmark", "Netherlands",
            "Belgium", "Luxembourg", "Portugal", "Ireland", "Malta", "Cyprus",
            # Non-EU relevant
            "Turkey", "Ukraine", "Belarus", "Russia", "Serbia", "Albania",
            "Bosnia", "Montenegro", "North Macedonia", "Kosovo",
            "Morocco", "Tunisia", "Libya", "Egypt",
        ]
        
        found = []
        text_lower = text.lower()
        for country in countries:
            if country.lower() in text_lower:
                found.append(country)
        
        return found if found else ["Europe"]

    def _extract_statistics(self, text: str) -> Optional[dict]:
        """Extract numerical statistics from text."""
        import re
        
        stats = {}
        
        # Look for numbers with context
        patterns = [
            (r'(\d+(?:,\d+)*)\s*(?:irregular\s+)?(?:border\s+)?crossings?', 'crossings'),
            (r'(\d+(?:,\d+)*)\s*migrants?', 'migrants'),
            (r'(\d+(?:,\d+)*)\s*(?:percent|%)\s*(?:increase|decrease)', 'percent_change'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, text.lower())
            if match:
                value = match.group(1).replace(',', '')
                stats[key] = int(value)
        
        return stats if stats else None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()

    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS date format."""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()
