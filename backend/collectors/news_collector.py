"""
News Collector for news outlets and RSS feeds.
Extends RSS collector with news-specific handling.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend.core.logging import get_logger
from backend.models.source import Source, SourceType, CollectionMethod
from backend.models.raw_observation import RawObservation
from backend.collectors.rss_collector import RSSCollector

logger = get_logger(__name__)


class NewsCollector(RSSCollector):
    """
    Collector for news outlets.
    
    Extends RSSCollector with:
    - News-specific field extraction
    - Author/byline extraction
    - Category/section extraction
    - News API integration support
    
    Primarily uses RSS but can be extended for news APIs.
    """
    
    def __init__(self):
        """Initialize News collector."""
        super().__init__()
        # Override to news-specific max
        self.max_entries = 100
    
    def validate_source(self, source: Source) -> bool:
        """
        Validate that source is a news source.
        
        Args:
            source: Source to validate
            
        Returns:
            True if source is NEWS type with valid URL
        """
        if not source.url:
            return False
        # Accept both NEWS and general RSS sources
        if source.source_type not in [SourceType.NEWS, None]:
            # Also allow sources without explicit type
            if hasattr(source, 'source_type') and source.source_type:
                return source.source_type == SourceType.NEWS
        return True
    
    def _process_entry(
        self,
        entry: Dict[str, Any],
        source: Source
    ) -> Optional[RawObservation]:
        """
        Process a news feed entry with additional metadata.
        
        Args:
            entry: Feed entry
            source: Source object
            
        Returns:
            RawObservation or None
        """
        # Get base observation from parent
        observation = super()._process_entry(entry, source)
        
        if observation:
            # Extract additional news-specific metadata
            metadata = self._extract_news_metadata(entry)
            
            # Append metadata to the raw text for enrichment
            if metadata:
                metadata_text = self._format_metadata(metadata)
                observation.raw_text = f"{observation.raw_text}\n\n---\nMetadata:\n{metadata_text}"
        
        return observation
    
    def _extract_news_metadata(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract news-specific metadata from entry.
        
        Args:
            entry: Feed entry
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Author/byline
        author = entry.get("author") or entry.get("dc_creator")
        if author:
            metadata["author"] = author
        
        # Category/tags
        tags = entry.get("tags", [])
        if tags:
            metadata["categories"] = [t.get("term", "") for t in tags if t.get("term")]
        
        # Source attribution
        source_attr = entry.get("source", {})
        if source_attr:
            metadata["feed_source"] = source_attr.get("title", "")
        
        # Language
        language = entry.get("language")
        if language:
            metadata["language"] = language
        
        return metadata
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata as readable text.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted string
        """
        lines = []
        for key, value in metadata.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
