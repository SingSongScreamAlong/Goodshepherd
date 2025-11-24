"""
Enrichment pipeline coordinator.
Orchestrates all enrichment services to transform raw data into enriched events.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from backend.core.logging import get_logger
from backend.services.entity_extraction import entity_extraction_service
from backend.services.summarizer import summarizer_service
from backend.services.sentiment import sentiment_service
from backend.services.categorization import categorization_service
from backend.models.event import EventCategory, SentimentEnum, StabilityTrend

logger = get_logger(__name__)


class EnrichmentPipeline:
    """Pipeline for enriching raw event data."""

    def __init__(self):
        """Initialize enrichment pipeline."""
        self.entity_extractor = entity_extraction_service
        self.summarizer = summarizer_service
        self.sentiment_analyzer = sentiment_service
        self.categorizer = categorization_service

    def enrich(
        self,
        text: str,
        title: Optional[str] = None,
        existing_category: Optional[EventCategory] = None
    ) -> Dict[str, Any]:
        """
        Enrich raw text with AI-powered analysis.

        Args:
            text: Full text to analyze
            title: Optional title for additional context
            existing_category: If provided, skip categorization

        Returns:
            Dictionary with enrichment results:
            {
                "summary": "...",
                "category": EventCategory.PROTEST,
                "sentiment": SentimentEnum.NEGATIVE,
                "entity_list": {...},
                "confidence_score": 0.85,
                "relevance_score": 0.75
            }
        """
        logger.info("Starting enrichment pipeline", text_length=len(text), has_title=bool(title))

        start_time = datetime.utcnow()
        enrichment = {}

        try:
            # 1. Summarization
            summary = self.summarizer.summarize(text, max_length=500)
            enrichment["summary"] = summary
            logger.debug("Summarization complete", summary_length=len(summary))

            # 2. Entity extraction
            entities = self.entity_extractor.extract(text)
            enrichment["entity_list"] = entities
            logger.debug("Entity extraction complete", entity_count=sum(len(v) for v in entities.values()))

            # 3. Categorization (if not provided)
            if existing_category:
                category = existing_category
            else:
                category = self.categorizer.categorize(text, title)
            enrichment["category"] = category
            logger.debug("Categorization complete", category=category.value)

            # 4. Sentiment analysis
            sentiment = self.sentiment_analyzer.analyze(text)
            enrichment["sentiment"] = sentiment
            logger.debug("Sentiment analysis complete", sentiment=sentiment.value)

            # 5. Calculate confidence score
            confidence = self._calculate_confidence(enrichment, text)
            enrichment["confidence_score"] = confidence

            # 6. Calculate relevance score
            relevance = self._calculate_relevance(enrichment, text)
            enrichment["relevance_score"] = relevance

            # 7. Default stability trend
            enrichment["stability_trend"] = StabilityTrend.NEUTRAL

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "Enrichment pipeline complete",
                elapsed_seconds=elapsed,
                category=category.value,
                sentiment=sentiment.value,
                confidence=confidence,
                relevance=relevance
            )

            return enrichment

        except Exception as e:
            logger.error("Enrichment pipeline failed", error=str(e), exc_info=True)
            # Return minimal enrichment on failure
            return self._fallback_enrichment(text, title, existing_category)

    def _calculate_confidence(self, enrichment: Dict[str, Any], text: str) -> float:
        """
        Calculate confidence score for enrichment.

        Higher confidence when:
        - Text is longer and more detailed
        - More entities extracted
        - Clear sentiment
        - Clear category match

        Args:
            enrichment: Enrichment data
            text: Original text

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Text length factor
        text_length = len(text)
        if text_length > 500:
            score += 0.15
        elif text_length > 200:
            score += 0.10
        elif text_length > 100:
            score += 0.05

        # Entity count factor
        entity_list = enrichment.get("entity_list", {})
        total_entities = sum(len(v) for v in entity_list.values())
        if total_entities >= 10:
            score += 0.15
        elif total_entities >= 5:
            score += 0.10
        elif total_entities >= 2:
            score += 0.05

        # Category specificity (not OTHER)
        category = enrichment.get("category")
        if category and category != EventCategory.OTHER:
            score += 0.10

        # Has location
        if entity_list.get("locations"):
            score += 0.10

        return min(1.0, score)

    def _calculate_relevance(self, enrichment: Dict[str, Any], text: str) -> float:
        """
        Calculate relevance score for missionaries.

        Higher relevance for:
        - Safety-related (crime, protest, health)
        - Cultural/religious topics
        - Infrastructure disruptions
        - Migration topics

        Args:
            enrichment: Enrichment data
            text: Original text

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.5  # Base relevance

        category = enrichment.get("category")

        # High relevance categories
        high_relevance = [
            EventCategory.CRIME,
            EventCategory.RELIGIOUS_FREEDOM,
            EventCategory.CULTURAL_TENSION,
            EventCategory.PROTEST
        ]

        # Medium relevance categories
        medium_relevance = [
            EventCategory.MIGRATION,
            EventCategory.INFRASTRUCTURE,
            EventCategory.HEALTH,
            EventCategory.POLITICAL
        ]

        if category in high_relevance:
            score += 0.35
        elif category in medium_relevance:
            score += 0.20

        # Negative sentiment increases relevance for safety
        sentiment = enrichment.get("sentiment")
        if sentiment == SentimentEnum.NEGATIVE and category in high_relevance:
            score += 0.15

        return min(1.0, score)

    def _fallback_enrichment(
        self,
        text: str,
        title: Optional[str],
        existing_category: Optional[EventCategory]
    ) -> Dict[str, Any]:
        """
        Fallback enrichment when pipeline fails.

        Args:
            text: Original text
            title: Optional title
            existing_category: Optional category

        Returns:
            Minimal enrichment dictionary
        """
        logger.warning("Using fallback enrichment")

        summary = title if title else text[:200].strip()
        if len(summary) > 200:
            summary = summary[:197] + "..."

        return {
            "summary": summary,
            "category": existing_category or EventCategory.OTHER,
            "sentiment": SentimentEnum.NEUTRAL,
            "entity_list": {
                "locations": [],
                "organizations": [],
                "groups": [],
                "topics": [],
                "keywords": []
            },
            "confidence_score": 0.3,
            "relevance_score": 0.5,
            "stability_trend": StabilityTrend.NEUTRAL
        }


# Global pipeline instance
enrichment_pipeline = EnrichmentPipeline()
