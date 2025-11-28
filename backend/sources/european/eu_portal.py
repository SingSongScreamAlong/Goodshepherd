"""EU Open Data Portal Connector.

Fetches data from the European Union Open Data Portal (data.europa.eu).
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class EUDataset:
    """EU dataset metadata."""
    id: str
    title: str
    description: str
    publisher: str
    issued: Optional[datetime]
    modified: Optional[datetime]
    keywords: list[str]
    spatial: Optional[str]
    distributions: list[dict]


class EUDataPortalConnector:
    """Connector for EU Open Data Portal.
    
    Provides access to datasets from data.europa.eu including:
    - Emergency and crisis data
    - Public health information
    - Security and border data
    - Humanitarian assistance data
    """

    BASE_URL = "https://data.europa.eu/api/hub/search"
    
    # Relevant dataset categories for threat intelligence
    RELEVANT_CATEGORIES = [
        "GOVE",  # Government and public sector
        "HEAL",  # Health
        "JUST",  # Justice, legal system and public safety
        "INTR",  # International issues
    ]

    def __init__(self):
        self.api_key = os.getenv("EU_DATA_PORTAL_API_KEY")
        self.timeout = int(os.getenv("EU_DATA_PORTAL_TIMEOUT", "30"))

    async def search_datasets(
        self,
        query: str,
        categories: Optional[list[str]] = None,
        country: Optional[str] = None,
        limit: int = 20,
    ) -> list[EUDataset]:
        """Search for datasets matching query."""
        params = {
            "q": query,
            "limit": limit,
            "sort": "relevance+desc,modified+desc",
        }

        if categories:
            params["categories"] = ",".join(categories)
        if country:
            params["country"] = country

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/datasets",
                    params=params,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                datasets = []
                for result in data.get("result", {}).get("results", []):
                    datasets.append(self._parse_dataset(result))

                return datasets

        except httpx.HTTPError as e:
            logger.error(f"EU Data Portal search failed: {e}")
            return []

    async def get_crisis_datasets(
        self,
        region: Optional[str] = None,
    ) -> list[EUDataset]:
        """Get datasets related to crises and emergencies."""
        queries = [
            "emergency crisis",
            "humanitarian assistance",
            "disaster response",
            "security threat",
        ]

        all_datasets = []
        for query in queries:
            datasets = await self.search_datasets(
                query=query,
                categories=self.RELEVANT_CATEGORIES,
                country=region,
                limit=10,
            )
            all_datasets.extend(datasets)

        # Deduplicate by ID
        seen = set()
        unique = []
        for ds in all_datasets:
            if ds.id not in seen:
                seen.add(ds.id)
                unique.append(ds)

        return unique

    async def get_health_alerts(self) -> list[EUDataset]:
        """Get health-related alert datasets."""
        return await self.search_datasets(
            query="health alert outbreak disease",
            categories=["HEAL"],
            limit=20,
        )

    async def get_border_security_data(self) -> list[EUDataset]:
        """Get border and security datasets."""
        return await self.search_datasets(
            query="border security migration",
            categories=["JUST", "INTR"],
            limit=20,
        )

    def _get_headers(self) -> dict:
        """Get request headers."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "GoodShepherd/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _parse_dataset(self, data: dict) -> EUDataset:
        """Parse dataset from API response."""
        return EUDataset(
            id=data.get("id", ""),
            title=data.get("title", {}).get("en", data.get("title", "")),
            description=data.get("description", {}).get("en", ""),
            publisher=data.get("publisher", {}).get("name", "Unknown"),
            issued=self._parse_date(data.get("issued")),
            modified=self._parse_date(data.get("modified")),
            keywords=data.get("keywords", {}).get("en", []),
            spatial=data.get("spatial"),
            distributions=[
                {
                    "format": d.get("format", {}).get("label", "Unknown"),
                    "url": d.get("downloadUrl") or d.get("accessUrl"),
                }
                for d in data.get("distributions", [])
            ],
        )

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
