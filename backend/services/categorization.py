"""
Categorization service.
Automatically categorizes events based on content.
"""
from typing import Optional

from backend.core.logging import get_logger
from backend.services.llm_client import llm_client
from backend.models.event import EventCategory

logger = get_logger(__name__)


class CategorizationService:
    """Service for categorizing events."""

    def __init__(self):
        """Initialize categorization service."""
        self.llm = llm_client

    def categorize(self, text: str, title: Optional[str] = None) -> EventCategory:
        """
        Categorize text into an event category.

        Args:
            text: Full text to analyze
            title: Optional title/summary for additional context

        Returns:
            EventCategory enum value
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for categorization")
            return EventCategory.OTHER

        # Combine title and text for better context
        combined_text = f"{title}\n\n{text}" if title else text

        logger.info("Categorizing event", text_length=len(combined_text))

        # Use LLM for categorization
        category_str = self.llm.categorize(combined_text)

        # Convert to enum
        category = self._parse_category(category_str)

        logger.info("Event categorized", category=category.value)

        return category

    def _parse_category(self, category_str: str) -> EventCategory:
        """
        Parse category string to enum.

        Args:
            category_str: Category string

        Returns:
            EventCategory enum value
        """
        category_lower = category_str.lower().strip().replace("-", "_")

        # Try to match to enum
        try:
            return EventCategory(category_lower)
        except ValueError:
            # Fallback: try keyword matching
            return self._keyword_categorize(category_str)

    def _keyword_categorize(self, text: str) -> EventCategory:
        """
        Fallback categorization using keyword matching.

        Args:
            text: Text to categorize

        Returns:
            EventCategory enum value
        """
        text_lower = text.lower()

        # Keyword mapping
        keyword_map = {
            EventCategory.PROTEST: ["protest", "demonstration", "march", "rally"],
            EventCategory.CRIME: ["crime", "theft", "assault", "robbery", "violence"],
            EventCategory.RELIGIOUS_FREEDOM: ["religious", "church", "mosque", "faith", "worship"],
            EventCategory.CULTURAL_TENSION: ["cultural", "tension", "conflict", "ethnic"],
            EventCategory.POLITICAL: ["political", "election", "government", "policy", "parliament"],
            EventCategory.INFRASTRUCTURE: ["transport", "power", "infrastructure", "outage", "disruption"],
            EventCategory.HEALTH: ["health", "disease", "medical", "hospital", "outbreak"],
            EventCategory.MIGRATION: ["migration", "refugee", "migrant", "asylum", "border"],
            EventCategory.ECONOMIC: ["economic", "economy", "financial", "market", "trade"],
            EventCategory.WEATHER: ["weather", "storm", "flood", "earthquake", "disaster"],
            EventCategory.COMMUNITY_EVENT: ["festival", "celebration", "gathering", "event", "concert"],
        }

        # Check keywords
        for category, keywords in keyword_map.items():
            if any(keyword in text_lower for keyword in keywords):
                logger.info("Category matched by keyword", category=category.value)
                return category

        # Default to OTHER
        return EventCategory.OTHER


# Global service instance
categorization_service = CategorizationService()
