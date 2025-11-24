"""
Fusion service for merging related events.
Combines multiple events about the same incident into a unified view.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from collections import Counter

from backend.core.logging import get_logger
from backend.models.event import Event, EventCategory, SentimentEnum, StabilityTrend
from backend.services.clustering import clustering_service
from backend.services.scoring import scoring_service

logger = get_logger(__name__)


class FusionService:
    """Service for fusing related events into clusters."""

    def __init__(self):
        """Initialize fusion service."""
        self.clustering = clustering_service
        self.scoring = scoring_service

    def fuse_events(self, events: List[Event]) -> Dict[str, Any]:
        """
        Fuse multiple events about the same incident.

        Creates a unified representation by:
        - Using the best summary
        - Merging entity lists
        - Combining source lists
        - Averaging scores
        - Using most common category/sentiment

        Args:
            events: List of events to fuse

        Returns:
            Fused event data dictionary
        """
        if not events:
            logger.warning("No events to fuse")
            return {}

        if len(events) == 1:
            # Single event, no fusion needed
            return self._event_to_dict(events[0])

        logger.info("Fusing events", count=len(events))

        # Sort by confidence score (highest first)
        events_sorted = sorted(
            events,
            key=lambda e: e.confidence_score or 0.0,
            reverse=True
        )

        # Use best event as base
        best_event = events_sorted[0]

        # Merge data from all events
        fused = {
            "cluster_id": best_event.cluster_id,
            "timestamp": self._get_earliest_timestamp(events),
            "summary": self._select_best_summary(events),
            "full_text": self._merge_full_texts(events),
            "location_lat": best_event.location_lat,
            "location_lon": best_event.location_lon,
            "location_name": best_event.location_name,
            "category": self._get_most_common_category(events),
            "sub_category": best_event.sub_category,
            "sentiment": self._get_most_common_sentiment(events),
            "stability_trend": self._assess_stability_trend(events),
            "source_list": self._merge_sources(events),
            "entity_list": self._merge_entities(events),
            "confidence_score": self._calculate_fused_confidence(events),
            "relevance_score": self._calculate_fused_relevance(events),
        }

        logger.info(
            "Events fused",
            cluster_id=str(fused["cluster_id"]),
            event_count=len(events),
            confidence=fused["confidence_score"]
        )

        return fused

    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "cluster_id": event.cluster_id,
            "timestamp": event.timestamp,
            "summary": event.summary,
            "full_text": event.full_text,
            "location_lat": event.location_lat,
            "location_lon": event.location_lon,
            "location_name": event.location_name,
            "category": event.category,
            "sub_category": event.sub_category,
            "sentiment": event.sentiment,
            "stability_trend": event.stability_trend,
            "source_list": event.source_list or [],
            "entity_list": event.entity_list or {},
            "confidence_score": event.confidence_score,
            "relevance_score": event.relevance_score,
        }

    def _get_earliest_timestamp(self, events: List[Event]) -> datetime:
        """Get earliest timestamp from events."""
        timestamps = [e.timestamp for e in events if e.timestamp]
        return min(timestamps) if timestamps else datetime.utcnow()

    def _select_best_summary(self, events: List[Event]) -> str:
        """Select the best summary from events."""
        # Prefer longer, more detailed summaries from high-confidence events
        summaries = [
            (e.summary, e.confidence_score or 0.0, len(e.summary))
            for e in events
            if e.summary
        ]

        if not summaries:
            return "No summary available"

        # Sort by confidence, then length
        summaries.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return summaries[0][0]

    def _merge_full_texts(self, events: List[Event]) -> str:
        """Merge full texts from events."""
        # Combine unique full texts
        texts = []
        seen_texts = set()

        for event in events:
            if event.full_text:
                # Use first 200 chars as fingerprint to avoid exact duplicates
                fingerprint = event.full_text[:200].lower().strip()
                if fingerprint not in seen_texts:
                    texts.append(event.full_text)
                    seen_texts.add(fingerprint)

        if not texts:
            return ""

        # If multiple texts, separate with markers
        if len(texts) == 1:
            return texts[0]
        else:
            return "\n\n---\n\n".join(texts)

    def _get_most_common_category(self, events: List[Event]) -> EventCategory:
        """Get most common category from events."""
        categories = [e.category for e in events if e.category]

        if not categories:
            return EventCategory.OTHER

        counter = Counter(categories)
        return counter.most_common(1)[0][0]

    def _get_most_common_sentiment(self, events: List[Event]) -> Optional[SentimentEnum]:
        """Get most common sentiment from events."""
        sentiments = [e.sentiment for e in events if e.sentiment]

        if not sentiments:
            return None

        counter = Counter(sentiments)
        return counter.most_common(1)[0][0]

    def _assess_stability_trend(self, events: List[Event]) -> StabilityTrend:
        """
        Assess stability trend based on event progression.

        If events are getting more negative over time, trend is DECREASING.
        If events are getting more positive, trend is INCREASING.
        Otherwise, NEUTRAL.

        Args:
            events: List of events in cluster

        Returns:
            StabilityTrend enum value
        """
        # Sort by timestamp
        events_sorted = sorted(events, key=lambda e: e.timestamp)

        # Look at sentiment progression
        sentiments = [e.sentiment for e in events_sorted if e.sentiment]

        if len(sentiments) < 2:
            return StabilityTrend.NEUTRAL

        # Simple heuristic: compare first and last
        first_sentiment = sentiments[0]
        last_sentiment = sentiments[-1]

        sentiment_values = {
            SentimentEnum.POSITIVE: 1,
            SentimentEnum.NEUTRAL: 0,
            SentimentEnum.NEGATIVE: -1
        }

        first_value = sentiment_values.get(first_sentiment, 0)
        last_value = sentiment_values.get(last_sentiment, 0)

        if last_value > first_value:
            return StabilityTrend.INCREASING
        elif last_value < first_value:
            return StabilityTrend.DECREASING
        else:
            return StabilityTrend.NEUTRAL

    def _merge_sources(self, events: List[Event]) -> List[Dict[str, Any]]:
        """Merge source lists from events."""
        all_sources = []
        seen_urls = set()

        for event in events:
            if event.source_list:
                for source in event.source_list:
                    url = source.get("url", "")
                    if url and url not in seen_urls:
                        all_sources.append(source)
                        seen_urls.add(url)

        return all_sources

    def _merge_entities(self, events: List[Event]) -> Dict[str, List[str]]:
        """Merge entity lists from events."""
        merged = {
            "locations": set(),
            "organizations": set(),
            "groups": set(),
            "topics": set(),
            "keywords": set()
        }

        for event in events:
            if event.entity_list:
                for key in merged.keys():
                    entities = event.entity_list.get(key, [])
                    for entity in entities:
                        # Normalize and add
                        merged[key].add(entity.lower().strip())

        # Convert sets to sorted lists
        result = {
            key: sorted(list(values))[:20]  # Limit to 20 per category
            for key, values in merged.items()
        }

        return result

    def _calculate_fused_confidence(self, events: List[Event]) -> float:
        """
        Calculate confidence for fused event.

        Fused events have higher confidence due to multiple sources.

        Args:
            events: List of events in cluster

        Returns:
            Fused confidence score
        """
        # Average of individual confidences
        confidences = [e.confidence_score for e in events if e.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Boost for multiple sources
        source_count = len(events)
        if source_count >= 5:
            boost = 0.15
        elif source_count >= 3:
            boost = 0.10
        elif source_count >= 2:
            boost = 0.05
        else:
            boost = 0.0

        fused_confidence = min(1.0, avg_confidence + boost)

        return round(fused_confidence, 2)

    def _calculate_fused_relevance(self, events: List[Event]) -> float:
        """
        Calculate relevance for fused event.

        Args:
            events: List of events in cluster

        Returns:
            Fused relevance score
        """
        # Use maximum relevance from cluster
        relevances = [e.relevance_score for e in events if e.relevance_score]

        if not relevances:
            return 0.5

        return round(max(relevances), 2)


# Global service instance
fusion_service = FusionService()
