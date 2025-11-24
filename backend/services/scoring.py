"""
Scoring service for calculating event scores.
Provides relevance, confidence, and priority scoring.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.core.logging import get_logger
from backend.models.event import EventCategory, SentimentEnum

logger = get_logger(__name__)


class ScoringService:
    """Service for calculating various event scores."""

    def __init__(self):
        """Initialize scoring service."""
        # Category weights for missionary relevance (0.0 to 1.0)
        self.category_relevance = {
            EventCategory.CRIME: 0.95,
            EventCategory.RELIGIOUS_FREEDOM: 0.95,
            EventCategory.PROTEST: 0.90,
            EventCategory.CULTURAL_TENSION: 0.85,
            EventCategory.MIGRATION: 0.70,
            EventCategory.HEALTH: 0.70,
            EventCategory.INFRASTRUCTURE: 0.65,
            EventCategory.POLITICAL: 0.60,
            EventCategory.ECONOMIC: 0.40,
            EventCategory.WEATHER: 0.50,
            EventCategory.COMMUNITY_EVENT: 0.30,
            EventCategory.OTHER: 0.20,
        }

    def calculate_relevance(
        self,
        category: EventCategory,
        sentiment: Optional[SentimentEnum] = None,
        entity_list: Optional[Dict[str, List[str]]] = None,
        text_length: int = 0
    ) -> float:
        """
        Calculate relevance score for missionaries.

        Args:
            category: Event category
            sentiment: Event sentiment
            entity_list: Extracted entities
            text_length: Length of event text

        Returns:
            Relevance score (0.0 to 1.0)
        """
        # Base relevance from category
        score = self.category_relevance.get(category, 0.5)

        # Sentiment adjustment
        if sentiment == SentimentEnum.NEGATIVE:
            # Negative events in high-relevance categories are more relevant
            if category in [
                EventCategory.CRIME,
                EventCategory.RELIGIOUS_FREEDOM,
                EventCategory.PROTEST,
                EventCategory.CULTURAL_TENSION
            ]:
                score = min(1.0, score + 0.10)
        elif sentiment == SentimentEnum.POSITIVE:
            # Positive events slightly less urgent
            score = max(0.2, score - 0.05)

        # Entity boost
        if entity_list:
            has_location = len(entity_list.get("locations", [])) > 0
            has_organization = len(entity_list.get("organizations", [])) > 0

            if has_location and has_organization:
                score = min(1.0, score + 0.05)

        # Text detail boost
        if text_length > 500:
            score = min(1.0, score + 0.05)

        return round(score, 2)

    def calculate_confidence(
        self,
        text_length: int,
        entity_count: int,
        has_location: bool,
        has_specific_category: bool,
        has_source: bool = True
    ) -> float:
        """
        Calculate confidence score for event data.

        Higher confidence when:
        - Text is detailed
        - Multiple entities extracted
        - Has specific location
        - Clear category (not OTHER)
        - Has verified source

        Args:
            text_length: Length of event text
            entity_count: Number of entities extracted
            has_location: Whether event has location
            has_specific_category: Whether category is not OTHER
            has_source: Whether event has source attribution

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.3  # Base confidence

        # Text length factor (up to +0.25)
        if text_length >= 1000:
            score += 0.25
        elif text_length >= 500:
            score += 0.20
        elif text_length >= 200:
            score += 0.15
        elif text_length >= 100:
            score += 0.10
        elif text_length >= 50:
            score += 0.05

        # Entity count factor (up to +0.25)
        if entity_count >= 15:
            score += 0.25
        elif entity_count >= 10:
            score += 0.20
        elif entity_count >= 5:
            score += 0.15
        elif entity_count >= 2:
            score += 0.10

        # Location factor (+0.15)
        if has_location:
            score += 0.15

        # Specific category (+0.15)
        if has_specific_category:
            score += 0.15

        # Source verification (+0.10)
        if has_source:
            score += 0.10

        return min(1.0, round(score, 2))

    def calculate_priority(
        self,
        relevance: float,
        confidence: float,
        recency_hours: float,
        cluster_size: int = 1
    ) -> float:
        """
        Calculate priority score for event display ordering.

        Priority is higher when:
        - High relevance
        - High confidence
        - Recent
        - Part of larger cluster (more sources)

        Args:
            relevance: Relevance score
            confidence: Confidence score
            recency_hours: Hours since event timestamp
            cluster_size: Number of events in cluster

        Returns:
            Priority score (0.0 to 1.0)
        """
        # Weighted combination of factors
        base_score = (relevance * 0.5) + (confidence * 0.3)

        # Recency decay (exponential)
        # Recent events get boost, older events decay
        if recency_hours < 6:
            recency_factor = 0.20
        elif recency_hours < 24:
            recency_factor = 0.15
        elif recency_hours < 72:
            recency_factor = 0.10
        elif recency_hours < 168:  # 1 week
            recency_factor = 0.05
        else:
            recency_factor = 0.0

        # Cluster size boost (up to +0.10)
        if cluster_size >= 5:
            cluster_factor = 0.10
        elif cluster_size >= 3:
            cluster_factor = 0.07
        elif cluster_size >= 2:
            cluster_factor = 0.04
        else:
            cluster_factor = 0.0

        priority = base_score + recency_factor + cluster_factor

        return min(1.0, round(priority, 2))

    def calculate_recency_hours(self, timestamp: datetime) -> float:
        """
        Calculate hours since timestamp.

        Args:
            timestamp: Event timestamp

        Returns:
            Hours since timestamp
        """
        delta = datetime.utcnow() - timestamp
        return delta.total_seconds() / 3600


# Global service instance
scoring_service = ScoringService()
