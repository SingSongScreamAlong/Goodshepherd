"""
Official Collector for government and official agency feeds.
Handles government advisories, disaster feeds, and humanitarian datasets.
"""
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from backend.core.logging import get_logger
from backend.models.source import Source, SourceType, CollectionMethod
from backend.models.raw_observation import RawObservation
from backend.collectors.collector_base import CollectorBase
from backend.collectors.rss_collector import RSSCollector

logger = get_logger(__name__)


class OfficialCollector(CollectorBase):
    """
    Collector for official government and agency sources.
    
    Supports:
    - Government advisory feeds (RSS/API)
    - Disaster monitoring feeds (GDACS, etc.)
    - Humanitarian datasets (UNHCR, WHO, etc.)
    - Official press releases
    
    These sources get higher trust_baseline by default.
    """
    
    def __init__(self):
        """Initialize Official collector."""
        super().__init__(CollectionMethod.API)
        self.rss_collector = RSSCollector()  # Reuse RSS logic for RSS feeds
        
        # Known official API endpoints
        self.known_apis = {
            "gdacs": self._collect_gdacs,
            "reliefweb": self._collect_reliefweb,
        }
    
    def validate_source(self, source: Source) -> bool:
        """
        Validate that source is an official source.
        
        Args:
            source: Source to validate
            
        Returns:
            True if source is official type with valid URL
        """
        if not source.url:
            return False
        if source.source_type != SourceType.OFFICIAL:
            return False
        return True
    
    def collect(self, source: Source) -> List[RawObservation]:
        """
        Collect data from an official source.
        
        Routes to appropriate collector based on source type.
        
        Args:
            source: Official source to collect from
            
        Returns:
            List of RawObservation objects
        """
        self.log_collection_start(source)
        
        observations = []
        
        # Check if it's a known API
        for api_name, collector_fn in self.known_apis.items():
            if api_name in source.url.lower():
                observations = collector_fn(source)
                break
        else:
            # Default to RSS collection if URL ends with common feed extensions
            if any(source.url.endswith(ext) for ext in ['.rss', '.xml', '/feed', '/rss']):
                observations = self.rss_collector.collect(source)
            else:
                # Try generic API collection
                observations = self._collect_generic_api(source)
        
        self.log_collection_complete(source, len(observations))
        return observations
    
    def _collect_gdacs(self, source: Source) -> List[RawObservation]:
        """
        Collect from GDACS (Global Disaster Alert and Coordination System).
        
        Args:
            source: GDACS source
            
        Returns:
            List of observations
        """
        # GDACS provides RSS feeds
        return self.rss_collector.collect(source)
    
    def _collect_reliefweb(self, source: Source) -> List[RawObservation]:
        """
        Collect from ReliefWeb API.
        
        Args:
            source: ReliefWeb source
            
        Returns:
            List of observations
        """
        observations = []
        
        try:
            headers = {"User-Agent": self.user_agent}
            response = httpx.get(
                source.url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get("data", [])[:50]:
                fields = item.get("fields", {})
                
                title = fields.get("title", "")
                body = fields.get("body", "")
                url = fields.get("url_alias", "")
                date_str = fields.get("date", {}).get("created")
                
                content = f"{title}\n\n{body}"
                
                extracted_time = None
                if date_str:
                    try:
                        extracted_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except Exception:
                        pass
                
                observation = self.create_observation(
                    source=source,
                    content=content,
                    title=title,
                    url=url,
                    extracted_timestamp=extracted_time
                )
                
                if observation:
                    observations.append(observation)
                    
        except Exception as e:
            logger.error(
                "ReliefWeb collection error",
                source_id=str(source.id),
                error=str(e)
            )
        
        return observations
    
    def _collect_generic_api(self, source: Source) -> List[RawObservation]:
        """
        Generic API collection for unknown APIs.
        
        Args:
            source: API source
            
        Returns:
            List of observations
        """
        observations = []
        
        try:
            headers = {"User-Agent": self.user_agent}
            response = httpx.get(
                source.url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                data = response.json()
                
                # Handle common JSON structures
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    # Try common keys
                    for key in ["data", "items", "results", "entries", "articles"]:
                        if key in data and isinstance(data[key], list):
                            items = data[key]
                            break
                
                for item in items[:50]:
                    # Extract common fields
                    title = item.get("title") or item.get("headline") or ""
                    body = item.get("body") or item.get("content") or item.get("description") or ""
                    url = item.get("url") or item.get("link") or ""
                    
                    if title or body:
                        observation = self.create_observation(
                            source=source,
                            content=f"{title}\n\n{body}",
                            title=title,
                            url=url
                        )
                        if observation:
                            observations.append(observation)
                            
            except json.JSONDecodeError:
                # Not JSON, treat as text
                observation = self.create_observation(
                    source=source,
                    content=response.text,
                    url=source.url
                )
                if observation:
                    observations.append(observation)
                    
        except Exception as e:
            logger.error(
                "Generic API collection error",
                source_id=str(source.id),
                error=str(e)
            )
        
        return observations
