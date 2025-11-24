"""
Entity extraction service.
Extracts structured entities from unstructured text.
"""
from typing import Dict, Any, List, Optional

from backend.core.logging import get_logger
from backend.services.llm_client import llm_client

logger = get_logger(__name__)


class EntityExtractionService:
    """Service for extracting entities from text."""

    def __init__(self):
        """Initialize entity extraction service."""
        self.llm = llm_client

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with extracted entities:
            {
                "locations": ["Berlin", "Mitte"],
                "organizations": ["AfD", "Police"],
                "groups": ["protesters"],
                "topics": ["immigration", "refugee policy"],
                "keywords": ["march", "tension"]
            }
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for entity extraction")
            return self._empty_entities()

        logger.info("Extracting entities from text", text_length=len(text))

        # Use LLM for extraction
        entities = self.llm.extract_entities(text)

        if entities:
            # Clean and deduplicate entities
            entities = self._clean_entities(entities)

            logger.info(
                "Entities extracted",
                locations=len(entities.get("locations", [])),
                organizations=len(entities.get("organizations", [])),
                groups=len(entities.get("groups", [])),
                topics=len(entities.get("topics", [])),
                keywords=len(entities.get("keywords", []))
            )

            return entities

        logger.warning("Entity extraction returned no results")
        return self._empty_entities()

    def _clean_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Clean and deduplicate entity lists.

        Args:
            entities: Raw entity dictionary

        Returns:
            Cleaned entity dictionary
        """
        cleaned = {}

        for key, values in entities.items():
            if not isinstance(values, list):
                cleaned[key] = []
                continue

            # Remove duplicates (case-insensitive) and empty strings
            seen = set()
            unique_values = []

            for value in values:
                if not isinstance(value, str):
                    continue

                value_clean = value.strip()
                if not value_clean:
                    continue

                value_lower = value_clean.lower()
                if value_lower not in seen:
                    seen.add(value_lower)
                    unique_values.append(value_clean)

            cleaned[key] = unique_values[:20]  # Limit to 20 per category

        return cleaned

    def _empty_entities(self) -> Dict[str, List[str]]:
        """Return empty entity structure."""
        return {
            "locations": [],
            "organizations": [],
            "groups": [],
            "topics": [],
            "keywords": []
        }


# Global service instance
entity_extraction_service = EntityExtractionService()
