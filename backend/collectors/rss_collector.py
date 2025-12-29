"""
RSS Collector for ingesting RSS/Atom feeds.
Refactored from the original rss_worker to use the collector pattern.
"""
import feedparser
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from dateutil import parser as date_parser

from backend.core.logging import get_logger
from backend.models.source import Source, CollectionMethod
from backend.models.raw_observation import RawObservation, ContentType
from backend.collectors.collector_base import CollectorBase

logger = get_logger(__name__)


class RSSCollector(CollectorBase):
    """
    Collector for RSS and Atom feeds.
    
    Supports:
    - Standard RSS 2.0 feeds
    - Atom feeds
    - Automatic timestamp extraction
    - Content deduplication via hash
    """
    
    def __init__(self):
        """Initialize RSS collector."""
        super().__init__(CollectionMethod.RSS)
        self.max_entries = 50  # Max entries to process per feed
    
    def validate_source(self, source: Source) -> bool:
        """
        Validate that source is a valid RSS source.
        
        Args:
            source: Source to validate
            
        Returns:
            True if source has a URL and is RSS type
        """
        if not source.url:
            return False
        return True
    
    def collect(self, source: Source) -> List[RawObservation]:
        """
        Collect data from an RSS feed.
        
        Args:
            source: RSS source to collect from
            
        Returns:
            List of RawObservation objects
        """
        self.log_collection_start(source)
        
        observations = []
        errors = 0
        
        try:
            # Fetch the feed
            feed = self._fetch_feed(source.url)
            
            if not feed:
                logger.error("Failed to fetch feed", source_id=str(source.id))
                return []
            
            # Process entries
            for entry in feed.entries[:self.max_entries]:
                try:
                    observation = self._process_entry(entry, source)
                    if observation:
                        observations.append(observation)
                except Exception as e:
                    logger.warning(
                        "Error processing entry",
                        source=source.name,
                        error=str(e)
                    )
                    errors += 1
            
        except Exception as e:
            logger.error(
                "RSS collection error",
                source_id=str(source.id),
                error=str(e)
            )
            errors += 1
        
        self.log_collection_complete(source, len(observations), errors)
        return observations
    
    def _fetch_feed(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch and parse RSS feed.
        
        Args:
            url: Feed URL
            
        Returns:
            Parsed feed or None
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = httpx.get(
                url,
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            )
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(
                    "Feed parsing warning",
                    url=url,
                    error=str(feed.bozo_exception)
                )
            
            return feed
            
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching feed", url=url, error=str(e))
            return None
        except Exception as e:
            logger.error("Error fetching feed", url=url, error=str(e))
            return None
    
    def _process_entry(
        self,
        entry: Dict[str, Any],
        source: Source
    ) -> Optional[RawObservation]:
        """
        Process a single feed entry into a RawObservation.
        
        Args:
            entry: Feed entry
            source: Source object
            
        Returns:
            RawObservation or None
        """
        # Extract fields
        title = entry.get("title", "Untitled")
        summary = entry.get("summary", entry.get("description", ""))
        link = entry.get("link", "")
        
        # Build full text
        full_text = f"{title}\n\n{summary}"
        
        # Extract timestamp
        extracted_timestamp = self._extract_timestamp(entry)
        
        # Extract media if present
        media_refs = self._extract_media(entry)
        
        # Create observation
        return self.create_observation(
            source=source,
            content=full_text,
            title=title,
            url=link,
            content_type="text",
            media_refs=media_refs,
            extracted_timestamp=extracted_timestamp
        )
    
    def _extract_timestamp(self, entry: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract timestamp from feed entry.
        
        Args:
            entry: Feed entry
            
        Returns:
            Extracted datetime or None
        """
        # Try structured time first
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed:
            try:
                return datetime(*published_parsed[:6])
            except Exception:
                pass
        
        # Try string parsing
        published_str = entry.get("published") or entry.get("updated")
        if published_str:
            try:
                return date_parser.parse(published_str)
            except Exception:
                pass
        
        return None
    
    def _extract_media(self, entry: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Extract media references from feed entry.
        
        Args:
            entry: Feed entry
            
        Returns:
            List of media references or None
        """
        media_refs = []
        
        # Check for enclosures
        enclosures = entry.get("enclosures", [])
        for enclosure in enclosures:
            media_refs.append({
                "url": enclosure.get("href") or enclosure.get("url"),
                "type": enclosure.get("type", "unknown"),
                "length": enclosure.get("length")
            })
        
        # Check for media content
        media_content = entry.get("media_content", [])
        for media in media_content:
            media_refs.append({
                "url": media.get("url"),
                "type": media.get("type", "unknown"),
                "medium": media.get("medium")
            })
        
        return media_refs if media_refs else None
