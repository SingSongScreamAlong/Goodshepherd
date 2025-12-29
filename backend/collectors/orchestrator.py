"""
Collector Orchestrator for managing and scheduling data collection.
Coordinates all collectors and handles observation persistence.
"""
from typing import List, Dict, Type, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.logging import get_logger
from backend.core.database import SessionLocal
from backend.models.source import Source, CollectionMethod, SourceType
from backend.models.raw_observation import RawObservation
from backend.collectors.collector_base import CollectorBase
from backend.collectors.rss_collector import RSSCollector
from backend.collectors.official_collector import OfficialCollector
from backend.collectors.news_collector import NewsCollector

logger = get_logger(__name__)


class CollectorOrchestrator:
    """
    Orchestrates data collection across all sources.
    
    Responsibilities:
    - Route sources to appropriate collectors
    - Handle observation persistence with deduplication
    - Track collection statistics
    - Manage collection scheduling
    """
    
    def __init__(self):
        """Initialize orchestrator with all collectors."""
        self.collectors: Dict[CollectionMethod, CollectorBase] = {
            CollectionMethod.RSS: RSSCollector(),
            CollectionMethod.API: OfficialCollector(),
        }
        
        # Source type to collector mapping
        self.type_collectors: Dict[SourceType, CollectorBase] = {
            SourceType.OFFICIAL: OfficialCollector(),
            SourceType.NEWS: NewsCollector(),
            SourceType.NGO: RSSCollector(),
            SourceType.PARTNER: RSSCollector(),
            SourceType.SOCIAL: RSSCollector(),  # Social RSS feeds only
        }
    
    def get_collector(self, source: Source) -> Optional[CollectorBase]:
        """
        Get appropriate collector for a source.
        
        Args:
            source: Source to get collector for
            
        Returns:
            Collector instance or None
        """
        # First try by collection method
        collector = self.collectors.get(source.allowed_collection_method)
        if collector and collector.can_collect(source):
            return collector
        
        # Then try by source type
        collector = self.type_collectors.get(source.source_type)
        if collector and collector.validate_source(source):
            return collector
        
        # Default to RSS collector
        default_collector = RSSCollector()
        if default_collector.validate_source(source):
            return default_collector
        
        return None
    
    def collect_from_source(
        self,
        source: Source,
        db: Optional[Session] = None
    ) -> int:
        """
        Collect and persist observations from a single source.
        
        Args:
            source: Source to collect from
            db: Optional database session
            
        Returns:
            Number of new observations persisted
        """
        collector = self.get_collector(source)
        if not collector:
            logger.warning(
                "No collector available for source",
                source_id=str(source.id),
                source_name=source.name
            )
            return 0
        
        # Collect observations
        observations = collector.collect(source)
        
        if not observations:
            return 0
        
        # Persist observations
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        persisted = 0
        
        try:
            for observation in observations:
                try:
                    db.add(observation)
                    db.commit()
                    persisted += 1
                except IntegrityError:
                    # Duplicate (content_hash unique constraint)
                    db.rollback()
                    logger.debug(
                        "Duplicate observation skipped",
                        hash=observation.content_hash[:16]
                    )
                except Exception as e:
                    db.rollback()
                    logger.error(
                        "Error persisting observation",
                        error=str(e)
                    )
            
            # Update source stats
            source.last_success_at = datetime.utcnow()
            source.fetch_count += 1
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(
                "Error in collection",
                source_id=str(source.id),
                error=str(e)
            )
        finally:
            if should_close:
                db.close()
        
        logger.info(
            "Collection complete",
            source=source.name,
            collected=len(observations),
            persisted=persisted,
            duplicates=len(observations) - persisted
        )
        
        return persisted
    
    def collect_all_active(self) -> Dict[str, int]:
        """
        Collect from all active sources.
        
        Returns:
            Dictionary of source names to observation counts
        """
        logger.info("Starting full collection run")
        
        db = SessionLocal()
        results = {}
        
        try:
            # Get all active sources
            sources = db.query(Source).filter(Source.is_active == True).all()
            logger.info("Found active sources", count=len(sources))
            
            for source in sources:
                try:
                    count = self.collect_from_source(source, db)
                    results[source.name] = count
                except Exception as e:
                    logger.error(
                        "Error collecting from source",
                        source=source.name,
                        error=str(e)
                    )
                    results[source.name] = -1  # Error indicator
            
        finally:
            db.close()
        
        total = sum(c for c in results.values() if c > 0)
        logger.info(
            "Full collection run complete",
            sources=len(results),
            total_observations=total
        )
        
        return results
    
    def collect_by_type(self, source_type: SourceType) -> Dict[str, int]:
        """
        Collect from all sources of a specific type.
        
        Args:
            source_type: Type of sources to collect from
            
        Returns:
            Dictionary of source names to observation counts
        """
        logger.info("Starting type-specific collection", source_type=source_type.value)
        
        db = SessionLocal()
        results = {}
        
        try:
            sources = db.query(Source).filter(
                Source.is_active == True,
                Source.source_type == source_type
            ).all()
            
            for source in sources:
                count = self.collect_from_source(source, db)
                results[source.name] = count
                
        finally:
            db.close()
        
        return results


# Global orchestrator instance
collector_orchestrator = CollectorOrchestrator()


def run_collection():
    """Entry point for running collection."""
    return collector_orchestrator.collect_all_active()
