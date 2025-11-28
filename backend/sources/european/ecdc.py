"""ECDC (European Centre for Disease Prevention and Control) Connector.

Fetches health threat data from ECDC for European health surveillance.
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ECDCAlert:
    """ECDC health alert."""
    id: str
    title: str
    summary: str
    disease: str
    threat_level: str
    countries_affected: list[str]
    published_at: datetime
    updated_at: Optional[datetime]
    url: str
    case_count: Optional[int]
    death_count: Optional[int]


class ECDCConnector:
    """Connector for ECDC health surveillance data.
    
    ECDC provides surveillance data and risk assessments for
    communicable diseases in the EU/EEA.
    """

    RSS_URL = "https://www.ecdc.europa.eu/en/taxonomy/term/1/feed"
    THREAT_ASSESSMENT_URL = "https://www.ecdc.europa.eu/en/threats-and-outbreaks/reports-and-data/weekly-threats"
    
    # Disease categories
    DISEASE_CATEGORIES = {
        "respiratory": ["covid", "influenza", "flu", "respiratory", "pneumonia", "tuberculosis"],
        "vector_borne": ["malaria", "dengue", "zika", "chikungunya", "west nile", "tick"],
        "food_water": ["salmonella", "e. coli", "listeria", "cholera", "hepatitis a"],
        "vaccine_preventable": ["measles", "polio", "diphtheria", "pertussis", "mumps"],
        "emerging": ["ebola", "marburg", "mpox", "monkeypox", "novel"],
    }

    def __init__(self):
        self.timeout = 30

    async def get_alerts(self) -> list[ECDCAlert]:
        """Fetch current ECDC health alerts."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.RSS_URL,
                    headers={"User-Agent": "GoodShepherd/1.0"},
                )
                response.raise_for_status()

                return self._parse_rss(response.text)

        except httpx.HTTPError as e:
            logger.error(f"ECDC fetch failed: {e}")
            return []

    async def get_threat_assessments(self) -> list[dict]:
        """Get weekly threat assessment summaries."""
        # This would parse the ECDC threat assessment page
        # For now, return structured placeholder
        return []

    async def get_disease_alerts(self, disease: str) -> list[ECDCAlert]:
        """Get alerts for a specific disease."""
        alerts = await self.get_alerts()
        disease_lower = disease.lower()
        return [
            a for a in alerts
            if disease_lower in a.title.lower() or disease_lower in a.summary.lower()
        ]

    async def get_high_priority_alerts(self) -> list[ECDCAlert]:
        """Get high and critical priority alerts."""
        alerts = await self.get_alerts()
        return [a for a in alerts if a.threat_level in ["critical", "high"]]

    def to_event_format(self, alert: ECDCAlert) -> dict:
        """Convert ECDC alert to standard event format."""
        return {
            "source": "ecdc",
            "source_id": alert.id,
            "title": alert.title,
            "summary": alert.summary,
            "category": "health",
            "subcategory": self._categorize_disease(alert.disease),
            "threat_level": alert.threat_level,
            "region": "Europe",
            "countries": alert.countries_affected,
            "published_at": alert.published_at.isoformat(),
            "link": alert.url,
            "raw": {
                "disease": alert.disease,
                "case_count": alert.case_count,
                "death_count": alert.death_count,
            },
        }

    def _parse_rss(self, xml_content: str) -> list[ECDCAlert]:
        """Parse ECDC RSS feed."""
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

                    # Extract disease from title
                    disease = self._extract_disease(title)
                    
                    # Determine threat level based on keywords
                    threat_level = self._assess_threat_level(title, description)
                    
                    # Extract countries mentioned
                    countries = self._extract_countries(title + " " + description)

                    alerts.append(ECDCAlert(
                        id=guid or f"ecdc-{hash(title)}",
                        title=title,
                        summary=self._clean_html(description),
                        disease=disease,
                        threat_level=threat_level,
                        countries_affected=countries,
                        published_at=self._parse_date(pub_date),
                        updated_at=None,
                        url=link,
                        case_count=self._extract_number(description, "cases"),
                        death_count=self._extract_number(description, "deaths"),
                    ))

                except Exception as e:
                    logger.warning(f"Failed to parse ECDC item: {e}")
                    continue

        except ET.ParseError as e:
            logger.error(f"Failed to parse ECDC RSS: {e}")

        return alerts

    def _extract_disease(self, text: str) -> str:
        """Extract disease name from text."""
        text_lower = text.lower()
        
        # Check known diseases
        known_diseases = [
            "covid-19", "influenza", "measles", "mpox", "monkeypox",
            "salmonella", "listeria", "e. coli", "hepatitis",
            "tuberculosis", "malaria", "dengue", "west nile",
        ]
        
        for disease in known_diseases:
            if disease in text_lower:
                return disease.title()
        
        return "Unknown"

    def _assess_threat_level(self, title: str, description: str) -> str:
        """Assess threat level based on content."""
        text = (title + " " + description).lower()
        
        critical_keywords = ["outbreak", "epidemic", "pandemic", "emergency", "death", "fatal"]
        high_keywords = ["increase", "surge", "spread", "alert", "warning", "risk"]
        
        if any(kw in text for kw in critical_keywords):
            return "high"
        if any(kw in text for kw in high_keywords):
            return "medium"
        return "low"

    def _extract_countries(self, text: str) -> list[str]:
        """Extract EU country names from text."""
        eu_countries = [
            "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
            "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
            "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
            "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
            "Slovenia", "Spain", "Sweden",
            # EEA
            "Iceland", "Liechtenstein", "Norway",
        ]
        
        found = []
        text_lower = text.lower()
        for country in eu_countries:
            if country.lower() in text_lower:
                found.append(country)
        
        return found if found else ["EU/EEA"]

    def _categorize_disease(self, disease: str) -> str:
        """Categorize disease type."""
        disease_lower = disease.lower()
        for category, keywords in self.DISEASE_CATEGORIES.items():
            if any(kw in disease_lower for kw in keywords):
                return category
        return "other"

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()

    def _extract_number(self, text: str, keyword: str) -> Optional[int]:
        """Extract number associated with keyword."""
        import re
        pattern = rf'(\d+)\s*{keyword}'
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
        return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS date format."""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()
