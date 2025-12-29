"""
Base collector interface for all data collectors.
All collectors output RawObservation objects.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from backend.core.logging import get_logger
from backend.models.source import Source, CollectionMethod
from backend.models.raw_observation import RawObservation

logger = get_logger(__name__)


class CollectorBase(ABC):
    """
    Abstract base class for all data collectors.
    
    All collectors must:
    - Implement collect() to fetch data from a source
    - Implement validate_source() to check source compatibility
    - Output RawObservation objects
    - Respect rate limits and ethical collection guidelines
    """
    
    def __init__(self, collection_method: CollectionMethod):
        """
        Initialize collector.
        
        Args:
            collection_method: The collection method this collector supports
        """
        self.collection_method = collection_method
        self.user_agent = "GoodShepherd/2.0 (World Situational Awareness)"
        self.timeout = 30
    
    @abstractmethod
    def collect(self, source: Source) -> List[RawObservation]:
        """
        Collect data from a source.
        
        Args:
            source: Source to collect from
            
        Returns:
            List of RawObservation objects
        """
        pass
    
    @abstractmethod
    def validate_source(self, source: Source) -> bool:
        """
        Validate that this collector can handle the given source.
        
        Args:
            source: Source to validate
            
        Returns:
            True if source is compatible
        """
        pass
    
    def can_collect(self, source: Source) -> bool:
        """
        Check if this collector can collect from the given source.
        
        Args:
            source: Source to check
            
        Returns:
            True if collection is allowed
        """
        if not source.is_active:
            return False
        if source.allowed_collection_method != self.collection_method:
            return False
        return self.validate_source(source)
    
    def create_observation(
        self,
        source: Source,
        content: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        content_type: str = "text",
        media_refs: Optional[list] = None,
        extracted_timestamp: Optional[datetime] = None
    ) -> Optional[RawObservation]:
        """
        Create a RawObservation from collected content.
        
        Args:
            source: Source the content came from
            content: Raw text content
            title: Optional title
            url: Original URL
            content_type: Type of content
            media_refs: Optional media references
            extracted_timestamp: Timestamp extracted from content
            
        Returns:
            RawObservation object or None if duplicate
        """
        from backend.models.raw_observation import ContentType, RawObservation
        
        # Compute content hash for deduplication
        content_hash = RawObservation.compute_hash(content, url or "")
        
        # Map content type
        type_map = {
            "text": ContentType.TEXT,
            "image": ContentType.IMAGE,
            "video": ContentType.VIDEO,
            "dataset": ContentType.DATASET
        }
        
        observation = RawObservation(
            source_id=source.id,
            collected_at=datetime.utcnow(),
            content_type=type_map.get(content_type, ContentType.TEXT),
            raw_text=content,
            title=title,
            original_url=url,
            content_hash=content_hash,
            media_refs=media_refs,
            extracted_timestamp=extracted_timestamp,
            processed=False
        )
        
        return observation
    
    def log_collection_start(self, source: Source) -> None:
        """Log start of collection."""
        logger.info(
            "Starting collection",
            source_id=str(source.id),
            source_name=source.name,
            collector=self.__class__.__name__
        )
    
    def log_collection_complete(
        self,
        source: Source,
        count: int,
        errors: int = 0
    ) -> None:
        """Log completion of collection."""
        logger.info(
            "Collection complete",
            source_id=str(source.id),
            source_name=source.name,
            collector=self.__class__.__name__,
            observations_created=count,
            errors=errors
        )
