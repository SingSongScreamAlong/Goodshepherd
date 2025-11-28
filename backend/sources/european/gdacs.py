"""GDACS (Global Disaster Alert and Coordination System) Connector.

Fetches disaster alerts from GDACS, a cooperation framework between
the United Nations and the European Commission.
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GDACSAlert:
    """GDACS disaster alert."""
    id: str
    title: str
    description: str
    event_type: str  # EQ, TC, FL, VO, DR, WF (earthquake, cyclone, flood, volcano, drought, wildfire)
    alert_level: str  # Green, Orange, Red
    country: str
    region: str
    latitude: float
    longitude: float
    event_date: datetime
    severity: dict
    population_affected: Optional[int]
    url: str


class GDACSConnector:
    """Connector for GDACS disaster alerts.
    
    GDACS provides near real-time alerts about natural disasters
    around the world and tools to facilitate response coordination.
    """

    RSS_URL = "https://www.gdacs.org/xml/rss.xml"
    CAP_URL = "https://www.gdacs.org/xml/rss_cap.xml"
    
    # Event type mapping
    EVENT_TYPES = {
        "EQ": "earthquake",
        "TC": "tropical_cyclone",
        "FL": "flood",
        "VO": "volcano",
        "DR": "drought",
        "WF": "wildfire",
    }
    
    # Alert level to threat level mapping
    ALERT_TO_THREAT = {
        "Red": "critical",
        "Orange": "high",
        "Green": "medium",
    }

    def __init__(self):
        self.timeout = 30

    async def get_alerts(
        self,
        event_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        region: Optional[str] = None,
    ) -> list[GDACSAlert]:
        """Fetch current GDACS alerts."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.RSS_URL,
                    headers={"User-Agent": "GoodShepherd/1.0"},
                )
                response.raise_for_status()

                alerts = self._parse_rss(response.text)

                # Apply filters
                if event_type:
                    alerts = [a for a in alerts if a.event_type == event_type]
                if alert_level:
                    alerts = [a for a in alerts if a.alert_level == alert_level]
                if region:
                    region_lower = region.lower()
                    alerts = [
                        a for a in alerts
                        if region_lower in a.region.lower() or region_lower in a.country.lower()
                    ]

                return alerts

        except httpx.HTTPError as e:
            logger.error(f"GDACS fetch failed: {e}")
            return []

    async def get_european_alerts(self) -> list[GDACSAlert]:
        """Get alerts specifically for European region."""
        european_countries = [
            "Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia",
            "Bulgaria", "Croatia", "Cyprus", "Czech", "Denmark", "Estonia",
            "Finland", "France", "Germany", "Greece", "Hungary", "Iceland",
            "Ireland", "Italy", "Kosovo", "Latvia", "Liechtenstein", "Lithuania",
            "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
            "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Russia",
            "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden",
            "Switzerland", "Turkey", "Ukraine", "United Kingdom", "Vatican",
        ]

        all_alerts = await self.get_alerts()
        
        european_alerts = []
        for alert in all_alerts:
            for country in european_countries:
                if country.lower() in alert.country.lower():
                    european_alerts.append(alert)
                    break

        return european_alerts

    async def get_high_priority_alerts(self) -> list[GDACSAlert]:
        """Get Red and Orange level alerts."""
        alerts = await self.get_alerts()
        return [a for a in alerts if a.alert_level in ["Red", "Orange"]]

    def to_event_format(self, alert: GDACSAlert) -> dict:
        """Convert GDACS alert to standard event format."""
        return {
            "source": "gdacs",
            "source_id": alert.id,
            "title": alert.title,
            "summary": alert.description,
            "category": "disaster",
            "subcategory": self.EVENT_TYPES.get(alert.event_type, alert.event_type),
            "threat_level": self.ALERT_TO_THREAT.get(alert.alert_level, "medium"),
            "region": alert.region,
            "country": alert.country,
            "geocode": {
                "lat": alert.latitude,
                "lon": alert.longitude,
            },
            "published_at": alert.event_date.isoformat(),
            "link": alert.url,
            "raw": {
                "event_type": alert.event_type,
                "alert_level": alert.alert_level,
                "severity": alert.severity,
                "population_affected": alert.population_affected,
            },
        }

    def _parse_rss(self, xml_content: str) -> list[GDACSAlert]:
        """Parse GDACS RSS feed."""
        alerts = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            ns = {
                "gdacs": "http://www.gdacs.org",
                "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
            }

            for item in root.findall(".//item"):
                try:
                    # Extract basic info
                    title = item.findtext("title", "")
                    description = item.findtext("description", "")
                    link = item.findtext("link", "")
                    guid = item.findtext("guid", "")

                    # Extract GDACS-specific data
                    event_type = item.findtext("gdacs:eventtype", "", ns)
                    alert_level = item.findtext("gdacs:alertlevel", "", ns)
                    country = item.findtext("gdacs:country", "", ns)
                    
                    # Extract coordinates
                    lat = float(item.findtext("geo:lat", "0", ns) or "0")
                    lon = float(item.findtext("geo:long", "0", ns) or "0")

                    # Extract severity info
                    severity = {}
                    severity_elem = item.find("gdacs:severity", ns)
                    if severity_elem is not None:
                        severity = {
                            "value": severity_elem.get("value"),
                            "unit": severity_elem.get("unit"),
                        }

                    # Parse date
                    pub_date = item.findtext("pubDate", "")
                    event_date = self._parse_date(pub_date)

                    # Extract population affected
                    pop_text = item.findtext("gdacs:population", "", ns)
                    population = int(pop_text) if pop_text and pop_text.isdigit() else None

                    alerts.append(GDACSAlert(
                        id=guid or f"gdacs-{event_type}-{hash(title)}",
                        title=title,
                        description=description,
                        event_type=event_type,
                        alert_level=alert_level,
                        country=country,
                        region=self._extract_region(title, country),
                        latitude=lat,
                        longitude=lon,
                        event_date=event_date,
                        severity=severity,
                        population_affected=population,
                        url=link,
                    ))

                except Exception as e:
                    logger.warning(f"Failed to parse GDACS item: {e}")
                    continue

        except ET.ParseError as e:
            logger.error(f"Failed to parse GDACS RSS: {e}")

        return alerts

    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS date format."""
        try:
            # RFC 822 format: "Sat, 01 Jan 2000 00:00:00 GMT"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()

    def _extract_region(self, title: str, country: str) -> str:
        """Extract region from title or use country."""
        # Try to extract more specific location from title
        if " in " in title:
            parts = title.split(" in ")
            if len(parts) > 1:
                return parts[-1].strip()
        return country or "Unknown"
